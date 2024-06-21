import os
from dotenv import load_dotenv
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import argparse
import json
import http.client
import urllib
import ai_gen_files.successful_response_func as response_ai_gen

###################### START CONSTANTS ####################
MUTE = False
MUTED_NUMBERS = ['9179038697',
                 'test-test-test',
                 'test',
                 'test1',
                 '6467611319']

ALREADY_BOOKED_NUMBERS = [
    '3042765830', # Akshay
    '6105634153' # Jack
]

cookies = {
    ######## REPLACE THIS IF GOT LOGIN PAGE!!! ########
    'PHPSESSID': '8e8uc4n950se7el9l7mdt72csv',
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


def get_raw_response(date, interval):
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
    print("Message sent.")
    if _debug:
        print("user_token,api_token=", user_token, api_token)

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
For questions or complaints please email bookingbotbros@gmail.com."""

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_PHONE_NUMBER")

    client = Client(account_sid, auth_token)

    client.messages.create(
        body=message,
        from_=from_number,
        to=phone_number
    )

    print(f"Sending text to {phone_number}:\n{message}")
    if _debug:
        print("Message sent using Twilio.")
        


def strip_activity(activity):
    return activity.replace("-", "").replace(" ", "")

# Testing only.
def fetch_user_queries():
    
    # TODO(Charlie, Dice): Fetch these from DB.
    return {'000-000-0000': {'date': '06/18/2024', 'interval': '30', 'time_range': ['11:00AM', '5:00PM'], 'activity_filter': 'Pickleball / Mini Tennis', 'name': 'Fabian'},
            '111-111-1111': {'date': '06/25/2024', 'interval': '60', 'time_range': ['3:00PM', '8:00PM'], 'activity_filter': 'Tennis', 'name': 'Johnboy'},
            '222-222-2222': {'date': '06/18/2024', 'interval': '30', 'time_range': ['11:00AM', '5:00PM'], 'activity_filter': 'Tennis', 'name': 'Jacobi'}}


def fetch_available_times(input_date, input_interval, input_time_range, activity_filter):
    # Get response
    response = get_raw_response(input_date, input_interval)

    if _debug:
        print("Raw response:\n" + response.text)

    soup = BeautifulSoup(response.text, 'html.parser')

    if 'First time here' in response.text:
        e_string = "ERROR: Got login page. Try replacing PHP Session ID with a fresh one!"
        print(e_string)
        send_notification("ERROR!", e_string, "", api_token, user_token)

    activities = response_ai_gen.func(response.text)

    if _debug:
        print(activities)

    filtered_activities = filter_activities_by_time_and_activity(
        activities, input_time_range, activity_filter)    

    return filtered_activities

def fetch_and_convert_data():
    # URL of the API
    url = 'https://bookmecourts.fly.dev/api/v1/bookings'
    
    # Send a GET request to the API
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        data = response.json()['data']
        
        # Convert the data to the desired format
        converted_data = {}
        for item in data:

            phone_number = item['phone_number']
            start_time = item['start_time']
            end_time = item['end_time']
            activity = item['activity']

            # Convert UI drop down activity to correct format.
            if activity == 'Pickleball':
                activity = 'Pickleball / Mini Tennis'
            elif activity is None:
                activity = 'Tennis'
            
            # Skip test
            if phone_number in MUTED_NUMBERS or phone_number in ALREADY_BOOKED_NUMBERS:
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
            converted_data[phone_number] = {
                'date': date,
                'interval': '60',  # Default interval
                'time_range': [start_time_formatted, end_time_formatted],  # Default time range
                'activity_filter': activity,  # Default activity filter
                'name': 'Dummy'  # Default name
            }
        return converted_data
    else:
        print("Failed to fetch data from API")
        return {}


########################## FUNCTIONS ##############################
if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()

    # Now you can use os.getenv to access your variables
    api_token = os.getenv('PUSHOVER_API_TOKEN')
    user_token = os.getenv('PUSHOVER_USER_TOKEN')
    print(f"API_TOKEN: {api_token}")
    print(f"USER_TOKEN: {user_token}")
    
    # Test
    #send_text("+19179038697", {"Tennis": ["11:00AM", "5:00PM"]}, {"date": "06/18/2024", "interval": "30", "time_range": ["11:00AM", "5:00PM"], "activity_filter": "Tennis", "name": "Fabian"})

    queries = fetch_and_convert_data()
    activity_results = {}
    for phone, query in queries.items():        
        input_date = query['date']
        input_interval = query['interval']
        input_time_range = query['time_range']
        activity_filter = query['activity_filter']
        filtered_activities = fetch_available_times(
            input_date, input_interval, input_time_range, activity_filter)
        if len(filtered_activities) > 0:
            # Uncomment to enable texting
            # send_text(phone, filtered_activities, query)
            activity_results[phone] = filtered_activities

    # If filtered activities is not empty, send a pushbullet notification (with info + link)
    if len(activity_results) > 0 and not MUTE:
        send_notification("Activities available!", activity_results,
                          'https://gtc.clubautomation.com', api_token, user_token)

    # Add to log
    try:
        with open('logs/activity_results.txt', 'a') as f:
            entry = {"timestamp": str(datetime.now()),
                     "data": activity_results}
            json.dump(entry, f)
            f.write("\n")
    except FileNotFoundError:
        os.makedirs('logs', exist_ok=True)
        with open('logs/activity_results.txt', 'a') as f:
            entry = {"timestamp": str(datetime.now()),
                     "data": activity_results}
            json.dump(entry, f)
            f.write("\n")

    print(f"Activity results: {activity_results}")
