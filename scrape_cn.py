import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

def scrape_cn_variants():
    chrome_path = r"C:\Users\MarkvanBrecht\Downloads\chromedriver-win64 (1)\chromedriver-win64\chromedriver.exe"

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")

    service = Service(executable_path=chrome_path)
    driver = webdriver.Chrome(service=service, options=options)

    url = "https://cnsupplements.com/products/creatine-monohydraat"
    print(f"[CN] Loading URL: {url}")
    driver.get(url)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    visible_text = soup.get_text().lower()
    variants = []

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if data.get("@type") == "Product":
                offers = data.get("offers", [])
                if not isinstance(offers, list):
                    offers = [offers]
                for offer in offers:
                    price = float(offer.get("price", 0))
                    sku = offer.get("sku", "unknown")
                    url = offer.get("url", "")
                    variant_id = url.split("variant=")[-1] if "variant=" in url else sku

                    # ✅ Match known SKUs to weights
                    if sku.endswith("0492"):
                        weight = "100g"
                    elif sku.endswith("0201"):
                        weight = "400g"
                    elif sku.endswith("2627"):
                        weight = "1000g"
                    else:
                        weight = "unknown"

                    # ✅ Determine visibility based on visible page content
                    terms = [weight, weight.replace("g", " g"), weight.replace("g", " gram")]
                    visible = any(term in visible_text for term in terms)

                    variants.append({
                        "brand": "CN Supplements",
                        "weight": weight,
                        "price": price,
                        "sku": sku,
                        "status": "Visible" if visible else "Hidden",
                        "matched_text": weight if visible else ""
                    })

        except Exception as e:
            print(f"[CN] Error parsing JSON: {e}")
            continue

    print(f"[CN] ✅ {len(variants)} variants scraped.")
    return variants
