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

cookies = {
    ######## REPLACE THIS IF GOT LOGIN PAGE!!! ########
    'PHPSESSID': 'gkh6l4o78mgvr1vflh86aa8g5m',
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


def strip_activity(activity):
    return activity.replace("-", "").replace(" ", "")


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


########################## FUNCTIONS ##############################
if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()

    # Now you can use os.getenv to access your variables
    api_token = os.getenv('PUSHOVER_API_TOKEN')
    user_token = os.getenv('PUSHOVER_USER_TOKEN')
    print(f"API_TOKEN: {api_token}")
    print(f"USER_TOKEN: {user_token}")

    queries = fetch_user_queries()
    activity_results = {}
    for phone, query in queries.items():
        input_date = query['date']
        input_interval = query['interval']
        input_time_range = query['time_range']
        activity_filter = query['activity_filter']
        filtered_activities = fetch_available_times(
            input_date, input_interval, input_time_range, activity_filter)
        if len(filtered_activities) > 0:
            activity_results[phone] = filtered_activities

    # If filtered activities is not empty, send a pushbullet notification (with info + link)
    if len(activity_results) > 0:
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
