import os
from dotenv import load_dotenv, find_dotenv
from playwright.sync_api import sync_playwright

# load username and password
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    # login
    page.goto("https://www.7pointops.com/login")
    page.locator("#userName").fill(os.getenv("username"))
    page.locator("#password").fill(os.getenv("password"))
    page.click("#loginButton")
    page.wait_for_url("https://www.7pointops.com")

    # navigate to Book
    page.goto("https://www.7pointops.com/book")
    page.wait_for_url("https://www.7pointops.com/book")
    page.locator("#locationColumnWrapper").wait_for(timeout=30000)
    print("done")

    # wait for book to load
    # get all the rooms that could be in use today
    # get all the events that a room has

    # create a class for each time slot
    #

    # id=locationColumnWrapper -> contains all room numbers
    # class=buildingsContainer -> contains all events

    browser.close()

