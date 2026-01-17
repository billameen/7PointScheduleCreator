import os
import re
from dataclasses import dataclass
from typing import Optional, Tuple, List
from dotenv import load_dotenv, find_dotenv
from playwright.sync_api import sync_playwright
import pendulum


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
}


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
    time_str = time_str.strip().upper()

    for fmt in TIME_FORMATS:
        try:
            return pendulum.from_format(time_str, fmt, tz=tz)
        except Exception:
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
    error: Optional[str] = None

    def print(self):
        print(self.room)
        print(self.setup_desc)
        print(self.start_time)
        print(self.end_time)
        print(self.access_time)
        print(self.error)


# This dataclass will store all information pertaining to a task
@dataclass
class Task:
    time: Optional[str] = None
    room: Optional[str] = None
    type: Optional[str] = None
    more_info: Optional[str] = None
    error: Optional[str] = None





def set_event_room_num(event, page):
    if page.locator(".roomDesc").count() > 0:
        room_num = page.locator(".roomDesc").inner_text()
        event.room = room_num
        print("room: ", event.room)
    else:
        event.room = None
        event.error = "No room number"
        raise Exception("No room number") # Having no room number is fatal. An event should not be processed if it doesn't have a room number.


def set_event_setup_desc(event, page):
    if page.locator("h3").count() > 0:
        header_info = page.locator("h3").inner_text()
        event.setup_desc = get_setup_desc(header_info)
        print("setup desc: ", event.setup_desc)
    else:
        event.setup_desc = None
        event.error = "No setup description"
        print("setup desc: None")


def set_event_time(event, page):
    if page.locator(".groupDetails>dl").count() > 0:
        time_info = get_event_time(page.locator(".groupDetails>dl").first.inner_html())
        event.start_time = time_info[0]
        print("start time: ", event.start_time)
        event.end_time = time_info[1]
        print("end time: ", event.end_time)
    else:
        event.start_time = None
        event.end_time = None
        event.error = "No start time or end time"
        raise Exception("No start time or end time") # Having no start or end times is fatal. An event should not be processed if it doesn't have this information


def set_event_access_time(event, page):
    if page.get_by_text('Access Time').count() > 0:
        access_time = get_access_time(page)
        event.access_time = access_time
        print("access time: ", event.access_time)
    else:
        event.access_time = None
        event.error = "No access time"
        print("access time: None")



# Expected input: Med Deli Catering Meeting - Talley Student Union - 3220 - (Conference, 5, act. 0)
# Expected output: Conference, 5
def get_setup_desc(desc: str) -> str:
    """
    Gets the setup description (i.e. Conference 15, Classroom 40, etc.)
    :param desc: the heading (<h3>) of the event description
    """
    setup = desc.split('(')[1].split(', act.')[0].strip()
    return setup


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

    assert re.fullmatch(time_pattern, start_time), f"Invalid start time: {start_time}"
    assert re.fullmatch(time_pattern, end_time), f"Invalid end time: {end_time}"

    return start_time, end_time


def get_access_time(page):
    try:
        access_time_html = page.get_by_text("Access Time").inner_html(timeout=1000).split('<p class="preWrap indent">')[1].strip().split('</p>')[0].strip()
        access_time = re.search(time_pattern, access_time_html).group()

        assert access_time_html and access_time_html.strip() != '', f'Invalid event access time: {access_time_html}'

        return access_time

    except Exception as e:
        raise e


def calc_unlock_time(event):

    if event.access_time is not None:
        t = parse_time_12h(event.access_time)
        rounded_t = (
            t.start_of("hour")
            .add(minutes=(t.minute // 30) * 30)
        )
        rounded_t.subtract(minutes=30)
        return rounded_t.format("h:mm A")

    else:
        t = parse_time_12h(event.start_time)
        rounded_t = (
            t.start_of("hour")
            .add(minutes=(t.minute // 30) * 30)
        )
        rounded_t.subtract(minutes=30)
        return rounded_t.format("h:mm A")
# def get_previous_setup(page):




def process_event_info(page):
    """
    Extract event info from the 7PointOps Event Details HTML page.
    If an error occurs, the event's error field is populated with the Exception
    :param page: the webpage containing the event details
    :return: an Event dataclass object
    """
    event = Event()
    try:
        # make sure page has loaded
        page.locator("#ngplus-overlay-container").wait_for(state="hidden")

        set_event_room_num(event, page)
        set_event_setup_desc(event, page)
        set_event_time(event, page)
        set_event_access_time(event, page)

        return event

    except Exception as e:
        print("There was an error processing an event: ", e)


def get_schedule() -> List[Event]:
    """
    Scan 7PointOps Book page and retrieve data for each event happening on the current day
    :return: a list of events
    """
    event_list = []

    # load username and password
    dotenv_path = find_dotenv()
    load_dotenv(dotenv_path)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # login
        page.goto("https://www.7pointops.com/login")
        page.locator("#userName").fill(os.getenv("USERNAME"))
        page.locator("#password").fill(os.getenv("PASSWORD"))

        with page.expect_navigation():
            page.click("#loginButton")

        page.wait_for_load_state("networkidle")
        page.goto("https://www.7pointops.com/book")
        page.wait_for_selector(".eventBarText", timeout=15000)

        print("Number of events:", page.locator(".eventBarText").count())
        i = 0

        for event in page.locator(".eventBarText").all():
            print(f"----------------- {i} -----------------")
            event.click() # click to see event details
            event_info = process_event_info(page) # scrape the relevant event info and save it
            generate_event_tasks(event_info)
            page.get_by_role("button").get_by_text("×").click() # exit the event details page
            i += 1

        browser.close()

    return event_list


# Event example:    Event(room, setup_desc, start_time, end_time, access_time, error)
#                   Event('4265', 'Conference, 12', '6:30 PM', '8:00 PM', '6pm', None)
def generate_event_tasks(event):
    """
    Based on an event, generates a list of associated tasks
    :return:
    """
    if event is None:
        return
    else:
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
    unlock_task.type = "Unlock"


    # Greet
    greet_task.time = event.start_time
    greet_task.room = event.room
    greet_task.type = "Greet"

    # Reset
    reset_task.time = event.end_time
    reset_task.room = event.room
    reset_task.type = "Reset"
    reset_task.more_info = event.setup_desc

    # Lock
    lock_task.time = event.end_time
    lock_task.room = event.room
    lock_task.type = "Lock"

    task_list[unlock_task.time].append(unlock_task)
    task_list[greet_task.time].append(greet_task)
    task_list[reset_task.time].append(reset_task)
    task_list[lock_task.time].append(lock_task)


def get_all_tasks():
    return task_list


if __name__ == "__main__":
    get_schedule()
    print("tasks:\n\n", task_list)