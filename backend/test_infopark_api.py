import httpx

def test_api():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "X-Requested-With": "XMLHttpRequest"
    }
    resp = httpx.get("https://infopark.in/companies-job/0?search=react", headers=headers)
    print(f"Status: {resp.status_code}")
    print(f"Content: {resp.text[:500]}")
    with open("infopark_api_resp.json", "w", encoding="utf-8") as f:
        f.write(resp.text)

if __name__ == "__main__":
    test_api()
