import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import argparse
import json
import http.client
import urllib
import ai_gen_files.successful_response_func as response_ai_gen
import hashlib
import shelve
import logging
from auth import login_and_get_phpid
import pytz

# Configure logging
logging.basicConfig(filename=os.path.expanduser('~/Projects/tennis/logs/info.txt'), level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s', filemode='a')

# TODO: Let people know when they missed times.
# TODO: Add booking capability.
# TODO: Add rate limiting for phone numbers in case someone decides to spam my twilio.
# TODO: Let people know how many others have been notified of these available courts. (probably none for now)

class QueryKey:
    def __init__(self, phone_number, date, start_time, end_time, activity):
        self.phone_number = phone_number
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.activity = activity
        self.hash = self.generate_hash()

    @classmethod
    def from_query(cls, query):
        # Create a QueryKey instance from a query dictionary
        return cls(
            phone_number=query['phone_number'],
            date=query['date'],
            start_time=query['time_range'][0],
            end_time=query['time_range'][1],
            activity=query['activity_filter']
        )

    def generate_hash(self):
        unique_string = f"{self.phone_number}-{self.date}-{self.start_time}-{self.end_time}-{self.activity}"
        return hashlib.md5(unique_string.encode()).hexdigest()

    def __repr__(self):
        return f"({self.phone_number}, {self.date}, {self.start_time}, {self.end_time}, {self.activity})"

###################### START CONSTANTS ####################
MUTE = True
MUTED_NUMBERS = ['test']

cookies = {
    ######## REPLACE THIS IF GOT LOGIN PAGE!!! ########
    'PHPSESSID': 'ql1m8sc43aaj3636ifr1nmcct3',
    'SessionExpirationTime': '1718716227',
    'isLoggedIn': '1',
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/111.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://gtc.clubautomation.com/event/reserve-court-new',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest',
    'X-INSTANA-T': 'f2983719aaf08d0e',
    'X-INSTANA-S': 'f2983719aaf08d0e',
    'X-INSTANA-L': '1,correlationType=web;correlationId=f2983719aaf08d0e',
    'Origin': 'https://gtc.clubautomation.com',
    'Connection': 'keep-alive',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    # Requests doesn't support trailers
    # 'TE': 'trailers',
}

params = {
    'ajax': 'true',
}

#################### END CONSTANTS #############################

###################### PARSE INPUT #############################
# Parse inputs
parser = argparse.ArgumentParser(description='Accept input variables')
parser.add_argument('--debug', action='store_true', help='Enable debug mode')
args = parser.parse_args()

_debug = args.debug

###################### END PARSE INPUT #############################
###################### FUNCTIONS ###############################


def get_raw_response(date, interval, cookie):
    '''
    date: E.g. '04/13/2023'
    interval: '30', '45', or '60'
    '''

    data = {
        'reservation-list-page': '1',
        'user_id': '25397',
        'event_member_token_reserve_court': '2410e5f6c2ba7236467267b371223e6c',
        'current_guest_count': '0',
        'component': '2',
        'club': '-1',
        'location': '-1',
        'host': '25397',
        'ball_machine': '0',
        'date': date,
        'interval': interval,
        'time-reserve': '',
        'location-reserve': '',
        'surface-reserve': '',
        'courtsnotavailable': '',
        'join-waitlist-case': '1',
    }

    cookies['PHPSESSID'] = cookie

    response = requests.post(
        'https://gtc.clubautomation.com/event/reserve-court-new',
        params=params,
        cookies=cookies,
        headers=headers,
        data=data,
    )
    return response


def filter_activities_by_time_and_activity(activities, input_time_range, raw_activity_filter):
    filtered_activities = {}
    lower_time_obj = datetime.strptime(input_time_range[0], '%I:%M%p')
    upper_time_obj = datetime.strptime(input_time_range[1], '%I:%M%p')
    activity_filter = strip_activity(raw_activity_filter)

    for activity, times in activities.items():
        activity = strip_activity(activity)
        # Filter by activity filter
        if activity_filter != '' and activity != activity_filter:
            continue
        filtered_times = []
        for time_str in times:
            time_obj = datetime.strptime(time_str, '%I:%M%p')
            if lower_time_obj <= time_obj and time_obj <= upper_time_obj:
                filtered_times.append(time_str)
        if filtered_times:
            filtered_activities[activity] = filtered_times
    return filtered_activities


def send_notification(title, body, url, api_token, user_token):
    logging.info("Message sent.")
    if _debug:
        logging.info(f"user_token,api_token={user_token},{api_token}")

    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
                 urllib.parse.urlencode({
                     "token": api_token,
                     "user": user_token,
                     "message": body,
                     "url": url,
                     "title": title,
                 }), {"Content-type": "application/x-www-form-urlencoded"})
    conn.getresponse()

from twilio.rest import Client

def send_text(phone_number, activities, query):
    message = f"Activities available for {phone_number}:\n"
    for activity, times in activities.items():
        message += f"{activity}: {times}\n"
    date = query['date']
    start_time = query['time_range'][0]
    end_time = query['time_range'][1]
    message += f"Go to https://gtc.clubautomation.com/ and search:\nDate: {date}\nStart Time: {start_time}\nEnd Time: {end_time}\n"
    message += """To stop alerts, go to https://bookmecourts.fly.dev/. \
For questions or complaints please email bensc77@gmail.com."""

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")

    client = Client(account_sid, auth_token)

    client.messages.create(
        body=message,
        from_=from_number,
        to=phone_number
    )

    logging.info(f"Sending text to {phone_number}:\n{message}")
    if _debug:
        logging.info("Message sent using Twilio.")
        


def strip_activity(activity):
    return activity.replace("-", "").replace(" ", "")

# Testing only.
def fetch_user_queries():
    
    # TODO(Charlie, Dice): Fetch these from DB.
    return {'000-000-0000': {'date': '06/18/2024', 'interval': '30', 'time_range': ['11:00AM', '5:00PM'], 'activity_filter': 'Pickleball / Mini Tennis', 'name': 'Fabian'},
            '111-111-1111': {'date': '06/25/2024', 'interval': '60', 'time_range': ['3:00PM', '8:00PM'], 'activity_filter': 'Tennis', 'name': 'Johnboy'},
            '222-222-2222': {'date': '06/18/2024', 'interval': '30', 'time_range': ['11:00AM', '5:00PM'], 'activity_filter': 'Tennis', 'name': 'Jacobi'}}


def ensure_logged_in():
    # Try to fetch a response with dummy data to check login status
    with shelve.open(os.path.expanduser('~/Projects/tennis/session_db')) as db:
        cookie = db.get('PHPSESSID', cookies['PHPSESSID'])  # Retrieve the PHPSESSID from the database, if available
    dummy_response = get_raw_response('01/01/2000', '30', cookie)  # Use a dummy date and interval
    if 'First time here' in dummy_response.text:
        cookie = login_and_get_phpid()
        logging.info(f"Logged in with new cookie: {cookie}")
        print("logging in with new cookie.")
        with shelve.open(os.path.expanduser('~/Projects/tennis/session_db')) as db:
            db['PHPSESSID'] = cookie  # Store the new PHPSESSID in the database
    return cookie

def fetch_available_times(input_date, input_interval, input_time_range, activity_filter, cookie):
    # Get response
    response = get_raw_response(input_date, input_interval, cookie)

    if _debug:
        logging.info("Raw response:\n" + response.text)

    soup = BeautifulSoup(response.text, 'html.parser')

    if 'First time here' in response.text:
        e_string = "ERROR: Got login page. Try replacing PHP Session ID with a fresh one!"
        logging.error(e_string)
        print(e_string)
        send_notification("ERROR!", e_string, "", api_token, user_token)
        exit()

    activities = response_ai_gen.func(response.text)

    logging.info(f"Activities: {activities}")

    filtered_activities = filter_activities_by_time_and_activity(
        activities, input_time_range, activity_filter)    

    return filtered_activities

def format_phone_number(raw_phone):
    if raw_phone.startswith('+1'):
        return raw_phone
    elif raw_phone.startswith('1'):
        return '+' + raw_phone
    else:
        return '+1' + raw_phone

def fetch_and_convert_data():
    # URL of the API
    url = 'https://bookmecourts.fly.dev/api/v1/bookings'
    
    # Send a GET request to the API
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()['data']
        logging.info(f"Data fetched successfully from API: {data}")
        
        # Convert the data to the desired format
        converted_data = {}
        for item in data:

            phone_number = format_phone_number(item['phone_number'])
            start_time = item['start_time']
            end_time = item['end_time']
            activity = item['activity']

            # Convert UI drop down activity to correct format.
            if activity == 'Pickleball':
                activity = 'Pickleball / Mini Tennis'
            elif activity is None:
                activity = 'Tennis'
            
            # Skip test
            if phone_number in MUTED_NUMBERS:
                continue
            
            # Extract date and time range from start_time and end_time
            date = start_time.split('T')[0]  # Get the date part
            start_time_obj = datetime.strptime(start_time.split('T')[1][:5], '%H:%M')
            end_time_obj = datetime.strptime(end_time.split('T')[1][:5], '%H:%M')
            
            # Format time to 12-hour format with AM/PM
            start_time_formatted = start_time_obj.strftime('%I:%M%p')
            end_time_formatted = end_time_obj.strftime('%I:%M%p')
            
            # Create the formatted entry
            # Note: if user has multiple entries, we just take the latest
            query_key = QueryKey.from_query({
                'phone_number': phone_number,
                'date': date,
                'time_range': [start_time_formatted, end_time_formatted],
                'activity_filter': activity
            })
            converted_data[query_key] = {
                'phone_number': phone_number,
                'date': date,
                'interval': '60',  # Default interval
                'time_range': [start_time_formatted, end_time_formatted],  # Default time range
                'activity_filter': activity,  # Default activity filter
                'name': 'Dummy'  # Default name
            }
        return converted_data
    else:
        logging.error("Failed to fetch data from API")
        return {}

# Define the path for the notified_db
NOTIFIED_DB_PATH = os.path.expanduser('~/Projects/tennis/notified_db')

def should_notify(query):
    with shelve.open(NOTIFIED_DB_PATH) as db:
        return QueryKey.from_query(query).hash not in db  # Use the hash attribute

def update_notified(query):
    with shelve.open(NOTIFIED_DB_PATH) as db:
        # Store the datetime and query as a tuple
        db[QueryKey.from_query(query).hash] = (datetime.now().isoformat(), query)

def remove_old_entries():
    twelve_hours_ago = datetime.now() - timedelta(hours=12)
    with shelve.open(NOTIFIED_DB_PATH) as db:
        keys_to_delete = [key for key, value in db.items() if datetime.fromisoformat(value[0]) < twelve_hours_ago]
        for key in keys_to_delete:
            del db[key]

def remove_query(query):
    with shelve.open(NOTIFIED_DB_PATH) as db:
        query_hash = QueryKey.from_query(query).hash
        if query_hash in db:
            del db[query_hash]

def should_run():
    pacific_time = datetime.now(pytz.timezone('US/Pacific'))
    current_hour = pacific_time.hour
    if current_hour >= 22 or current_hour < 8:
        logging.info(f"{pacific_time}: Script not run due to night time hours.")
        return False
    return True


def process_queries(queries):
    activity_results = {}
    
    cookie = ensure_logged_in()
    
    for key, query in queries.items():
        input_date = query['date']
        phone = query['phone_number']
        input_interval = query['interval']
        input_time_range = query['time_range']
        activity_filter = query['activity_filter']
        
        filtered_activities = fetch_available_times(
            input_date, input_interval, input_time_range, activity_filter, cookie)
   
        if len(filtered_activities) == 0:
            logging.info(f"No activities found for {query}")
            remove_query(query)
        
        if len(filtered_activities) > 0:
            logging.info(f"Filtered activities found for {query}")
            if should_notify(query):
                logging.info(f"Sending text to {phone} with {filtered_activities} for {query}")
                if not MUTE:
                    send_text(phone, filtered_activities, query)
                    update_notified(query)
                activity_results[str(QueryKey.from_query(query))] = filtered_activities
            else:
                logging.info(f"Notification not sent for {query}")
    
    return activity_results

def log_activity_results(activity_results):
    """
    Logs the activity results to a file with a timestamp.
    """
    try:
        with open(os.path.expanduser('~/Projects/tennis/logs/activity_results.txt'), 'a') as f:
            entry = {"timestamp": str(datetime.now()), "data": activity_results}
            json.dump(entry, f)
            f.write("\n")
    except FileNotFoundError:
        os.makedirs(os.path.expanduser('~/Projects/tennis/logs'), exist_ok=True)
        with open(os.path.expanduser('~/Projects/tennis/logs/activity_results.txt'), 'a') as f:
            entry = {"timestamp": str(datetime.now()), "data": activity_results}
            json.dump(entry, f)
            f.write("\n")

if __name__ == "__main__":
    if not should_run():
        exit()

    load_dotenv()
    api_token = os.getenv('PUSHOVER_API_TOKEN')
    user_token = os.getenv('PUSHOVER_USER_TOKEN')
    
    

    remove_old_entries()

    queries = fetch_and_convert_data()
    logging.info(f"Queries: {queries}")
    activity_results = process_queries(queries)

    if len(activity_results) > 0 and not MUTE:
        send_notification("Activities available!", activity_results,
                          'https://gtc.clubautomation.com', api_token, user_token)

    log_activity_results(activity_results)

    logging.info(f"Activity results: {activity_results}")
