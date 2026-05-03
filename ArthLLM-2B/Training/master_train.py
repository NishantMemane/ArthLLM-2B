"""
ArthLLM Master Training Script
Runs on Kaggle 2×T4 GPUs — automated, unattended.
Features:
  - 8-bit AdamW (bitsandbytes) — saves VRAM
  - bf16 mixed precision — T4 native
  - Gradient checkpointing — fits 2B model on 32GB VRAM
  - WandB logging — monitor from phone
  - Telegram notifications — crash/save alerts
  - Auto-resume from checkpoint — Kaggle session limit safe
  - Google Drive checkpoint sync
"""

import os, math, time, logging
import torch
import torch.nn as nn
import wandb
import bitsandbytes as bnb
from pathlib import Path
from Model.config import ArthLLMConfig
from Model.model import ArthLLM
from Training.dataset import get_dataloader

log = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
BATCH_SIZE      = 4
GRADIENT_ACCUM  = 8          # effective batch = 32
SEQ_LEN         = 2048
LR              = 3e-4
LR_MIN          = 3e-5
WARMUP_STEPS    = 2000
MAX_STEPS       = 100_000
SAVE_EVERY      = 500
SHARD_DIR       = "data/tokenized_shards"
CKPT_DIR        = "checkpoints"
GDRIVE_DIR      = "/kaggle/working/gdrive/MyDrive/ArthLLM-2B/checkpoints"

os.makedirs(CKPT_DIR, exist_ok=True)


def get_lr(step: int) -> float:
    """Cosine decay with linear warmup."""
    if step < WARMUP_STEPS:
        return LR * (step / WARMUP_STEPS)
    progress = (step - WARMUP_STEPS) / (MAX_STEPS - WARMUP_STEPS)
    return LR_MIN + 0.5 * (LR - LR_MIN) * (1 + math.cos(math.pi * progress))


def send_telegram(msg: str):
    """Send training update via Telegram. Set TELEGRAM_TOKEN + CHAT_ID env vars."""
    token   = os.getenv("TELEGRAM_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return
    import requests
    try:
        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": msg}, timeout=10
        )
    except Exception:
        pass


def save_checkpoint(model, optimizer, step: int, loss: float):
    path = Path(CKPT_DIR) / f"arthlm_step_{step:06d}.pt"
    torch.save({
        "step": step, "loss": loss,
        "model":     model.state_dict(),
        "optimizer": optimizer.state_dict(),
    }, path)
    log.info(f"Checkpoint saved → {path}")

    # Sync to GDrive
    gdrive = Path(GDRIVE_DIR)
    if gdrive.exists():
        import shutil
        shutil.copy(path, gdrive / path.name)
        log.info(f"Synced to GDrive → {gdrive / path.name}")

    send_telegram(f"✅ ArthLLM Step {step:,}  loss={loss:.4f}  saved.")


def find_latest_checkpoint() -> dict | None:
    ckpts = sorted(Path(CKPT_DIR).glob("arthlm_step_*.pt"))
    if ckpts:
        log.info(f"Resuming from {ckpts[-1]}")
        return torch.load(ckpts[-1], map_location="cpu")
    return None


def train():
    logging.basicConfig(level=logging.INFO)
    wandb.init(project="ArthLLM-2B", config={
        "batch_size": BATCH_SIZE, "grad_accum": GRADIENT_ACCUM,
        "seq_len": SEQ_LEN, "lr": LR, "max_steps": MAX_STEPS,
    })

    cfg    = ArthLLMConfig()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model  = ArthLLM(cfg).to(device)

    # Enable gradient checkpointing to save VRAM
    model.gradient_checkpointing_enable() if hasattr(model, "gradient_checkpointing_enable") else None

    # 8-bit AdamW — saves ~4GB VRAM vs fp32 Adam
    optimizer = bnb.optim.AdamW8bit(model.parameters(), lr=LR, betas=(0.9, 0.95))

    # Resume if checkpoint exists
    start_step = 0
    ckpt = find_latest_checkpoint()
    if ckpt:
        model.load_state_dict(ckpt["model"])
        optimizer.load_state_dict(ckpt["optimizer"])
        start_step = ckpt["step"]
        log.info(f"Resumed from step {start_step}")

    loader = get_dataloader(SHARD_DIR, SEQ_LEN, BATCH_SIZE)
    scaler = torch.cuda.amp.GradScaler()   # for bf16

    model.train()
    t0 = time.time()
    optimizer.zero_grad()

    for step, (x, y) in enumerate(loader, start=start_step):
        if step >= MAX_STEPS:
            break

        x, y = x.to(device), y.to(device)

        with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
            logits = model(x)
            loss   = nn.functional.cross_entropy(
                logits.view(-1, cfg.vocab_size), y.view(-1)
            )
            loss   = loss / GRADIENT_ACCUM

        scaler.scale(loss).backward()

        if (step + 1) % GRADIENT_ACCUM == 0:
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)

            # LR schedule
            lr = get_lr(step)
            for pg in optimizer.param_groups:
                pg["lr"] = lr

            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad()

            elapsed = time.time() - t0
            tokens_per_sec = SEQ_LEN * BATCH_SIZE * GRADIENT_ACCUM / elapsed
            log.info(f"step={step:,}  loss={loss.item()*GRADIENT_ACCUM:.4f}  "
                     f"lr={lr:.2e}  tok/s={tokens_per_sec:,.0f}")
            wandb.log({"loss": loss.item() * GRADIENT_ACCUM, "lr": lr,
                       "tokens_per_sec": tokens_per_sec}, step=step)
            t0 = time.time()

        if step % SAVE_EVERY == 0 and step > start_step:
            save_checkpoint(model, optimizer, step, loss.item() * GRADIENT_ACCUM)

    save_checkpoint(model, optimizer, MAX_STEPS, loss.item())
    send_telegram("🎉 ArthLLM PRE-TRAINING COMPLETE!")
    wandb.finish()


if __name__ == "__main__":
    train()
