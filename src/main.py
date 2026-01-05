import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv, find_dotenv
from playwright.sync_api import sync_playwright


# This dataclass will store all information pertaining to an event
@dataclass
class Event:
    name: Optional[str] = None
    room: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    access_time: Optional[str] = None
    setup_desc: Optional[str] = None
    error: Optional[bool] = None



def main():
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

        # get all rooms
        # reservedRooms = {}
        # for roomName in page.locator("#locationColumnWrapper").all_inner_texts():
        #     reservedRooms[roomName] = []

        for event in page.locator(".eventBarText").all():
            event.click()

            page.locator("#ngplus-overlay-container").wait_for(state="hidden")
            # access the info inside the event
            roomnum = page.locator(".roomDesc").inner_text()
            headinfo = page.locator("h3").inner_text()
            # timeinfo = page.locator(".groupDetails>dl").first.inner_html()
            # accesstime = page.get_by_text("Event Timeline").inner_text(timeout=1000)

            print("roomnum:", roomnum)
            print("headinfo:", headinfo)
            # print("timeInfo:", timeinfo)
            # print("accesstime:", accesstime)

            page.wait_for_timeout(3000)

            # exit this event
            page.get_by_role("button").get_by_text("×").click()

        browser.close()


main()