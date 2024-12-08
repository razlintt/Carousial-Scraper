'''
DONE// Do comparison for dictionary(newly scraped) and the csv, check if there are new items and
then we append to the csv file. 

DONE// If there is a new data, send it through telegram bot. can run as polling for the 
telegram bot and for removed listing, put as Sold in datetime

ONGOING// do an ss at every stage so in case there is a crash, we have the last seen reason 
for crash

for errors occured, we can add a job queue to re-search, if its a specific error(?)
coz maybe its the scraper is unable to find the resource or something that may not need to rescrape

Do checks for reserved to unreserved.

scrape but without the image or useless data. Compare current scraping method vs debloated scraping.
Check for the total traffic pulled. We want to minimise the data pulled so we can save on bandwidth.

implement residential proxy rotation to the script, and check how to use it.
I am considering to get from https://iproyal.com/residential-proxies/ $7
We can then check for "Sold/Unlisted" listings.

'''

import requests
from playwright.sync_api import Playwright, sync_playwright, expect
from bs4 import BeautifulSoup
import time
from datetime import datetime
from random import randint
import pandas as pd

# Telegram Integration
# Send message

messageIds = []
bot_token = '7849400138:AAGwEP8GbOc9u2ZOhWaxvjBAMVSrsOJb8-M'
chat_id = '203298543' # My ChatID

def sendPhoto(filename: str):
    url = f'https://api.telegram.org/bot{bot_token}/sendPhoto'

    # Open the image file in binary mode
    with open(filename, 'rb') as photo:
        # Prepare the payload and the file
        data = {'chat_id': chat_id}
        files = {'photo': photo}
        # Send the POST request
        response = requests.post(URL, data=data, files=files)
    
    # Print the response from Telegram API
    if response.ok:
        print("Image sent successfully!")
    else:
        print(f"Failed to send image. Response: {response.text}")
        sendMessage(f"There is an image I want to send but got problem.\nFile: {filename}")

def sendMessage(message): # Working
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'  # Optional: use Markdown for formatting
    }

    response = requests.post(url, data=payload)
    if(response.json()['ok'] != True):
        message = ("Got Error in sending message. Please check logs.")
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'Markdown'  # Optional: use Markdown for formatting
        }
        errorLog = response.json()
        response = requests.post(url, data=payload)
        
    return response.json()['ok']

# This will scrape all the data and put them into a dictionary
def runDataScraper(playwright: Playwright) -> None:
    listOfSearches2b = ['y15', 'krr', 'rxz', 'nmax', 'burgman 200', 'adv 150']
    
    # Date Configuration
    now = datetime.now()
    dateTimeNow = now.strftime("%d-%m-%Y %H:%M:%S")

    # Website search
    websiteLink = "https://www.carousell.sg"
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(websiteLink)
    toggle = True
    for searchItem in listOfSearches2b:
        print(f"Running Search for {searchItem} at {dateTimeNow}")
        page.get_by_placeholder("Search for an item").click()
        page.get_by_placeholder("Search for an item").fill(searchItem)
        page.get_by_role("button", name=f"{searchItem} in Class 2B").click() # Search button
        page.get_by_role("button", name="Sort:Best Match").click()
        page.get_by_text("Recent").click()
        if toggle:
            page.get_by_role("button", name="Condition").click()
            page.locator("label").filter(has_text="Used").locator("rect").click()
            toggle = False
    
        # Wait for the page to fully load
        time.sleep(10)

        # Extract page content as HTML
        html_content = page.content()
        ''' # For Debugging
        # Save the HTML content to a text file
        with open(f"page_content_{searchItem}.txt", "w", encoding="utf-8") as file:
            file.write(html_content)
        '''
        soup = BeautifulSoup(html_content, "html.parser")
        keys = ['Date', 'Username', 'Name', 'Before Price', 'After Price', 'Link', 'Sold']
        data = {key: [] for key in keys}
        links = soup.find_all("a")
        # print(links)
        for link in links:
            href = link.get("href")
            
            if href[:3] == "/u/":
                userName = href[3:].split("/")[0]
                data['Username'].append(userName)
            
            if href[:3] == "/p/":  # Ensure there is an href attribute
                data['Date'].append(dateTimeNow)
                href = href.split('?t')[0]
                saveLink = websiteLink + href
                try:
                    productName, price = link.get_text().split("S$")
                    # print("Name: ", productName)
                    # print("Price: S$", price)
                    # print("link: ", href)
                    data['Name'].append(productName)
                    data['Before Price'].append("Not Slashed")
                    data['After Price'].append(price)
                    data['Link'].append(saveLink)
                    data['Sold'].append("No")
                except ValueError:
                    productName, price, beforePrice = link.get_text().split("S$")
                    # print("Name: ", productName)
                    # print("Price Before: ", beforePrice)
                    # print("Price Discounted: S$", price)
                    # print("link: ", href)
                    data['Name'].append(productName)
                    data['Before Price'].append(beforePrice)
                    data['After Price'].append(price)
                    data['Link'].append(saveLink)
                    data['Sold'].append("No")
        
            file_name = f'{searchItem}.csv'
        # print(data)

        # Here, the dictionary is complete. I want to compare with csv
        #appendToCsv(data, file_name)
        #print(data)
        scraped_df = pd.DataFrame(data)
        try:
            csv_df = pd.read_csv(file_name)
            runComparison2(data, file_name)
        except FileNotFoundError:
            scraped_df.to_csv(file_name, index=False)
        
    # ---------------------
    context.close()
    browser.close()
    print("------------------------------Done search------------------------------------")

def runCarousellSearch():
    with sync_playwright() as playwright:
        runDataScraper(playwright)
'''
def runComparison(data: dict, file_name: str, currentTime: str):
    scraped_df = pd.DataFrame(data)
    csv_df = pd.read_csv(file_name)
    # I am using row_index[0] is coz it will find the first row with the same link. Technically there shouldnt be any duplicates
    # Check for Sold Listings
    old_links_list = csv_df.loc[~csv_df['Link'].isin(scraped_df['Link']), 'Link'].tolist()
    for link in old_links_list:
        row_index = csv_df.index[csv_df['Link'] == link].tolist()
        listingName = csv_df.loc[row_index[0], ['Name']]
        listingPrice = csv_df.loc[row_index[0], ['After Price']]
        listingUsername = csv_df.loc[row_index[0], ['Username']]
        message = f'Alert: LISTING SOLD/REMOVED!! {file_name[:-4].upper()}\nName: {listingName}\nPrice: ${listingPrice}\nUser: {listingUsername}'
        sendMessage(message)
        csv_df.loc[csv_df['Link'] == link, 'Sold'] = currentTime
        csv_df.to_csv(file_name, index=False)

    # Check for New Listings
    new_links_list = scraped_df.loc[~scraped_df['Link'].isin(csv_df['Link']), 'Link'].tolist()
    for link in new_links_list:
        row_index = scraped_df.index[scraped_df['Link'] == link].tolist()
        listingName = scraped_df.loc[row_index[0], ['Name']]
        listingPrice = scraped_df.loc[row_index[0], ['After Price']]
        listingUsername = scraped_df.loc[row_index[0], ['Username']]
        message = f'Alert: New Listing for {file_name[:-4]}\nName: {listingName}\nPrice: ${listingPrice}\nUser: {listingUsername}'
        sendMessage(message)
        row_data = scraped_df.loc[row_index[0]] # will get the data in the scraped_df
        csv_df = pd.concat([csv_df, row_data], ignore_index=True)
'''
def messageBuilder(data_dict: dict):
    # Date, Username, Name, Before Price, After Price, Link, Sold
    
    string_main = f"""
    🔔 Name: {data_dict['Name']} \n
    👤 User: {data_dict['Username']} \n
    💰 Before Price: ${data_dict['Before Price']} \n
    💵 Price: ${data_dict['After Price']} \n
    🌍 Link: {data_dict['Link']} 
    """
    if data_dict['Sold'] == "Yes":
        string_main += "\n❗️❗️LISTING SOLD❗️❗️"
    return string_main

def runComparison2(data: dict, file_name: str):
    df_scraped = pd.DataFrame(data).dropna()
    df_data = pd.read_csv(file_name).dropna()

    # Added new Data into list
    new_data_list = df_scraped.loc[~df_scraped['Link'].isin(df_data['Link']), 'Link'].tolist() # List of Links that are new listings

    # Removed Data into list
    sold_data_list = df_data.loc[~df_data['Link'].isin(df_scraped['Link']), 'Link'].tolist() # List of Links that are Sold

    # Checking for Price Change
    # Merge the DataFrames on 'link' column to compare 'Before Price'
    merged_df = pd.merge(df_scraped, df_data, on='Link', suffixes=('_scraped', '_data'), how='inner')

    # Find rows where 'Before Price' in df_scraped is different from df_data
    changed_prices = merged_df[merged_df['Before Price_scraped'] != merged_df['Before Price_data']]

    # Compile the results into the list slashedPriceList
    slashedPriceList = changed_prices['Link'].values.tolist() # List of Links that has their price changed

    # Modifying data for Sold in data dataframe
    #df['Result'] = df['Score'].apply(lambda x: 'Pass' if x >= 60 else 'Fail')
    df_data['Sold'] = df_data['Link'].apply(lambda x: 'Yes' if x in sold_data_list else 'No')

    # Modifying data for price change 
    # Update the entire row in df_data with the corresponding row from df_scraped where there is a difference
    for index, row in changed_prices.iterrows():
        # Replace the entire row in df_data with the row from df_scraped
        df_data.loc[df_data['Link'] == row['Link'], :] = df_scraped.loc[df_scraped['Link'] == row['Link'], :].values

    # Adding new listings into data dataframe
    ##The pd.concat() method requires a list or tuple of DataFrames as its first argument. 
    ##This allows it to concatenate multiple DataFrames in one operation. Thats why we use [] as first argument
    df_data = pd.concat([df_data, df_scraped[~df_scraped['Link'].isin(df_data['Link'])]], ignore_index=True)

    # Gathering Data for Telegram Bot
    # Extract rows where 'link' matches and convert to list of lists for new listings
    new_listings = df_data[df_data['Link'].isin(new_data_list)].to_dict('records')

    # Extract rows where 'link' matches and convert to list of lists for sold listings
    sold_listings = df_data[df_data['Link'].isin(sold_data_list)].to_dict('records')

    # Extract rows where 'link' matches and convert to list of lists for discounted listings
    discounted_listings = df_data[df_data['Link'].isin(slashedPriceList)].to_dict('records')

    # Check if there are new listings, then send to telegram
    if(len(new_listings) > 0):
        for listing in new_listings:
            sendMessage("NEW LISTING FOUND\n" + messageBuilder(listing))
            
        for listing in sold_listings:
            sendMessage("A LISTING HAS BEEN SOLD\n" + messageBuilder(listing))
            
        for listing in discounted_listings:
            sendMessage("A LISTING HAS BEEN DISCOUNTED\n" + messageBuilder(listing))

    df_data.to_csv(file_name, index=False)

#  Main

_prevText = "value"
_prevSentMsg = ""

def runMainProgram():
    prevDay = 0

    # Timing Configurations
    morningCheck = 11 # Morning check at 11 am
    afternoonCheck = 15 # Afternoon check at 3 pm
    nightCheck = 21 # Night check at 9 pm
    lateNightCheck = 2 # Late Check at 2 am

    # Telegram Settings
    # Track the last execution times
    last_task_3s = time.time()
    toggle_1t = True
    last_task_1h = time.time()

    while True:
        current_time = time.time()
        time.sleep(3) # To stop continuous unneeded looping

        if toggle_1t:
            #_prevText, _prevSentMsg = telegramCheckUpdates(_prevText, _prevSentMsg)
            runCarousellSearch()
            toggle_1t = False
        '''
        # Commented as no need for checks.
        if toggle_1t:
            _prevText, _prevSentMsg = telegramCheckUpdates(_prevText, _prevSentMsg)
            toggle_1t = False
        
        # Check if it's time to run telegram check updates
        if current_time - last_task_3s >= 3:
            _prevText, _prevSentMsg = telegramCheckUpdates(_prevText, _prevSentMsg)
            last_task_3s = current_time
        '''
        # Check if it's time to scrape Carousell
        if current_time - last_task_1h >= 3600:
            now = datetime.now()
            dateTimeNow = now.strftime("%d-%m-%Y %H:%M:%S")
            day = int(now.strftime("%d"))
            hour = int(now.strftime("%H"))

            if prevDay != day:
                print(f"New Day: {dateTimeNow}")
                prevDay = day
                dailyCheck = [morningCheck, afternoonCheck, nightCheck, lateNightCheck]

            if hour in dailyCheck:
                runCarousellSearch()
                dailyCheck.remove(hour)

            last_task_1h = current_time
            

runMainProgram()