import json
import os
import re
from dataclasses import dataclass
from typing import Optional, Tuple, List
from dotenv import load_dotenv, find_dotenv
from playwright.sync_api import sync_playwright
import pendulum
from pathlib import Path
import webbrowser
import http.server
import socketserver

PORT = 8000

html_path = Path(__file__).parent / "index.html"
irrelevant_rooms_path = Path(__file__).parent / "irrelevant_rooms.txt"

DEBUG = False

task_list = {
    "5:00 AM": [],
    "5:30 AM": [],
    "6:00 AM": [],
    "6:30 AM": [],
    "7:00 AM": [],
    "7:30 AM": [],
    "8:00 AM": [],
    "8:30 AM": [],
    "9:00 AM": [],
    "9:30 AM": [],
    "10:00 AM": [],
    "10:30 AM": [],
    "11:00 AM": [],
    "11:30 AM": [],
    "12:00 PM": [],
    "12:30 PM": [],
    "1:00 PM": [],
    "1:30 PM": [],
    "2:00 PM": [],
    "2:30 PM": [],
    "3:00 PM": [],
    "3:30 PM": [],
    "4:00 PM": [],
    "4:30 PM": [],
    "5:00 PM": [],
    "5:30 PM": [],
    "6:00 PM": [],
    "6:30 PM": [],
    "7:00 PM": [],
    "7:30 PM": [],
    "8:00 PM": [],
    "8:30 PM": [],
    "9:00 PM": [],
    "9:30 PM": [],
    "10:00 PM": [],
    "10:30 PM": [],
    "11:00 PM": [],
    "11:30 PM": [],
    "12:00 AM": [],
    "12:30 AM": [],
    "1:00 AM": [],
    "1:30 AM": [],
    "2:00 AM": [],
    "2:30 AM": [],
    "3:00 AM": [],
}

irrelevant_rooms = set()


time_pattern = re.compile(
    r'\b\d{1,2}(?::\d{2})?\s?(?:a\.?m\.?|p\.?m\.?)\b',
    re.IGNORECASE
)


TIME_FORMATS = [
    "hA",        # 11AM
    "h A",       # 11 AM
    "h:mmA",     # 11:00AM
    "h:mm A",    # 11:00 AM
]

def parse_time_12h(time_str, tz="local"):
    time_str = " ".join(time_str.split()).upper()

    for fmt in TIME_FORMATS:
        try:
            return pendulum.from_format(time_str, fmt, tz=tz)
        except Exception as e:
            pass
    raise ValueError(f"Invalid time format: {time_str}")


# This dataclass will store all information pertaining to an event
@dataclass
class Event:
    room: Optional[str] = None
    setup_desc: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    access_time: Optional[str] = None
    catering_access_time: Optional[str] = None
    error: Optional[str] = None

    def print(self):
        print("Room: ", self.room)
        print("Setup: ", self.setup_desc)
        print("Start time: ", self.start_time)
        print("End time: ", self.end_time)
        print("Access time: ", self.access_time)
        print("Catering access time: ", self.catering_access_time)
        print(self.error)


# This dataclass will store all information pertaining to a task
@dataclass
class Task:
    time: Optional[str] = None
    room: Optional[str] = None
    type: Optional[str] = None
    more_info: Optional[str] = None
    error: Optional[str] = None





def set_event_room_num(event, event_locator):
    room_num = event_locator.locator(".mat-column-event")
    room_num.wait_for(state="visible", timeout=2000)
    if room_num.count() == 1:
        event.room = event_locator.locator(".mat-column-event").locator("b").inner_html().strip()
        # print("room: ", event.room)
    else:
        event.room = None
        event.error = "No room number"
        raise Exception("No room number") # Having no room number is fatal. An event should not be processed if it doesn't have a room number.


def set_event_setup_desc(event, event_locator):
    setup_desc = event_locator.locator(".mat-column-event")
    setup_desc.wait_for(state="visible", timeout=2000)
    if setup_desc.count() > 0:
        setup_text = setup_desc.inner_html().split("(")[1].split(")")[0]
        event.setup_desc = setup_text
    else:
        event.setup_desc = None
        event.error = "No setup description"
        #print("setup desc: None")


def set_event_time(event, event_details):
    customer_access = event_details.locator('sp-details-row[label="Customer Access"]')
    customer_access.wait_for(state="visible", timeout=2000)

    if DEBUG:
        print("Finding Event Time")

    if customer_access.count() == 1:
        time_info = customer_access.locator("span.detail-data").inner_text().split("-")

        start_time, end_time = time_info[0].strip(), time_info[1].strip()

        if DEBUG:
            print(f"Read event time from 7Point: '{start_time}' - '{end_time}'")

        event.start_time = parse_time_12h(start_time)
        event.end_time = parse_time_12h(end_time)

        if DEBUG:
            print(f"Event Time Parsed: {event.start_time} - {event.end_time}")

    else:
        event.start_time = None
        event.end_time = None
        event.error = "No start time or end time"
        raise Exception("No start time or end time") # Having no start or end times is fatal. An event should not be processed if it doesn't have this information




def calc_unlock_time(event):

    if event.catering_access_time is not None:
        rounded_t = (
            event.catering_access_time.start_of("hour")
            .add(minutes=(event.catering_access_time.minute // 30) * 30)
        )
        rounded_t = rounded_t.subtract(minutes=30)
        return rounded_t.format("h:mm A")

    if event.access_time is not None:
        rounded_t = (
            event.access_time.start_of("hour")
            .add(minutes=(event.access_time.minute // 30) * 30)
        )
        rounded_t = rounded_t.subtract(minutes=30)
        return rounded_t.format("h:mm A")

    else:
        rounded_t = (
            event.start_time.start_of("hour")
            .add(minutes=(event.start_time.minute // 30) * 30)
        )
        rounded_t = rounded_t.subtract(minutes=30)
        return rounded_t.format("h:mm A")


def calc_greet_time(event):
    if event.access_time is not None:

        t = event.access_time
        rounded_t = (t.start_of("hour").add(minutes=(t.minute // 30) * 30)).format("h:mm A")
        event.access_time = rounded_t
        return event.access_time.format("h:mm A")
    else:
        return event.start_time.format("h:mm A")


def round_event_times(event):
    try:
        if event.start_time is not None:
            t = parse_time_12h(event.start_time)
            rounded_t = (t.start_of("hour").add(minutes=(t.minute // 30) * 30)).format("h:mm A")
            event.start_time = rounded_t
        if event.access_time is not None:
            t = parse_time_12h(event.access_time)
            rounded_t = (t.start_of("hour").add(minutes=(t.minute // 30) * 30)).format("h:mm A")
            event.access_time = rounded_t
        if event.end_time is not None:
            t = parse_time_12h(event.end_time)
            rounded_t = (t.start_of("hour").add(minutes=-(-t.minute // 30) * 30)).format("h:mm A")
            event.end_time = rounded_t
        if event.catering_access_time is not None:
            t = parse_time_12h(event.catering_access_time)
            rounded_t = (t.start_of("hour").add(minutes=(t.minute // 30) * 30)).format("h:mm A")
            event.catering_access_time = rounded_t
    except Exception as e:
        print("Something went wrong when rounding event times", e)



def write_tasks():
    global task_list
    json.dump(task_list, open("tasks.json", "w"), default=lambda o: o.__dict__, indent=4)

def read_irrelevant_rooms():
    global irrelevant_rooms
    f = open(irrelevant_rooms_path, "r")
    contents = f.read()
    contents = contents.strip().split(',\n')
    f.close()
    for content in contents:
        irrelevant_rooms.add(content.strip())












def process_event_info(event_locator, event_details_locator):
    """
    Extract event info from the 7PointOps Daily Setup event page.
    If an error occurs, the event's error field is populated with the Exception
    :param event_locator: the html component containing the event room number
    :param event_details_locator: the html component containing all event details (start time, end time, access time, etc.)
    :return: an Event dataclass object
    """
    global irrelevant_rooms

    event = Event()
    try:


        set_event_room_num(event, event_locator)
        print("Event room:", event.room)

        if event.room in irrelevant_rooms:
            print("Irrelevant room!")
            return None

        event_locator.locator(".mat-column-ends").click()
        event_details_locator.locator(".mdc-tab__text-label").get_by_text("Event Details").click()


        set_event_time(event, event_details_locator.locator(".details-grid"))
        print("Event start time:", event.start_time)
        print("Event end time:", event.end_time)
        event.access_time = event.start_time
        # set_event_access_time(event, page)
        # print("Event access time:", event.access_time)
        # print("Catering access time:", event.catering_access_time)
        # round_event_times(event)
        # print("Event rounded start time:", event.start_time)
        # print("Event rounded end time:", event.end_time)
        # print("Event rounded access time:", event.access_time)
        # print("Event rounded catering time: ", event.catering_access_time)
        set_event_setup_desc(event, event_locator)
        print("Event setup:", event.setup_desc)

        return event

    except Exception as e:
        print("There was an error processing an event: ", e)










# Event example:    Event(room, setup_desc, start_time, end_time, access_time, error)
#                   Event('4265', 'Conference, 12', '6:30 PM', '8:00 PM', '6pm', None)
def generate_event_tasks(event):
    """
    Based on an event, generates a list of associated tasks
    :return:
    """
    if event is None:
        return
    if event.room is None or event.start_time is None or event.end_time is None:
        return

    global task_list

    unlock_task = Task()
    greet_task = Task()
    reset_task = Task()
    lock_task = Task()

    # Unlock
    unlock_task.time = calc_unlock_time(event)
    unlock_task.room = event.room
    unlock_task.type = "unlock"


    # Greet
    greet_task.time = calc_greet_time(event)
    greet_task.room = event.room
    greet_task.type = "greet"

    # Reset
    t = event.end_time
    rounded_t = (t.start_of("hour").add(minutes=-(-t.minute // 30) * 30)).format("h:mm A")
    reset_task.time = rounded_t

    reset_task.room = event.room
    reset_task.type = "reset"
    reset_task.more_info = event.setup_desc

    # Lock
    lock_task.time = rounded_t
    lock_task.room = event.room
    lock_task.type = "lock"

    task_list[unlock_task.time].append(unlock_task)
    task_list[greet_task.time].append(greet_task)
    task_list[reset_task.time].append(reset_task)
    task_list[lock_task.time].append(lock_task)








def get_schedule():
    """
    Scan 7PointOps Book page and retrieve data for each event happening on the current day
    :return: a list of events
    """
    # event_list = []

    # load username and password
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    read_irrelevant_rooms() # get all the rooms OPS don't care about

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        login(page)

        eventLocator, eventDetailsLocator = load_event_table(page)

        i = 0
        for event, event_details in zip(eventLocator.all(), eventDetailsLocator.all()):
            print(f"----------------- {i} -----------------")
            event_info = process_event_info(event, event_details) # scrape the relevant event info and save it
            # generate_event_tasks(event_info, irrelevant_rooms) # create each task associated with an event
            i += 1
            generate_event_tasks(event_info)
            # event_list.append(event_info)

        browser.close()

    # return event_list


def login(page):
    print("Logging in...")
    page.goto("https://www.7pointops.com/sign-in")
    page.locator("#email").fill(os.getenv("USERNAME"))
    # page.wait_for_timeout(3000)

    page.get_by_text("Continue").click()
    page.locator("#password").wait_for()
    # page.wait_for_timeout(3000)

    page.locator("#password").fill(os.getenv("PASSWORD"))
    page.get_by_role("button", name="Login").click()
    page.wait_for_url("https://www.7pointops.com/daily-setup")


def load_event_table(page):
    print("Loading events table...")
    # waits for "loaded at x:xx" to appear on the Events table - this indicates that all events have loaded on the page
    container = page.locator('sp-table-container[tablelabel="Events"]')
    table = container.locator('.table-wrapper')

    event_rows = table.locator("tr.table-row")
    event_detail_rows = table.locator("tr.details-row")
    event_rows.first.wait_for(state="visible")

    print("event num:", event_rows.count())

    return event_rows, event_detail_rows


if __name__ == "__main__":
    get_schedule()
    write_tasks()

    # 2) Start server
    handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("localhost", PORT), handler)

    # 3) Open browser
    webbrowser.open("http://localhost:8000")

    print("Serving at http://localhost:8000")
    print("Press Ctrl+C to stop")

    # 4) Keep server running
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.shutdown()