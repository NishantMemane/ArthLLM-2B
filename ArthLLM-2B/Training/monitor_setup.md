# Monitoring Setup — WandB + Telegram

## WandB (Loss Curves)
```bash
pip install wandb
wandb login   # paste your API key from wandb.ai
```
Then open https://wandb.ai/your-username/ArthLLM-2B from your phone browser.
You'll see live: loss curve, tokens/sec, learning rate, GPU utilisation.

## Telegram (Crash/Save Alerts)
1. Open Telegram → search @BotFather → /newbot → name it ArthLLMBot
2. Copy the token it gives you
3. Message your bot once, then get your chat_id:
   https://api.telegram.org/bot<TOKEN>/getUpdates
4. Set env vars on Kaggle:
   - TELEGRAM_TOKEN = your bot token
   - TELEGRAM_CHAT_ID = your chat id

## Kaggle Scheduler
In Kaggle notebook settings → Schedule → every 12 hours.
The training script auto-resumes from the latest checkpoint.
You receive a Telegram message every 500 steps and on completion.
