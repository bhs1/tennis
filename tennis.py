import requests
from bs4 import BeautifulSoup

###################### START CONSTANTS ####################

cookies = {
    'PHPSESSID': '3q6gjdrceq2pp6geqrnpfkeh6b',
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
    # 'Cookie': 'PHPSESSID=3q6gjdrceq2pp6geqrnpfkeh6b; SessionExpirationTime=1681388464; isLoggedIn=1',
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

########################## FUNCTIONS ###############################

# Parse inputs

input_date = '04/13/2023'
input_interval = '60'
input_time_range = ['4:00pm', '7:00pm']


response = get_raw_response(input_date, input_interval)
soup = BeautifulSoup(response.text, 'html.parser')

activities = {}

for td in soup.find_all('td'):
    activity = td.find('b').text
    times = []
    for a in td.find_all('a'):
        times.append(a.text.strip())
    activities[activity] = times

# Next: Filter times by input time range

print(activities)
