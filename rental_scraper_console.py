import pandas as pd
import os
from playwright.sync_api import sync_playwright
from scrapers.scrapeRentals import scrapeRentals
from scrapers.scrapeRealtor import scrapeRealtor
from scrapers.scrapeZillow import scrapeZillow

if __name__ == "__main__":
    # Clear previous combined rental data CSV if it exists
    if os.path.exists('combined_rental_data.csv'):
        os.remove('combined_rental_data.csv')
    
    # Initialize an empty DataFrame for rentals data
    df = pd.DataFrame(columns=["id", "name", "beds", "bathrooms", "parkingSpaces", "rent", "address1", "slug", "url", "company", "address2", "postal_code", "view_on_map_url", "city", "location", "phone"])
    
    # Scrape rentals.ca data
    try:
        print("Scraping: rentals.ca")
        df_rentals = scrapeRentals('https://rentals.ca/sarnia/all-apartments-all-houses-condos-rooms', df.copy())
    except Exception as e:
        df_rentals = None
        print(f"Error scraping rentals.ca: {str(e)}")
    
    # Scrape zillow.com data
    try:
        print("Scraping: zillow.com")
        df_zillow = scrapeZillow('https://www.zillow.com/sarnia-on/rentals/', df.copy())
    except Exception as e:
        df_zillow = None
        print(f"Error scraping zillow.com: {str(e)}")
    
    # Scrape realtor.ca data
    try:
        print("Scraping: realtor.ca")
        df_realtor = scrapeRealtor('https://www.realtor.ca/on/sarnia/rentals', df.copy())
    except Exception as e:
        df_realtor = None
        print(f"Error scraping realtor.ca: {str(e)}")
    
    # Merge DataFrames and handle duplicates
    dfs = [df_rentals, df_zillow, df_realtor]
    df_combined = pd.concat([d for d in dfs if d is not None], ignore_index=True)
    
    # Preprocess DataFrame to handle dictionary columns
    # Example: If 'location' is a dictionary, flatten or drop it
    if 'location' in df_combined.columns:
        df_combined.drop(columns=['location'], inplace=True)  # Example: Drop the 'location' column
    
    # Convert 'rent' column to numeric type
    df_combined['rent'] = pd.to_numeric(df_combined['rent'], errors='coerce')
    
    # Filter out rows where rent is NaN (not numeric)
    df_combined = df_combined[df_combined['rent'].notnull()]
    
    # Sort by rent
    df_combined_sorted = df_combined.sort_values(by='rent')
    
    # Save to CSV
    df_combined_sorted.to_csv('combined_rental_data.csv', index=False)
    
    print("Combined rental data saved to combined_rental_data.csv")