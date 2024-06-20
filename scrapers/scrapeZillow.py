from playwright.sync_api import sync_playwright
import random
import re
import json
import time
import pandas as pd

# https://www.zillow.com/
# TODO: multiple pages, us cities only 1 result
def scrapeZillow(url_template, df):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features-AutomationControlled"])
        page = browser.new_page()

        chrome_version = f"Chrome/{random.randint(70, 90)}.0.{random.randint(1000, 9999)}.{random.randint(100, 999)}"
        safari_version = f"Safari/{random.randint(500, 600)}.{random.randint(0, 99)}"
        user_agent = f"Mozilla/{random.randint(5, 125)}.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) {chrome_version} {safari_version}"
        page.set_extra_http_headers({"User-Agent": user_agent})

        page.context.add_cookies([
            {"name": "cookieName3", "value": "cookieValue3", "url": url_template}
        ])

        page.goto(url_template)
        #page.wait_for_load_state('networkidle')
        #time.sleep(random.uniform(2, 6))
        print(f"Page loaded: {url_template}")
        content = page.content()
        #print(content)

        #will occur if many requests
        if "px-captcha-container" in content:
            input("Please solve the captcha challenge in the browser. Once solved, press Enter to continue...")
            content = page.content()

        #pattern = r'"homeInfo":({[^}]*}),'
        pattern = r'"hdpData":\{"homeInfo":({.*?})\}'
        patternURL = r'"hdpData":\{"homeInfo":{.*?"detailUrl":"(.*?)".*?\}'

        matches = re.findall(pattern, content)
        matchesURL = re.findall(patternURL, content)
        #clean url data
        for i in range(len(matchesURL)):
            if not matchesURL[i].startswith('https://www.zillow.com/'):
                matchesURL[i] = 'https://www.zillow.com/' + matchesURL[i]

        for i, match in enumerate(matches):
            if match.count('{') > match.count('}'):
                    match += '}'     
            try: 
                data = json.loads(match)
                print(data)
                # Extract JSON data into property_data format
                property_data = {
                    "id": data["zpid"],
                    "name": None,
                    "beds": data.get("bedrooms"),
                    "bathrooms": data.get("bathrooms"),
                    "parkingSpaces": None,  
                    "rent": data.get("price"),
                    "address1": data.get("streetAddress"),
                    "url": matchesURL[i-1],  # Use corresponding URL from matchesURL
                    "company": None,
                    "address2": None,
                    "postal_code": data.get("zipcode"),
                    "view_on_map_url": None,
                    "city": data.get("city"),
                    "location": {"latitude": data.get("latitude"),"longitude": data.get("longitude")},
                    "phone": None,  
                    "time": data.get("daysOnZillow") 
                }
                df = df.append(property_data, ignore_index=True)
            except json.JSONDecodeError:
                print("Invalid JSON:", match)

        browser.close()
        print(df)
        #df.to_csv('zillow.csv', index=False)
        return df