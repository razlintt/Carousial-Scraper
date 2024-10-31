from playwright.sync_api import Playwright, sync_playwright, expect
from bs4 import BeautifulSoup
import re
import time

def run(playwright: Playwright) -> None:
    websiteLink = "https://www.carousell.sg/"
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto(websiteLink)
    page.get_by_placeholder("Search for an item").click()
    page.get_by_placeholder("Search for an item").fill("y15")
    page.get_by_role("button", name="y15 in Class 2B").click()
    page.get_by_role("button", name="Sort:Best Match").click()
    page.get_by_text("Recent").click()
    page.get_by_role("button", name="Condition").click()
    page.locator("label").filter(has_text="Used").locator("rect").click()
    
    # Wait for the page to fully load
    time.sleep(10)

    # Extract page content as HTML
    html_content = page.content()

    # Save the HTML content to a text file
    with open("page_content_y15.txt", "w", encoding="utf-8") as file:
        file.write(html_content)
        
    soup = BeautifulSoup(html_content, "html.parser")

    links = soup.find_all("a")
    for followUp in links:
        href = followUp.get("href")
        link = websiteLink[:-1] + href

        print(link)

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)