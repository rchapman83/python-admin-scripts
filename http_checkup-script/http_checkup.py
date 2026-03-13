from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from datetime import datetime

def get_website_status_urllib(url):
    req = Request(url)
    try:
        with urlopen(req) as response:
            return f"Website is working fine. Status code: {response.getcode()}"
    except HTTPError as e:
        return f"The server couldn't fulfill the request. Error code: {e.code}"
    except URLError as e:
        return f"We failed to reach a server. Reason: {e.reason}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"


# Text/CLI based menu 
menu_options = {
	1: "Check single website",
	2: "Cloudflare exported list check",
	0: "Exit",
}

def print_menu():
    for key in menu_options.keys():
        print (key, "--", menu_options[key] )

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
            url_to_check = input("Enter the URL of the website to check:\n")            
            if not url_to_check.startswith(('http://', 'https://')):
                url_to_check = 'https://' + url_to_check            
            result = get_website_status_urllib(url_to_check)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open('output.log', 'a') as f:
                f.write(f"{timestamp}: {url_to_check} >>> {result}\n")
            print("Check completed. Results logged to output.log")
        elif option == 2:
            file_to_load = input("Enter the path to the file containing URLs to check:\n")
            exit()
        elif option == 0:
            print("Exiting...")
            exit()
else:
   print("Invalid selection. Please enter a number between 0 and 2.")