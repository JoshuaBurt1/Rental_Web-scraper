import pandas as pd
import os
from playwright.sync_api import sync_playwright
from scrapers.scrapeRentals import scrapeRentals
from scrapers.scrapeRealtor import scrapeRealtor
from scrapers.scrapeZillow import scrapeZillow
from scrapers.scrapeApartments import scrapeApartments

# facebook marketplace
# https://www.viewit.ca/rentals/scarborough?cid=364 
# https://trreb.ca/

# Eventually: some kind of machine learning to look at any content = page.content() and organize it into a pandas dataframe
# TODO: A. this needs to find duplicates and delete B. site specific two word search format

if __name__ == "__main__":
    # Change rental search location here:
    searchLocation = "ajax"
    #B.
    searchLocation = searchLocation.replace(' ', '-').replace('_', '-') 

    # Clear previous combined rental data CSV if it exists
    if os.path.exists('combined_rental_data.csv'):
        os.remove('combined_rental_data.csv')
    
    # Initialize an empty DataFrame for rentals data
    df = pd.DataFrame(columns=["id", "name", "beds", "bathrooms", "parkingSpaces", "rent", "address1", "url", "company", "address2", "postal_code", "view_on_map_url", "city", "location", "region", "phone", "time"])

    # Scrape rentals.ca data
    try:
        print("Scraping: rentals.ca")
        df_rentals = scrapeRentals(f'https://rentals.ca/{searchLocation}/all-apartments-all-houses-condos-rooms', df.copy())
    except Exception as e:
        df_rentals = None
        print(f"Error scraping rentals.ca: {str(e)}")
    
    # Scrape apartments.com data
    try:
        print("Scraping: apartments.com")
        df_apartments = scrapeApartments(f'https://www.apartments.com/{searchLocation}-on/', df.copy())
    except Exception as e:
        df_apartments = None
        print(f"Error scraping apartments.com: {str(e)}")
    
    # Scrape zillow.com data
    try:
        print("Scraping: zillow.com")
        df_zillow = scrapeZillow(f'https://www.zillow.com/{searchLocation}-on/rentals/', df.copy())
    except Exception as e:
        df_zillow = None
        print(f"Error scraping zillow.com: {str(e)}")

    # Scrape realtor.ca data
    try:
        print("Scraping: realtor.ca")
        df_realtor = scrapeRealtor(f'https://www.realtor.ca/on/{searchLocation}/rentals', df.copy())
    except Exception as e:
        df_realtor = None
        print(f"Error scraping realtor.ca: {str(e)}")
     
    # Merge DataFrames and handle duplicates
    dfs = [df_rentals, df_apartments, df_zillow, df_realtor]
    df_combined = pd.concat([d for d in dfs if d is not None], ignore_index=True)
   # Convert 'location' column to string
    if 'location' in df_combined.columns:
        df_combined['location'] = df_combined['location'].astype(str)
    df_combined['rent'] = pd.to_numeric(df_combined['rent'], errors='coerce')
    df_combined = df_combined[df_combined['rent'].notnull()]
    df_combined_sorted = df_combined.sort_values(by='rent')
    # Save to CSV
    df_combined_sorted.to_csv('combined_rental_data.csv', index=False)
    print("Combined rental data saved to combined_rental_data.csv")
    #print(df_combined_sorted)