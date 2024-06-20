from playwright.sync_api import sync_playwright
import time
import random
import json
import pandas as pd

# alert: canada only
# A. This website adds to the url during pagination a specific "GeoIds" parameter associated with a location
#to webscrape, this would require making a list of each village,town,city and matching its associated "GeoIds"
# OR use playwright to loop (press the right button id then get the page.content) - get multiple page data

#Example page 1: 
# https://www.realtor.ca/on/georgina/rentals
#Example page 2+:
#https://www.realtor.ca/map#view=list&CurrentPage=4&Sort=6-D&GeoIds=g30_dpz6xg42&GeoName=Newmarket%2C%20ON&PropertyTypeGroupID=1&TransactionTypeId=3&PropertySearchTypeId=1&Currency=CAD&HiddenListingIds=&IncludeHiddenListings=false
#https://www.realtor.ca/map#view=list&CurrentPage=3&Sort=6-D&GeoIds=g30_dpz6xg42&GeoName=Newmarket%2C%20ON&PropertyTypeGroupID=1&TransactionTypeId=3&PropertySearchTypeId=1&Currency=CAD&HiddenListingIds=&IncludeHiddenListings=false
#https://www.realtor.ca/map#view=list&CurrentPage=2&Sort=6-D&GeoIds=g30_dpz6xg42&GeoName=Newmarket%2C%20ON&PropertyTypeGroupID=1&TransactionTypeId=3&PropertySearchTypeId=1&Currency=CAD&HiddenListingIds=&IncludeHiddenListings=false    
#https://www.realtor.ca/map#view=list&Sort=6-D&GeoIds=g30_dpz6xg42&GeoName=Newmarket%2C%20ON&PropertyTypeGroupID=1&TransactionTypeId=3&PropertySearchTypeId=1&Currency=CAD&HiddenListingIds=&IncludeHiddenListings=false
#https://www.realtor.ca/map#view=list&CurrentPage=2&Sort=6-D&GeoIds=g30_dpzd6uq3&GeoName=Whitchurch-Stouffville%2C%20ON&PropertyTypeGroupID=1&TransactionTypeId=3&PropertySearchTypeId=1&Currency=CAD&HiddenListingIds=&IncludeHiddenListings=false

# B. Additionally it uses Incapsula challenge if bot detect
#to make a better user experience: Train model to solve Incapsula challenges automatically (machine learning); i frame in webpage to show visual

def scrapeRealtor(url_template,df):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False) #required for this webpage
        page = browser.new_page()
        
        # Set a custom user-agent header to avoid bot detection
        chrome_version = f"Chrome/{random.randint(70, 90)}.0.{random.randint(1000, 9999)}.{random.randint(100, 999)}"
        safari_version = f"Safari/{random.randint(500, 600)}.{random.randint(0, 99)}"
        user_agent = f"Mozilla/{random.randint(5, 125)}.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) {chrome_version} {safari_version}"
        page.set_extra_http_headers({"User-Agent": user_agent})

        # Adds cookies; modify as needed for your use case
        page.context.add_cookies([
            {"name": "cookieName2", "value": "cookieValue2", "url": url_template}
        ])

        # Navigate to the provided URL
        page.goto(url_template)
        time.sleep(random.uniform(2, 6))
        print(f"Page loaded: {url_template}")

        # Get the modified HTML content after script removal
        content = page.content()
        #print(content)

        # Check if the content indicates an Incapsula challenge
        if "Incapsula" in content:
            input("Please solve the Incapsula challenge in the browser. Once solved, press Enter to continue...")
            # Reload the page after challenge is solved
            page.reload()
            time.sleep(random.uniform(2, 6))
            content = page.content()
            #print(content)

        # Extract JSON data embedded in the HTML
        try:
            json_data = content.split('<script nonce="" type="application/json" id="SEOLandingPageInitialResponse">')[1].split('</script>')[0]
            parsed_data = json.loads(json_data)
            results = parsed_data.get("Results", [])
            totalPagesRealtor = parsed_data.get("Paging").get("TotalPages")
            totalUnitsRealtor = parsed_data.get("Paging").get("TotalRecords")
            print(f"Total pages: {totalPagesRealtor}")
            print(f"Total units: {totalUnitsRealtor}")
        except (IndexError, KeyError, json.JSONDecodeError) as e:
            print(f"Error extracting JSON data: {e}")
            results = []

        # Extract relevant data into a list of dictionaries
        data_list = []
        for result in results:
            property_data = {
                "id": result.get("MlsNumber"),
                "name": None,
                "beds": result["Building"].get("Bedrooms"),
                "bathrooms": result["Building"].get("BathroomTotal"),
                "parkingSpaces": result["Property"].get("ParkingSpaceTotal"),
                "rent": result["Property"].get("LeaseRentUnformattedValue"),
                "address1": result["Property"]["Address"].get("AddressText"),
                "url": "https://www.realtor.ca/"+result["RelativeDetailsURL"],
                "company": None,
                "address2": None,
                "postal_code": result["PostalCode"],
                "view_on_map_url": None,
                "city": None,
                "location": result["Property"]["Address"].get("Latitude")+";"+result["Property"]["Address"].get("Longitude"),
                "phone": result["Individual"][0]["Organization"]["Phones"][0]["AreaCode"]+"-"+result["Individual"][0]["Organization"]["Phones"][0]["PhoneNumber"],
                "time": result["TimeOnRealtor"]
            }
            data_list.append(property_data)

        # Create a DataFrame from the list of dictionaries
        df = pd.DataFrame(data_list)
        print(df)
        #df.to_csv('realtor.csv', index=False)
        browser.close()
        return df
