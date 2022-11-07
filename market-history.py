import json
import pandas as pd
import requests
import datetime
from datetime import date
import logging
import os

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')


# Ignore warnings
pd.options.mode.chained_assignment = None  # default='warn'

# Reads CSV in current location with custom list of id's
# CSV to be formatted same as example
df = pd.read_csv ('invTypes.csv', index_col='ID')
print(df)
# Set base URL for hitting ESI endpoints
base_url = 'https://esi.evetech.net/latest/'

# List of region ids to use for lookup
region_choice = input("Please enter the Region ID (Press enter for Placid): ")
if region_choice:
    region = region_choice
else:
    region = 10000048
# CSV to contain results
generated_csv = f"{(date.today())}-{region}-history.csv"


# Function for calculating average of list
def average(lists):
    average = sum(lists) / len(lists)
    return average
# Function for getting data from ESI market history endpoint for The Forge
def get_history(type_id, region):
    price_list = []
    volume_list = []
    # Page is not needed, but just in case....
    page = 1
    # Set parameters for the ESI query
    payload = {'datasource': 'tranquility','page': f'{page}', 'type_id': f'{type_id}', 'region_id': f'{region}'}
    # Build URL for region The Forge
    ORDERS_URL = f"{base_url}markets/{region}/history"
    # Make request and convert to Json
    request = requests.get(
            ORDERS_URL,
            params=payload
            )
    print(request.status_code)
    if request.status_code == 304:
        logging.info(f'{type_id} - Error: 304 (Not Modified)')
    elif request.status_code == 400:
        logging.info(f'{type_id} - Error: 400 (Bad Request)')
    elif request.status_code == 404:
        logging.info(f'{type_id} - Error: 404 (Type Not Found)')
    elif request.status_code == 420:
        logging.info(f'{type_id} - Error: 420 (Error Limited)')
    elif request.status_code == 422:
        logging.info(f'{type_id} - Error: 422 (Not Found)')
    elif request.status_code == 500:
        logging.info(f'{type_id} - Error: 500 (Internal Server Error)')
    elif request.status_code == 503:
        logging.info(f'{type_id} - Error: 503 (Service Unavailable)')
    elif request.status_code == 504:
        logging.info(f'{type_id} - Error: 504 (Gateway Timeout)')
    elif request.status_code == 520:
        logging.info(f'{type_id} - Error: 520 (Internal error thrown from the EVE server)')
    elif request.status_code == 200:
        history = request.json()

        # Attempt to get the average daily price and volume for this item over a 30 day period
        # If no price or volume, simply leave blank cells and print to screen "No History Found" 
        # This can be caused by ESI error or there actually being no history
        try:
            month = history[-30:]
            for date in range(len(month)):
                price = month[date]["average"]
                volume = month[date]["volume"]
                price_list.append(price)
                volume_list.append(volume)
            # Calculate averages and insert row into Dataframe 
            try:
                df.at[type_id, '30DayPrice'] = '{0:.2f}'.format(average(price_list))
                df.at[type_id, '30DayVolume'] = '{0:.0f}'.format(average(volume_list))
                df.at[type_id, '30DayISKVolume'] = '{0:.2f}'.format(average(price_list) * average(volume_list))
            except:
                print(f"Item {type_id} - No average available.")
        except:
            print(f"Item {type_id} - No history found.")

        # Attempt to get the average daily price and volume for this item over a 7 day period
        # If no price or volume, simply leave blank cells and print to screen "No History Found" 
        # This can be caused by ESI error or there actually being no history
        try:
            week = history[-7:]
            for date in range(len(week)):
                price = week[date]["average"]
                volume = week[date]["volume"]
                price_list.append(price)
                volume_list.append(volume)
            # Calculate averages and insert row into Dataframe        
            try:
                df.at[type_id, '7DayPrice'] = '{0:.2f}'.format(average(price_list))
                df.at[type_id, '7DayVolume'] = '{0:.0f}'.format(average(volume_list))
                df.at[type_id, '7DayISKVolume'] = '{0:.2f}'.format(average(price_list) * average(volume_list))
            except:
                print(f"Item {type_id} - No average available.")
        except:
            print(f"Item {type_id} - No history found.")
        

        


if __name__ == "__main__":

    # Timer to determine time taken to run script
    begin_time = datetime.datetime.now()
    # Item counter to display progress
    item_num = 1

    for index, row in df.iterrows():
        print(f"Item {item_num} of {len(df)}")
        print(df["typeName"][index], end='\r')
        get_history(index, region)
        
        item_num += 1
    end_time = datetime.datetime.now()
    print(f"Time Taken: {end_time - begin_time}")
    # Convert the dataframe to a CSV for use elsewhere
df.to_csv(generated_csv)
