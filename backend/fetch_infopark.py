import urllib.request
import re

try:
    req = urllib.request.Request(
        'https://infopark.in/companies-job', 
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    html = urllib.request.urlopen(req).read().decode('utf-8')
    links = re.findall(r'href=[\'"]?([^\'" >]+)', html)
    
    print("All links containing 'job' or 'career':")
    for link in links:
        if 'job' in link.lower() or 'career' in link.lower():
            print("  ", link)
            
    print("\nText in links containing 'job' or 'career':")
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all('a', href=True):
        if 'job' in a['href'].lower() or 'career' in a['href'].lower():
            print("  ", a['href'], "->", a.text.strip())
            
except Exception as e:
    print("Error:", e)
