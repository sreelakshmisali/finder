from bs4 import BeautifulSoup

def find_ajax():
    with open("infopark_raw.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, 'html.parser')
    scripts = soup.find_all('script')
    for s in scripts:
        if s.string and 'job-search' in s.string:
            print("--- SCRIPT ---")
            print(s.string)
            print("--------------")

if __name__ == "__main__":
    find_ajax()
