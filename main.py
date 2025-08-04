#!/usr/bin/env python3
import os, csv, time, re, traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

cities = ["pune", "delhi", "gurgaon", "noida", "bangalore", "mumbai"]
keywords = [
    "software companies",
    "IT services",
    "digital marketing agencies",
    "AI startups",
    "web development companies"
]

def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def extract_phone(text):
    phone_regex = re.compile(r'(?:(?:\+91[\s-]*)?\d{10}|\d{5}[\s-]\d{5})')
    match = phone_regex.search(text)
    return match.group().strip() if match else "N/A"

def extract_open_status(text):
    for line in text.split('\n'):
        if any(k in line.lower() for k in ["open", "closed", "opens", "closes"]):
            return line.strip()[:60]
    return "Unknown"

def extract_address(lines, name):
    for line in lines:
        if len(line) > 20 and line != name and not extract_phone(line):
            return line
    return "N/A"

def extract_website(element):
    try:
        links = element.find_elements(By.TAG_NAME, "a")
        for link in links:
            href = link.get_attribute("href")
            if href and "google.com" not in href and href.startswith("http"):
                return href
    except:
        pass
    return "N/A"

def extract_name(element):
    try:
        name_el = element.find_element(By.CSS_SELECTOR, "div.Nv2PK > div > div > div > div > div > div")
        return name_el.text.strip()
    except:
        return "N/A"

def scrape_city_keyword(driver, city, keyword, writer):
    query = f"{keyword} in {city}"
    area = query.split("in ")[-1].strip()
    print(f"🔍 Searching: {query}")

    try:
        driver.get("https://www.google.com/maps")
        time.sleep(2)

        box = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "searchboxinput")))
        box.clear()
        box.send_keys(query)
        box.send_keys(Keys.ENTER)
        time.sleep(4)

        listings = driver.find_elements(By.CSS_SELECTOR, "div.Nv2PK")
        print(f"📦 Found {len(listings)} listings")

        for el in listings:
            try:
                full_text = el.text
                lines = full_text.split("\n")

                name = extract_name(el)
                website = extract_website(el)
                phone = extract_phone(full_text)
                status = extract_open_status(full_text)
                address = extract_address(lines, name)

                writer.writerow([name, website, phone, status, address, keyword, area])
            except Exception as e:
                print(f"⚠️ Skipping listing due to error: {e}")
                continue

    except Exception as e:
        print(f"❌ Error scraping '{query}': {e}")
        traceback.print_exc()

def main():
    os.makedirs("results", exist_ok=True)
    driver = get_driver()

    for city in cities:
        print(f"\n🏙️ Scraping city: {city}")
        file_path = f"results/businesses_{city}.csv"
        with open(file_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Name", "Website", "Phone", "Open", "Address", "Keyword", "Area"])

            for keyword in keywords:
                scrape_city_keyword(driver, city, keyword, writer)
                time.sleep(2)

    driver.quit()
    print("\n✅ All cities scraped successfully!")

if __name__ == "__main__":
    main()
