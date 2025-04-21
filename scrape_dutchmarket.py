# scrape_dutchmarket.py
import json
import csv
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from scrape_cn import scrape_cn_variants

CHROME_PATH = r"C:\Users\MarkvanBrecht\Downloads\chromedriver-win64 (1)\chromedriver-win64\chromedriver.exe"

def get_driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    service = Service(CHROME_PATH)
    return webdriver.Chrome(service=service, options=opts)

def parse_json_ld_scripts(driver):
    scripts = driver.find_elements(By.XPATH, "//script[@type='application/ld+json']")
    entries = []
    for s in scripts:
        try:
            block = json.loads(s.get_attribute("innerHTML"))
        except:
            continue
        if isinstance(block, dict) and "@graph" in block:
            entries.extend(block["@graph"])
        elif isinstance(block, list):
            entries.extend(block)
        else:
            entries.append(block)
    return entries

def scrape_upfront_variants(driver):
    url = "https://upfront.nl/products/upfront-creatine"
    print(f"[INFO] Scraping Upfront from {url}")
    driver.get(url)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'creatine')]"))
        )
    except:
        print("  ⚠️ Upfront load timeout")
    text = driver.execute_script("return document.body.innerText").lower()
    variants = []
    for data in parse_json_ld_scripts(driver):
        if data.get("@type") != "Product":
            continue
        offers = data.get("offers") or []
        if not isinstance(offers, list):
            offers = [offers]
        for off in offers:
            sku = off.get("sku", "unknown")
            price = float(off.get("price", 0))
            u = off.get("url", "")
            if "48062935892317" in u or sku.endswith("Z5SUCR-1"):
                w = "500g"
            elif "55112139014527" in u or sku.endswith("P5SUCR-1"):
                w = "300g"
            elif "55183972041087" in u or sku.endswith("P2SUCR-1"):
                w = "200g"
            else:
                w = "unknown"
            status = "Visible" if w in text else "Hidden"
            variants.append({
                "brand": "Upfront", "weight": w, "price": price,
                "sku": sku, "status": status,
                "matched_text": w if status == "Visible" else ""
            })
    print(f"  ✅ {len(variants)} Upfront variants scraped.")
    return variants

def scrape_myprotein_variants(driver):
    url = "https://nl.myprotein.com/p/sports-nutrition/creatine-monohydraat-poeder/10530050/?variation=10530051"
    print(f"[INFO] Scraping Myprotein from {url}")
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//script[@type='application/ld+json']"))
    )
    text = driver.execute_script("return document.body.innerText").lower()
    weights = [w.replace(" ", "") for w in dict.fromkeys(re.findall(r"(\d+\s?g)", text))]
    variants = []
    for data in parse_json_ld_scripts(driver):
        if data.get("@type") != "Product":
            continue
        offers = data.get("offers") or []
        if not isinstance(offers, list):
            offers = [offers]
        for idx, off in enumerate(offers):
            sku = off.get("sku", "unknown")
            price = float(off.get("price", 0))
            name = off.get("name", "").lower()
            w = next((x for x in weights if x in name), None)
            if not w and idx < len(weights):
                w = weights[idx]
            w = w or "unknown"
            status = "Visible" if w in text else "Hidden"
            variants.append({
                "brand": "Myprotein", "weight": w, "price": price,
                "sku": sku, "status": status,
                "matched_text": w if status == "Visible" else ""
            })
    print(f"  ✅ {len(variants)} Myprotein variants scraped.")
    return variants

def scrape_bulk_variants(driver):
    url = "https://www.bulk.com/nl/products/creatine-monohydrate/bpb-cmon-0000"
    print(f"[INFO] Scraping Bulk from {url}")
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//script[@type='application/ld+json']"))
    )
    text = driver.execute_script("return document.body.innerText").lower()
    weights = [w.replace(" ", "") for w in dict.fromkeys(re.findall(r"(\d+\s?g)", text))]
    variants = []
    for data in parse_json_ld_scripts(driver):
        if data.get("@type") != "Product":
            continue
        offers = data.get("offers") or []
        if not isinstance(offers, list):
            offers = [offers]
        for idx, off in enumerate(offers):
            sku = off.get("sku", "unknown")
            price = float(off.get("price", 0))
            name = off.get("name", "").lower()
            w = next((x for x in weights if x in name), None)
            if not w and idx < len(weights):
                w = weights[idx]
            w = w or "unknown"
            status = "Visible" if w in text else "Hidden"
            variants.append({
                "brand": "Bulk", "weight": w, "price": price,
                "sku": sku, "status": status,
                "matched_text": w if status == "Visible" else ""
            })
    print(f"  ✅ {len(variants)} Bulk variants scraped.")
    return variants

def scrape_xxlnutrition_variants(driver):
    base = "https://xxlnutrition.com/en/creatine-monohydraat"
    print(f"[INFO] Scraping XXL Nutrition variants from {base}")
    driver.get(base)

    try:
        consent_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button#onetrust-accept-btn-handler"))
        )
        consent_btn.click()
        print("  🍪 Cookie consent accepted.")
    except:
        print("  ⚠️ No cookie banner found or clickable.")

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.product-options"))
        )
    except:
        print("  ❌ Couldn't find the amount button container.")
        driver.save_screenshot("xxl_missing_buttons.png")
        return []

    amount_buttons = driver.find_elements(By.CSS_SELECTOR, "div.product-options button")
    variants = []

    for button in amount_buttons:
        label = button.text.strip()
        if not label or "grams" not in label:
            continue

        print(f"  → Selecting amount: {label}")
        button.click()

        try:
            WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((By.NAME, "flavor"))
            )
            flavor_select = Select(driver.find_element(By.NAME, "flavor"))
        except:
            print(f"  ⚠️ Flavor dropdown not found after selecting amount: {label}")
            continue

        for j in range(1, len(flavor_select.options)):
            flavor_select.select_by_index(j)

            try:
                WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "span.product-price"))
                )
                price_elem = driver.find_element(By.CSS_SELECTOR, "span.product-price")
                price_text = price_elem.text.replace("€", "").replace(",", ".").strip()
                price = float(re.search(r"[\d.]+", price_text).group())
            except:
                print(f"  ⚠️ Price not found for {label} + {flavor_select.options[j].text.strip()}")
                continue

            weight = label
            flavor = flavor_select.options[j].text.strip()
            sku = f"{weight}_{flavor}".replace(" ", "_")

            variants.append({
                "brand": "XXL Nutrition",
                "weight": weight,
                "price": price,
                "sku": sku,
                "status": "Visible",
                "matched_text": f"{weight} {flavor}"
            })

            print(f"     ✅ {weight} / {flavor} = €{price}")

    print(f"  ✅ {len(variants)} XXL Nutrition variants scraped.")
    return variants

def scrape_bodyandfit_variants(driver):
    url = "https://www.bodyandfit.com/nl-nl/Producten/Creatine-%26-Prestatie/Creatine-Monohydrate/p/C101235"
    print(f"[INFO] Scraping Body & Fit from {url}")
    driver.get(url)
    variants = []
    try:
        select = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "form select[name='id']"))
        )
        options = select.find_elements(By.TAG_NAME, "option")
        for opt in options:
            sku = opt.get_attribute('value')
            title = opt.text.lower()
            m = re.search(r"(\d+)g", title)
            w = f"{m.group(1)}g" if m else "unknown"
            price_attr = opt.get_attribute('data-price') or '0'
            price = float(price_attr) / 100
            variants.append({"brand": "Body & Fit","weight": w,
                             "price": price,"sku": sku,
                             "status": "Visible","matched_text": w})
        print(f"  ✅ {len(variants)} Body & Fit variants scraped (dropdown).")
        return variants
    except:
        print("  ⚠️ Variant dropdown not found; falling back to JSON-LD")
    text = driver.execute_script("return document.body.innerText").lower()
    for data in parse_json_ld_scripts(driver):
        if data.get("@type") != "Product":
            continue
        offers = data.get("offers") or []
        if not isinstance(offers, list):
            offers = [offers]
        for off in offers:
            sku = off.get("sku", "")
            price = float(off.get("price", 0))
            name = data.get("name", "").lower() + ' ' + off.get("name", "").lower()
            m = re.search(r"(\d+)g", name)
            w = f"{m.group(1)}g" if m else "unknown"
            variants.append({"brand": "Body & Fit","weight": w,
                             "price": price,"sku": sku,
                             "status": "Visible" if w in text else "Hidden",
                             "matched_text": w if w in text else ""})
    print(f"  ✅ {len(variants)} Body & Fit variants scraped (JSON-LD fallback).")
    return variants

def detect_creatine_variant_visibility_js():
    driver = get_driver()
    allv = []
    allv += scrape_upfront_variants(driver)
    allv += scrape_myprotein_variants(driver)
    allv += scrape_bulk_variants(driver)
    allv += scrape_xxlnutrition_variants(driver)
    allv += scrape_bodyandfit_variants(driver)
    driver.quit()
    allv += scrape_cn_variants()

    # Filter visible variants only
    visible_variants = [v for v in allv if v['status'] == 'Visible']

    # Add €/100g calculation
    for v in visible_variants:
        try:
            grams = int(re.search(r"(\d+)", v['weight']).group(1))
            v["price_per_100g"] = round((v['price'] / grams) * 100, 2)
        except:
            v["price_per_100g"] = ""

    with open("visible_variants.csv", "w", newline='', encoding='utf-8') as f:
        fieldnames = ["brand", "weight", "price", "sku", "status", "matched_text", "price_per_100g"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for v in visible_variants:
            print(f"{v['brand']:<20} | {v['weight']:>7} | €{v['price']:<6} | {v['sku']} | {v['status']} | €/100g: {v['price_per_100g']}")
            writer.writerow(v)

if __name__ == "__main__":
    detect_creatine_variant_visibility_js()
