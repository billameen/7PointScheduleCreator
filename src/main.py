import os
from dotenv import load_dotenv, find_dotenv
from playwright.sync_api import sync_playwright

# load username and password
dotenv_path = find_dotenv()
load_dotenv(dotenv_path)

with sync_playwright() as p:
    # login
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto("https://www.7pointops.com/login")
    page.locator("#userName").fill(os.getenv("username"))
    page.locator("#password").fill(os.getenv("password"))
    page.click("#loginButton")

    # navigate to Book
    page.wait_for_url("https://www.7pointops.com")
    page.goto("https://www.7pointops.com/book")
    print("waiting")
    page.wait_for_url("https://www.7pointops.com/book")
    page.wait_for_timeout(10000)
    browser.close()

