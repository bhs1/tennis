import requests
from bs4 import BeautifulSoup
from datetime import datetime
import argparse
import json
import http.client, urllib

###################### START CONSTANTS ####################

cookies = {
    'PHPSESSID': 'dctuhjqn7fbliji6blihqgmbn9',
    'SessionExpirationTime': '1681388464',
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

def filter_activities_by_time(activities, input_time_range):
    filtered_activities = {}
    for activity, times in activities.items():
        filtered_times = []
        for time_str in times:
            time_obj = datetime.strptime(time_str, '%I:%M%p')
            if input_time_range[0].lower() <= time_str.lower() <= input_time_range[1].lower():
                filtered_times.append(time_str)
        if filtered_times:
            filtered_activities[activity] = filtered_times
    return filtered_activities

def send_notification(title, body, url, pb_token):
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
    urllib.parse.urlencode({
        "token": "asg21wetbwa33qgk8vfhm7dodat6vp",
        "user": "uc1dk4b66zk4kpbztp8dk1wzow6j2r",
        "message": body,
        "url": url,
        "title": title,
    }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()

########################## FUNCTIONS ##############################


# Parse inputs
parser = argparse.ArgumentParser(description='Accept input variables')

parser.add_argument('--input_date', type=str, help='Input date in mm/dd/yyyy format')
parser.add_argument('--input_interval', type=int, help='Input interval in minutes')
parser.add_argument('--input_time_range', nargs='+', type=str, help='Input time range as a list of start and end times in hh:mm[am/pm] format')
parser.add_argument('--pb_token', help="Your pushbot token")
parser.add_argument('--debug', action='store_true', help='Enable debug mode')

args = parser.parse_args()

input_date = args.input_date
input_interval = args.input_interval
input_time_range = args.input_time_range
pb_token=args.pb_token
debug = args.debug

# Get response
response = get_raw_response(input_date, input_interval)

if debug:
    print("Raw response:\n"  + response.text)

soup = BeautifulSoup(response.text, 'html.parser')

if 'First time here' in response.text:
    print("ERROR: Got login page. Try replacing PHP Session ID with a fresh one!")

activities = {}

for td in soup.find_all('td'):
    activity = td.find('b').text
    times = []
    for a in td.find_all('a'):
        times.append(a.text.strip())
    activities[activity] = times

filtered_activities = filter_activities_by_time(activities, input_time_range)

# If filtered acttivities is not empty, send a pushbullet notification (with info + link)
if len(filtered_activities) > 0:
    send_notification("Activities available!", filtered_activities, 'https://gtc.clubautomation.com', pb_token)

print(filtered_activities)
