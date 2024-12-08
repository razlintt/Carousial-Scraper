import re
from playwright.sync_api import Playwright, sync_playwright, expect
import time

excluded_resource_types = ["image", "font"] 
def block_aggressively(route): 
	if (route.request.resource_type in excluded_resource_types): 
		route.abort() 
	else: 
		route.continue_() 

def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context(record_har_path="playwright_test_original.har")
    page = context.new_page()
    #page.on("request", lambda request: print(">>", request.method, request.url, request.resource_type)) 
    #page.on("response", lambda response: print("<<", response.status, response.url))
    #page.route("**/*", block_aggressively) 
    #page.route(re.compile(r"\.(jpg|png|svg)$"), lambda route: route.abort()) 
    page.goto("https://www.carousell.sg/")
    page.get_by_role("button", name="All Categories").click()
    page.locator("li").filter(has_text="Motorcycles").get_by_role("button").click()
    page.get_by_role("link", name="Motorcycles for Sale").click()
    page.get_by_role("button", name="Class 2B Class 2B").click()
    page.get_by_role("button", name="Sort:Best Match").click()
    page.locator("label").filter(has_text="Recent").click()
    page.get_by_role("button", name="Price").click()
    page.get_by_label("Minimum").click()
    page.get_by_label("Minimum").fill("300")
    page.get_by_label("Maximum").click()
    page.get_by_label("Maximum").fill("1500")
    page.get_by_role("button", name="Apply").click()
    time.sleep(3)
    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
