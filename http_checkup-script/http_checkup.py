from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from datetime import datetime
import csv

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


def process_zone_file(file_path):
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return
    with open('output.csv', 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for line in lines:
            line = line.strip()
            if not line or line.startswith(';') or line.startswith('#'):
                continue
            fields = line.split()
            if len(fields) < 3:
                continue
            domain = fields[0].rstrip('.')
            if 'IN' in fields:
                in_index = fields.index('IN')
                if in_index + 1 < len(fields):
                    record_type = fields[in_index + 1]
                else:
                    continue
            else:
                if len(fields) < 2:
                    continue
                record_type = fields[1]
            if record_type in ('A', 'CNAME'):
                if not domain.startswith(('http://', 'https://')):
                    domain = 'https://' + domain
                # Perform the check directly
                req = Request(domain)
                try:
                    with urlopen(req) as response:
                        message = "Website is working fine."
                        status = str(response.getcode())
                except HTTPError as e:
                    message = "The server couldn't fulfill the request."
                    status = str(e.code)
                except URLError as e:
                    message = "We failed to reach a server."
                    status = ''
                except Exception as e:
                    message = "An unexpected error occurred."
                    status = ''
                writer.writerow([domain, message, status])


# Text/CLI based menu 
menu_options = {
	1: "HTTP check single website",
	2: "HTTP check bulk [Cloudflare zone file]",
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
            process_zone_file(file_to_load)
            print("Zone file processed. Results appended to output.csv")
        elif option == 0:
            print("Exiting...")
            exit()
else:
   print("Invalid selection. Please enter a number between 0 and 2.")