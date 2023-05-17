import requests
import hmac
import hashlib
import json
import os

from base64 import b64encode, b64decode
from datetime import datetime

ENDPOINT = "https://api.detectify.com/rest"
api_key = os.getenv("DETFY_KEY")
api_secret_key = os.getenv("DETFY_SECRET_KEY")

menu_options = {
	1: "Get Scan Profiles",
	2: "Get Scan Status",
	3: "Start Scan",
	4: "Exit",
}

def print_menu():
    for key in menu_options.keys():
        print (key, "--", menu_options[key] )

def send_post_request(data: dict or None, path: str, url: str) -> dict or None:
    timestamp = str(int(datetime.now().timestamp()))

    if data:
        headers = make_headers("POST", path, timestamp, json.dumps(data))
        req = requests.post(url, headers=headers, data=json.dumps(data))
    else:
        headers = make_headers("POST", path, timestamp, None)
        req = requests.post(url, headers=headers, data=None)

    try:
        req.raise_for_status()
    except Exception as e:
        print(e)
        return None

    #print(f"Status code: {req.status_code} | Raw response: {req.json()}")
    return req.json()

def make_get_request(data: dict or None, path: str, url: str) -> dict or None:
    timestamp = str(int(datetime.now().timestamp()))

    if data:
        headers = make_headers("GET", path, timestamp, json.dumps(data))
        req = requests.get(url, headers=headers, data=json.dumps(data))
    else:
        headers = make_headers("GET", path, timestamp, None)
        req = requests.get(url, headers=headers, data=None)

    try:
        req.raise_for_status()
    except Exception as e:
        print(e)
        return None

    #print(f"Status code: {req.status_code} | Raw response: {req.json()}")
    return req.json()

def make_headers(method: str, path: str, timestamp: str, body: str = None):
    method = method.upper()
    signature = make_signature(method, path, timestamp, body)
    return {
        "X-Detectify-Key": api_key,
        "X-Detectify-Signature": signature,
        "X-Detectify-Timestamp": timestamp,
    }

def make_signature(method: str, path: str, timestamp: str, body: str = None):
    msg = f"{method};{path};{api_key};{timestamp};"
    if body:
        msg += f"{body}"

    secret = b64decode(api_secret_key)
    signature = hmac.new(
        secret, msg=bytes(msg, "utf=8"), digestmod=hashlib.sha256
    ).digest()

    b64_sig = b64encode(signature)
    return b64_sig.decode("utf-8")

def start_scan():
    sp_token = input("Please enter scan profile token:\n")
    path = f"/v2/scans/{sp_token}/"
    url = f"{ENDPOINT}{path}"
    resp = send_post_request(None, path, url)
    if resp is not None:
        print(resp)

def get_scan_profile():
  path = f"/v2/profiles/"
  url = f"{ENDPOINT}{path}"
  resp = make_get_request(None, path, url)
  if resp is not None:
    print(resp)

def get_scan_status():
  sp_token = input("Please enter scan profile token:\n")
  path = f"/v2/scans/{sp_token}/"
  url = f"{ENDPOINT}{path}"
  resp = make_get_request(None, path, url)
  if resp is not None:
    print(resp)

if __name__ == "__main__":
	print("Starting ...\nPlease make a selection \n")
	while(True):
		print_menu()
		option = ""
		try:
			option = int(input("Select option: "))
		except:
			print("Invalid input, numeric input only.")
		if option == 1:
			get_scan_profile()
		elif option == 2:
			get_scan_status()
		elif option == 3:
			start_scan()
		elif option == 4:
			print("Exiting...")
			exit()
		else:
			print("Invalid selection. Please enter a number between 1 and 4.")
