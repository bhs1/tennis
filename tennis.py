import requests


# Consider making SessionExpirationTime some time in the future?
cookies = {
    'PHPSESSID': 'fs74bsne1lrk6bpbfbnh5ble7g',
    'SessionExpirationTime': '1671028573',
    'isLoggedIn': '1',
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:108.0) Gecko/20100101 Firefox/108.0',
    'Accept': '*/*',
    'Accept-Language': 'en-US,en;q=0.5',
    # 'Accept-Encoding': 'gzip, deflate, br',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-Requested-With': 'XMLHttpRequest',
    'X-INSTANA-T': '7caeadc78d2e80d2',
    'X-INSTANA-S': '7caeadc78d2e80d2',
    'X-INSTANA-L': '1,correlationType=web;correlationId=7caeadc78d2e80d2',
    'Origin': 'https://gtc.clubautomation.com',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Referer': 'https://gtc.clubautomation.com/event/reserve-court-new',
    # 'Cookie': 'PHPSESSID=fs74bsne1lrk6bpbfbnh5ble7g; SessionExpirationTime=1671028573; isLoggedIn=1',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    # Requests doesn't support trailers
    # 'TE': 'trailers',
}

params = {
    'ajax': 'true',
}

data = {
    'reservation-list-page': '1',
    'user_id': '25397',
    'event_member_token_reserve_court': 'e98f270b2b10cf3e738f306d8b9e4a8e',
    'current_guest_count': '0',
    'component': '2',
    'club': '-1',
    'location': '-1',
    'host': '25397',
    'ball_machine': '0',
    'date': '12/15/2022',
    'interval': '30',
    'time-reserve': '',
    'location-reserve': '',
    'surface-reserve': '',
    'courtsnotavailable': '',
    'join-waitlist-case': '0',
}

response = requests.post(
    'https://gtc.clubautomation.com/event/reserve-court-new',
    params=params,
    cookies=cookies,
    headers=headers,
    data=data,
)

print(response.text)
