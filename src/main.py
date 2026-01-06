import os
from dataclasses import dataclass
from typing import Optional, Tuple
from dotenv import load_dotenv, find_dotenv
from playwright.sync_api import sync_playwright


# This dataclass will store all information pertaining to an event
@dataclass
class Event:
    room: Optional[str] = None
    setup_desc: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    access_time: Optional[str] = None
    error: Optional[bool] = None



# Expected input: Med Deli Catering Meeting - Talley Student Union - 3220 - (Conference, 5, act. 0)
# Expected output: Conference, 5
def get_setup_desc(desc: str) -> str:
    """
    Gets the setup description (i.e. Conference 15, Classroom 40, etc.)
    :param desc: the heading (<h3>) of the event description
    """
    desc = desc.split('(')[1].split(', act.')[0].strip()
    return desc



# Expected input: inner html <dt>Reserved Start</dt><dd><!-- react-text: 34 -->9:45 AM<!-- /react-text --><!-- react-text: 35 -->&nbsp;<!-- /react-text --></dd><dt>Event Start</dt><dd><!-- react-text: 38 -->10:00 AM<!-- /react-text --><!-- react-text: 39 -->&nbsp;<!-- /react-text --></dd><dt>Event End</dt><dd><!-- react-text: 42 -->11:00 AM<!-- /react-text --><!-- react-text: 43 -->&nbsp;<!-- /react-text --></dd><dt>Reserved End</dt><dd><!-- react-text: 46 -->11:15 AM<!-- /react-text --><!-- react-text: 47 -->&nbsp;<!-- /react-text --></dd><dt>Status</dt><dd><!-- react-text: 50 -->Confirmed<!-- /react-text --><!-- react-text: 51 -->&nbsp;<!-- /react-text --></dd><dt>Event Type</dt><dd><!-- react-text: 54 -->(none)<!-- /react-text --><!-- react-text: 55 -->&nbsp;<!-- /react-text --></dd>
# Expected output: (10:00 AM, 11:00 AM)
def get_event_time(desc: str) -> Tuple[str, str]:
    """
    Gets the start and end time of the event
    :param desc: HTML code containing the event start and end time. This is expected in a very specific format
    :return: (start time, end time)
    """
    start_time = desc.split('Event Start')[1].strip().split('Event End')[0].strip()
    end_time = desc.split('Event End')[1].strip().split('Reserved End')[0].strip()

    start_time = start_time.split('-->')[1].split('<!--')[0].strip()
    end_time = end_time.split('-->')[1].split('<!--')[0].strip()

    return start_time, end_time



def process_event_info(page):

    # make sure page has loaded
    page.locator("#ngplus-overlay-container").wait_for(state="hidden")

    # access the info inside the event
    room_num = page.locator(".roomDesc").inner_text()
    header_info = page.locator("h3").inner_text()
    time_info = get_event_time(page.locator(".groupDetails>dl").first.inner_html())
    # access_time = page.get_by_text("Event Timeline").inner_text(timeout=1000)

    print("room num:", room_num)
    print("head info:", header_info)
    print("start time", time_info[0])
    print("endtime", time_info[1])
    # print("access time", time_info[2])
    # print("error")

    event = Event()
    event.room = room_num
    event.setup_desc = get_setup_desc(header_info)
    event.start_time = time_info[0]
    event.end_time = time_info[1]

    page.wait_for_timeout(3000)



def get_event_data():

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

            process_event_info(page)

            # exit this event
            page.get_by_role("button").get_by_text("×").click()

        browser.close()



if __name__ == "__main__":
    get_event_data()