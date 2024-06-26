from playwright.sync_api import sync_playwright
import random
import re
import json
import time
import pandas as pd

def bot_detect(content, df):
    if "px-captcha-container" in content:
        print("\nBot detected.\n")
        df = None
        return df
    else:
        print(df)

# alert: different html/json depending on search location
def scrapeZillow(url_template, df):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features-AutomationControlled"])
        page = browser.new_page()

        chrome_version = f"Chrome/{random.randint(70, 90)}.0.{random.randint(1000, 9999)}.{random.randint(100, 999)}"
        safari_version = f"Safari/{random.randint(500, 600)}.{random.randint(0, 99)}"
        user_agent = f"Mozilla/{random.randint(5, 125)}.0 (Windows {random.randint(7, 11)}.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) {chrome_version} {safari_version}"
        page.set_extra_http_headers({"User-Agent": user_agent})

        page.context.add_cookies([
            {"name": f"cookieName{random.randint(5, 125)}", "value": f"cookieValue{random.randint(5, 125)}", "url": url_template}
        ])

        page.goto(url_template)
        print(f"Page loaded: {url_template}")
        time.sleep(random.uniform(2, 6))
        content = page.content()
        bot_detect(content, df)         #will occur if many requests
        #print(content)
        #with open('rentals_content_zillowUS.txt', 'a', encoding='utf-8') as file:
        #    file.write(content)

        #Page number and listing finder
        total_units_match = re.search(r'"totalResultCount":(\d+)', content)  #same method as scrapeRentals.py
        total_pages_match = re.search(r'"totalPages":(\d+)', content) 
        total_units = total_units_match.group(1) if total_units_match else None
        total_pages = total_pages_match.group(1) if total_pages_match else None
        current_page = 1
        print(f"total units:", total_units)
        print(f"total pages:", total_pages)

        while int(current_page) <= int(total_pages):
            #BIG CITY - single instance, then all results start with zpid: "cat1":\{"searchResults":\{"listResults":[{"zpid"
            pattern_bigCity = r'({"zpid".+?})' #same method as scrapeRentals.py
            matches_bigCity = re.findall(pattern_bigCity, content)
            #print(matches_us)
            for match in matches_bigCity:
                #make valid JSON
                if match.count('{') > match.count('}'):
                        match += ']}' 
                try:
                    data = json.loads(match)
                    #print(data)
                    # Extract JSON data into property_data format
                    property_data = {
                        "id": data["zpid"],
                        "name": data.get("statusText"),
                        "beds": data.get("units")[0].get("beds"), 
                        "bathrooms": None, 
                        "parkingSpaces": None,
                        "rent": data.get("units")[0].get("price").replace('$', '').replace(',', '').replace('+', '').replace('C', ''),  
                        "address1": data.get("addressStreet"), 
                        "url": f"https://www.zillow.com{data.get('detailUrl')}",
                        "company": None,
                        "address2": None,
                        "postal_code": data.get("addressZipcode"),
                        "view_on_map_url": None,
                        "city": data.get("addressCity"),
                        "location": {"latitude": None, "longitude": None}, 
                        "phone": None,
                        "time": None 
                    }
                    df = df.append(property_data, ignore_index=True)
                except json.JSONDecodeError:
                    print("Invalid JSON:", match)
            #print(df)
            #df.to_csv('zillow.csv', index=False)

            #OTHER CITY - multiple instances of pattern
            pattern = r'"hdpData":\{"homeInfo":({.*?})\}'
            patternURL = r'"hdpData":\{"homeInfo":{.*?"detailUrl":"(.*?)".*?\}'

            matches = re.findall(pattern, content)
            matchesURL = re.findall(patternURL, content)
            #clean url data
            for i in range(len(matchesURL)):
                if not matchesURL[i].startswith('https://www.zillow.com/'):
                    matchesURL[i] = 'https://www.zillow.com/' + matchesURL[i]

            for i, match in enumerate(matches):
                #make valid JSON
                if match.count('{') > match.count('}'):
                        match += '}'     
                try: 
                    data = json.loads(match)
                    #print(data)
                    # Extract JSON data into property_data format
                    property_data = {
                        "id": data["zpid"],
                        "name": None,
                        "beds": data.get("bedrooms"),
                        "bathrooms": data.get("bathrooms"),
                        "parkingSpaces": None,  
                        "rent": data.get("price"),
                        "address1": data.get("streetAddress"),
                        "url": matchesURL[i-1], 
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
            bot_detect(content, df)

            #Page turn via url
            current_page += 1
            page.close()
            if ((int(total_units)/(int(current_page)*41))) < 1: # 41 items per page : zillow #(try not to hard-code this)
                break
            time.sleep(random.uniform(31,32))  # may or may not trigger bot detections for next page webscrape
            page = browser.new_page(java_script_enabled=True) # necessary to prevent constant bot detections (60+ seconds seems to avoid)
            new_url_template = f'{url_template}/{current_page}_p/'
            page.goto(new_url_template)
            print(f"Navigating to page {current_page}: {new_url_template}")
            content = page.content()
        #df.to_csv('zillow2.csv', index=False)
        browser.close()
        return df
    