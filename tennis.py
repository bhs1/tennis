import requests
from bs4 import BeautifulSoup
from datetime import datetime
import argparse
import json
import http.client, urllib

###################### START CONSTANTS ####################

cookies = {
    'PHPSESSID': 'aqvhp2orooej1li87n4cev63hk',
    'SessionExpirationTime': '1696077770',
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

parser.add_argument('--input_date', type=str, help='Input date in mm/dd/yyyy format')
parser.add_argument('--input_interval', type=int, help='Input interval in minutes')
parser.add_argument('--input_time_range', nargs='+', type=str, help='Input time range as a list of start and end times in hh:mm[am/pm] format')
parser.add_argument('--api_token', help="Your api token")
parser.add_argument('--user_token', help="Your user token")
parser.add_argument('--debug', action='store_true', help='Enable debug mode')
parser.add_argument('--activity_filter', type=str, help='Tennis or  Pickleball / Mini Tennis')

args = parser.parse_args()

input_date = args.input_date
input_interval = args.input_interval
input_time_range = args.input_time_range
user_token=args.user_token
api_token=args.api_token
_debug = args.debug
activity_filter = args.activity_filter

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

def filter_activities_by_time_and_activity(activities, input_time_range, activity_filter):
    filtered_activities = {}
    lower_time_obj = datetime.strptime(input_time_range[0], '%I:%M%p')
    upper_time_obj = datetime.strptime(input_time_range[1], '%I:%M%p')
    for activity, times in activities.items():
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

# TODO: Fix this so that you can send to specific devices with specific times.
def send_notification(title, body, url, api_token, user_token):
    print("Message sent.")
    if _debug:
        print("user_token,api_token=",user_token,api_token)

    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
    urllib.parse.urlencode({
        "token": api_token,
        "user": user_token,
        "message": body,
        "url": url,
        "title": title,
    }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()

########################## FUNCTIONS ##############################

# Get response
response = get_raw_response(input_date, input_interval)

if _debug:
    print("Raw response:\n"  + response.text)

soup = BeautifulSoup(response.text, 'html.parser')

if 'First time here' in response.text:
    e_string = "ERROR: Got login page. Try replacing PHP Session ID with a fresh one!"
    print(e_string)
    send_notification("ERROR!", e_string, "",api_token, user_token)

activities = {}

for td in soup.find_all('td'):
    activity = td.find('b').text
    times = []
    for a in td.find_all('a'):
        times.append(a.text.strip())
    activities[activity] = times 

if _debug:
    print(activities)

filtered_activities = filter_activities_by_time_and_activity(activities, input_time_range, activity_filter)

# If filtered acttivities is not empty, send a pushbullet notification (with info + link)
if len(filtered_activities) > 0:
    send_notification("Activities available!", filtered_activities, 'https://gtc.clubautomation.com', api_token, user_token)

print(filtered_activities)
