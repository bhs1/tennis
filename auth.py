import requests
from bs4 import BeautifulSoup  # Import BeautifulSoup
import os

from dotenv import load_dotenv
load_dotenv()

def log(message):
    print(message)
    with open('logs/login.txt', 'a') as log_file:
        log_file.write(message + "\n")

def login(phpsessionid, login_token):
    # Define login URL and payload
    login_url = 'https://gtc.clubautomation.com/login/login'
    payload = {
        'email': 'bensc77',
        'password': os.getenv('GGP_PASSWORD'),
        'login_token': login_token  # Use the dynamic login token
    }

    # Define headers with dynamic PHPSESSID
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'cookie': f'PHPSESSID={phpsessionid}; __cf_bm=8tCR7FoYm1BwvXrwtkKuI6va1Ikdzt5RR9YU2mDzog4-1719006402-1.0.1.1-lg1PQEgETG0Z_PL6F4l2K9Qbt7WzqNtE.gukpGNLbI0M1aAI9GGL30XuvI4S9xoGLzchfxJAnakVj6NZnJPs2A',
        'origin': 'https://gtc.clubautomation.com',
        'priority': 'u=1, i',
        'referer': 'https://gtc.clubautomation.com/',
        'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        'x-instana-l': '1,correlationType=web;correlationId=1111535075ca1f4f',
        'x-instana-s': '1111535075ca1f4f',
        'x-instana-t': '1111535075ca1f4f',
        'x-requested-with': 'XMLHttpRequest'
    }

    # Perform the login request
    try:
        session = requests.Session()
        response = session.post(login_url, data=payload, headers=headers, verify=True)        

        # Check if login was successful
        if response.status_code == 200 and response.json().get('isLoggedIn', False):
            log("Logged in.")
            return True
        else:
            log("Could not log in.")
            return False

    except requests.RequestException:
        log("Login request failed due to an exception.")
        return False

    finally:
        if 'session' in locals() and session is not None:
            session.close()

def login_and_get_phpid():
    # Define the URL for the GET request
    url = 'https://gtc.clubautomation.com'


    # Create a session and perform the GET request
    with requests.Session() as session:
        log("Getting phpsessionid")
        response = session.get(url)                        
        # Parse the HTML to find the login token
        soup = BeautifulSoup(response.text, 'html.parser')
        login_token = soup.find('input', {'name': 'login_token'})['value']
        log(f"Extracted login token: {login_token}")

        # Use the extracted token in the login function
        cookie = session.cookies.get_dict()['PHPSESSID']
        log(f"PHPSESSID: {cookie}")
        login(cookie, login_token)  # Pass the login token to the login function
    return cookie

if __name__ == "__main__":
    login_and_get_ids()
