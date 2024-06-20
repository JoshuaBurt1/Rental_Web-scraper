from playwright.sync_api import sync_playwright
import random
import re
import json
import pandas as pd

# alert: canada only
def scrapeRentals(url_template, df):    
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--disable-blink-features-AutomationControlled"])
        page = browser.new_page()
        
        # Set a custom user-agent header; without this session will be flagged as a bot
        chrome_version = f"Chrome/{random.randint(70, 90)}.0.{random.randint(1000, 9999)}.{random.randint(100, 999)}"
        safari_version = f"Safari/{random.randint(500, 600)}.{random.randint(0, 99)}"
        user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) {chrome_version} {safari_version}"
        page.set_extra_http_headers({"User-Agent": user_agent})

        # Adds cookies; bot detection prevention
        page.context.add_cookies([
            {"name": "cookieName2", "value": "cookieValue2", "url": url_template}
        ])

        page.goto(url_template)
        content = page.content()
        #with open('rentals_content1.txt', 'a', encoding='utf-8') as file:
        #    file.write(content)
        
        total_units_match = re.search(r'"total_units":(\d+)', content)
        if total_units_match:
            total_units = int(total_units_match.group(1))
            print("Total Units Match:", total_units)
        else:
            total_units = None

        current_page = 1
        while True:
            website_url = f'{url_template}?p={current_page}'
            page.goto(website_url)
            content = page.content()

            # Initialize variables to store last encountered values
            last_values = {
                "address1": None,
                "slug": None,
                "city": None,
                "url": None,
                "region": None,
                "company": None,
                "address2": None,
                "postal_code": None,
                "view_on_map_url": None,
                "location": None,
                "phone": None,
                "time": None
            }

            # Initialize DataFrame
            initial_length = len(df)
            #same method as scrapeZillow.py
            pattern = r'({"id".+?})'
            matches = re.findall(pattern, content)
            print(matches)
            if not matches:
                break  # No more listings on this page

            #make JSON valid format
            for match in matches:
                if match.count('{') > match.count('}'):
                    match += '}'     
                try:
                    match = match.replace('true', 'True')
                    match = match.replace('false', 'False')
                    data = json.loads(match)

                    # For all values that are empty, update last encountered values (address & url strings)
                    for key in last_values:
                        if key in data:
                            last_values[key] = data[key]

                    # Append data to DataFrame
                    df = df.append({**data, **last_values}, ignore_index=True)
                    df['city'] = df['slug']
                    
                except json.JSONDecodeError:
                    print("Invalid JSON:", match)

            # Print current DataFrame index to keep track in console
            print(total_units)
            print(len(df))
            # If no new information was added to the dataframe or the dataframe index exceeds total_units, exit the loop
            if len(df) == initial_length or (total_units is not None and len(df) >= total_units):
                break

            current_page += 1

        # Convert 'rent' column to numeric type for sorting
        df['rent'] = pd.to_numeric(df['rent'], errors='coerce')
        # Filter rows where rent is None, blank, null, or 0
        df = df[df['rent'].notnull() & (df['rent'] != 0)]
        df.drop(columns=['slug'], inplace=True)
        df_sorted = df.sort_values(by="rent")
        print(df_sorted)
        #df.to_csv('rentals.csv', index=False)

        browser.close()
    return df_sorted