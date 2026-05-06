import urllib.request
import re
req = urllib.request.Request('https://www.rbi.org.in/Scripts/PublicationReportDetails.aspx?ID=1194', headers={'User-Agent': 'Mozilla/5.0'})
html = urllib.request.urlopen(req).read().decode('utf-8')
print("PDF Links:", re.findall(r'href=[\'"]([^\'"]+\.pdf)[\'"]', html, re.I))
