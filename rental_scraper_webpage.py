from flask import Flask, render_template, request, Response
from playwright.sync_api import sync_playwright
import time
import random
import re
import json
import pandas as pd
import os

#TODO: csv download, better webpage

app = Flask(__name__)

# Function to perform web scraping
def scrape_rental_info(city):
    url_template = f'https://rentals.ca/{city}/all-apartments-all-houses-condos-rooms'

    df = pd.DataFrame(columns=["id", "name", "beds", "rent", "address1", "slug", "url", "region", "company", "address2", "postal_code", "view_on_map_url", "city", "location", "phone"])
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
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
        with open('rental_content.txt', 'a', encoding='utf-8') as file:
            file.write(content)

        # Send initial response with empty data
        yield ""

        total_units_match = re.search(r'"total_units":(\d+)', content)
        if total_units_match:
            total_units = int(total_units_match.group(1))
            print("Total Units Match:", total_units)
            # Send total units information
            yield f"Total Units Match: {total_units}<br>"
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
                "url": None,
                "region": None,
                "company": None,
                "address2": None,
                "postal_code": None,
                "view_on_map_url": None,
                "city": None,
                "location": None,
                "phone": None
            }

            # Initialize DataFrame
            initial_length = len(df)
            pattern = r'({"id".+?})'
            matches = re.findall(pattern, content)
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
                    # Send data to the client
                    yield f"{data}<br>"
                except json.JSONDecodeError:
                    print("Invalid JSON:", match)

            # Send current progress information
            print(total_units)
            print(len(df))

            yield f"Processed {len(df)} entries<br>"

            # If no new information was added to the dataframe or the dataframe index exceeds total_units, exit the loop
            if len(df) == initial_length or (total_units is not None and len(df) >= total_units):
                break

            current_page += 1

        # Convert 'rent' column to numeric type
        df['rent'] = pd.to_numeric(df['rent'], errors='coerce')
        # Filter rows where rent is None, blank, null, or 0
        df = df[df['rent'].notnull() & (df['rent'] != 0)]
        df_sorted = df.sort_values(by="rent")

        # Send final response with sorted data
        if len(df) == 0: 
            yield f"No available rentals found.<br>"
        else:
            yield f"Final sorted data:<br>{df_sorted.to_html()}"

        # Save DataFrame to CSV file
        df_sorted.to_csv('rental_data.csv', index=False)

        browser.close()

# Flask route to handle requests
@app.route('/', methods=['GET', 'POST'])
def index():
    city = 'toronto'  # Default city
    if request.method == 'POST':
        city = request.form['city']
        # Replace spaces and underscores with hyphens; #https://rentals.ca/ specific
        city = city.replace(' ', '-').replace('_', '-') 
        # Return a Response object with a generator function
        return Response(scrape_rental_info(city), mimetype='text/html')
    return render_template('index.html', city=city)

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)