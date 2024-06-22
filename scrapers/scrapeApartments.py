from playwright.sync_api import sync_playwright
import re
import time
import random
import pandas as pd

# alert: different html/json depending on search location
def scrapeApartments(url_template, df):
    with sync_playwright() as p:
        # Launch browser in non-headless mode for less likelihood of encountering bot features
        browser = p.chromium.launch(headless=False, args=["--disable-blink-features-AutomationControlled"])  
        page = browser.new_page()

        # Set a custom user-agent header to prevent bot detection
        chrome_version = f"Chrome/{random.randint(70, 90)}.0.{random.randint(1000, 9999)}.{random.randint(100, 999)}"
        safari_version = f"Safari/{random.randint(500, 600)}.{random.randint(0, 99)}"
        user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) {chrome_version} {safari_version}"
        page.set_extra_http_headers({"User-Agent": user_agent})

        # Navigate to the target URL
        page.goto(url_template)
        #time.sleep(random.uniform(2, 5))
        print(f"Page loaded: {url_template}")
        content = page.content()

        #Page turn start, 40 per page (try not to hard-code this)
        total_units_match = re.search(r'"TotalUnitCount":(\d+)', content)  #same method as scrapeZillow.py & scrapeRentals.py
        total_units = int(total_units_match.group(1)) if total_units_match else None
        current_page = 1
        end = 0
        while end != 1:
            #print(content)
            #with open('rentals_content_ApartmentsCOM.txt', 'a', encoding='utf-8') as file:
            #    file.write(content)

            # Extract rental data from both rental_elementsA and rental_elementsB
            rental_elementsA = page.query_selector_all('.property-link')    # alternate rental_elementsA: .bed-price-range
            if not rental_elementsA:
                rental_elementsA = page.query_selector_all('.bed-price-range')
            rental_elementsB = page.query_selector_all('.property-title-wrapper') #other cities
            if not rental_elementsB:
                rental_elementsB = page.query_selector_all('.property-information') #toronto, miami, etc.

            for i, elementA in enumerate(rental_elementsA):
                # Try to extract rent and bed information from rental_elementsA
                rent_elementA = elementA.query_selector('.property-rents') #other cities
                if rent_elementA is None:
                    rent_elementA = elementA.query_selector('.property-pricing') #toronto, miami, etc.
                bed_elementA = elementA.query_selector('.property-beds')

                if rent_elementA and bed_elementA:
                    rent_text = rent_elementA.inner_text().strip()
                    try:
                        rent_text = int(rent_text.replace('$', '').replace('C', '').replace(',', '').split('-')[0].strip())
                    except ValueError:
                        print(f"Skipping element {i}: Rent information cannot be converted to integer.")
                        continue
                    #print(rent_text)
                    bed_text = bed_elementA.inner_text().strip()
                    #print(bed_text)

                    # Check if there is a corresponding element in rental_elementsB
                    if i < len(rental_elementsB):
                        elementB = rental_elementsB[i]
                        title_element = elementB.query_selector('.js-placardTitle.title')
                        address_element = elementB.query_selector('.property-address.js-url')
                        url_element = elementB.query_selector('.property-link')

                        if title_element and address_element and url_element:
                            title_text = title_element.inner_text().strip()
                            #print(title_text)
                            address_text = address_element.inner_text().strip()
                            #print(address_text)
                            url_text = url_element.get_attribute('href') 
                            #print(url_element)
                            address1_text = f"{title_text}, {address_text}"

                            # apartment.com data is obtained from the inner_text of html tags
                            property_data = {
                                "id": None,  
                                "name": None,  
                                "beds": bed_text,
                                "bathrooms": None,  
                                "parkingSpaces": None, 
                                "rent": rent_text,
                                "address1": address1_text,
                                "url": url_text, 
                                "company": None,  
                                "address2": None,
                                "postal_code": None,  
                                "view_on_map_url": None,
                                "city": None,  
                                "location": {"latitude": None, "longitude": None},  
                                "phone": None,  
                                "time": None 
                            }
                            df = df.append(property_data, ignore_index=True)
                        else:
                            print("Some elements not found for a rental, skipping...")

            #Page turn via url
            current_page += 1
            #page.close()
            if ((int(total_units)/(int(current_page)*40))) < 1: # 40 items per page : apartments.com #(try not to hard-code this)
                end = 1
                break
            #time.sleep(random.uniform(31,32))  # may or may not trigger bot detections for next page webscrape
            #page = browser.new_page(java_script_enabled=True) # necessary to prevent constant bot detections (60+ seconds seems to avoid)
            new_url_template = f'{url_template}{current_page}/'
            page.goto(new_url_template)
            print(f"Navigating to page {current_page}: {new_url_template}")
            content = page.content()

        browser.close()
        print(df)
        return df
