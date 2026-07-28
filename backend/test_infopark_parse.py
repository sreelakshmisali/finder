from bs4 import BeautifulSoup
import json

def parse_html():
    with open("infopark_raw.html", "r", encoding="utf-8") as f:
        html = f.read()
        
    soup = BeautifulSoup(html, 'html.parser')
    
    # Check for job containers
    jobs = []
    
    # Search for typical classes or tags
    print("Looking for interesting elements...")
    for class_name in ['job', 'company', 'row', 'card', 'item']:
        elements = soup.find_all(class_=lambda x: x and class_name in x)
        print(f"Elements with class '{class_name}': {len(elements)}")
        
    # Check for javascript data
    scripts = soup.find_all('script')
    print(f"Found {len(scripts)} script tags")
    
    # Check if there is a main form or container
    print("Main containers:")
    main = soup.find('main')
    if main:
        print("Main element exists")

    # The Infopark jobs page might use ajax
    # Let's see if there are any API URLs in scripts
    for s in scripts:
        if s.string and ('ajax' in s.string or 'fetch' in s.string):
            print("Found AJAX script:")
            print(s.string[:200])
            
    # Try to find a list of jobs
    job_elements = soup.find_all('div', class_='company-job-list')
    if not job_elements:
        job_elements = soup.find_all('div', class_='job-list')
    
    print(f"Found {len(job_elements)} job elements")

if __name__ == "__main__":
    parse_html()
