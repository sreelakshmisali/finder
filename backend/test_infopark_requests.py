import httpx

def fetch_infopark():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    resp = httpx.get("https://infopark.in/companies-job", headers=headers)
    print(f"Status: {resp.status_code}")
    print(f"Content Length: {len(resp.text)}")
    
    with open("infopark_raw.html", "w", encoding="utf-8") as f:
        f.write(resp.text)

if __name__ == "__main__":
    fetch_infopark()
