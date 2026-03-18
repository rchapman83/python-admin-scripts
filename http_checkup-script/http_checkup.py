from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse
from datetime import datetime
import ssl
import socket
import hashlib
import csv
import time
import concurrent.futures

LOG_FILE = 'output.log'
BULK_OUTPUT_FILE = 'output.csv'
CUSTOM_USER_AGENT = 'python-http-checkup/1.0'
OTHER_PORTS = [8080, 8443, 22, 25, 587]
# Port scan timeout in seconds
PORT_SCAN_TIMEOUT = 1
# To avoid overwhelming servers, we can limit the number of requests per second.
MAX_REQUESTS_PER_SECOND = 5 
REQUEST_INTERVAL = 1.0 / MAX_REQUESTS_PER_SECOND

def get_website_status(url):
    req = Request(url, headers={'User-Agent': CUSTOM_USER_AGENT})
    try:
        with urlopen(req) as response:
            status_code = response.getcode()
            final_url = response.geturl()
            if final_url != url:
                return f"Website redirected from {url} to {final_url}. Status code: {status_code}"
            return f"Website is working fine. Status code: {status_code}"
    except HTTPError as e:
        if e.code in (301, 302, 303, 307, 308):
            location = e.headers.get('Location', 'unknown') if hasattr(e, 'headers') else 'unknown'
            return f"Redirect detected {e.code} -> {location}."
        return f"The server couldn't fulfill the request. Error code: {e.code}"
    except URLError as e:
        return f"We failed to reach a server. Reason: {e.reason}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"

def get_website_fingerprint(url):
    parsed = urlparse(url)
    if not parsed.scheme:
        url = 'https://' + url
        parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port or 443

    if not host:
        message = f"Invalid URL: {url}"
        print(message)
        return None

    context = ssl.create_default_context()
    try:
        with socket.create_connection((host, port), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=host) as ssock:
                der_cert = ssock.getpeercert(binary_form=True)
                sha256 = hashlib.sha256(der_cert).hexdigest().upper()
                fingerprint = ':'.join(sha256[i:i+2] for i in range(0, len(sha256), 2))
                cert = ssock.getpeercert()
                subject = cert.get('subject', ())
                issuer = cert.get('issuer', ())
                message = (
                    f"SSL/TLS fingerprint for {url}: {fingerprint}. "
                    f"Subject: {subject}. Issuer: {issuer}."
                )
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                with open(LOG_FILE, 'a') as f:
                    f.write(f"{timestamp}: {message}\n")
                return fingerprint
    except Exception as e:
        message = f"Error getting fingerprint for {url}: {e}"
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(LOG_FILE, 'a') as f:
            f.write(f"{timestamp}: {message}\n")
        print(message)
        return None

def is_port_open(host, port, timeout=PORT_SCAN_TIMEOUT):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        result = sock.connect_ex((host, port))
        return result == 0
    except Exception:
        return False
    finally:
        sock.close()

def scan_ports(host, ports, timeout=PORT_SCAN_TIMEOUT):
    open_ports = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(ports), 10)) as executor:
        futures = {executor.submit(is_port_open, host, port, timeout): port for port in ports}
        for future in concurrent.futures.as_completed(futures):
            port = futures[future]
            try:
                if future.result():
                    open_ports.append(port)
            except Exception:
                pass
    return sorted(open_ports)


def process_zone_file(file_path):
    try:
        with open(file_path, 'r') as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"File {file_path} not found.")
        return
    total_lines = len(lines)
    processed = 0
    skipped = 0
    with open(BULK_OUTPUT_FILE, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        for idx, line in enumerate(lines, start=1):
            print(f"Processing {idx}/{total_lines} lines...", end='\r', flush=True)
            line = line.strip()
            if not line or line.startswith(';') or line.startswith('#'):
                skipped += 1
                continue
            fields = line.split()
            if len(fields) < 3:
                skipped += 1
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
                # Skip irrelevant records that are not real web hosts
                irrelevant_prefixes = (
                    '_domainkey',
                    'autodiscover',
                    '_validation',
                    '_dnstest',
                    '_spf',
                )
                normalized = domain.lstrip('.').lower()
                # Split the domain into labels and reject records where any label begins with an irrelevant prefix.
                # This avoids matching portions of longer labels incorrectly via startswith at the full domain level,
                # and ensures e.g. "foo._domainkey.example.com" is filtered out as intended.
                labels = normalized.split('.')
                if any(any(label.startswith(prefix) for prefix in irrelevant_prefixes) for label in labels):
                    continue
                if not domain.startswith(('http://', 'https://')):
                    domain = 'https://' + domain
                # Perform the check directly
                req = Request(domain, headers={'User-Agent': CUSTOM_USER_AGENT})
                try:
                    with urlopen(req) as response:
                        status_code = response.getcode()
                        final_url = response.geturl()
                        if final_url != domain:
                            message = f"Redirected from {domain} to {final_url}."
                            status = str(status_code)
                        else:
                            message = "Website is working fine."
                            status = str(status_code)
                except HTTPError as e:
                    if e.code in (301, 302, 303, 307, 308):
                        location = e.headers.get('Location', 'unknown') if hasattr(e, 'headers') else 'unknown'
                        message = f"Redirect detected {e.code} -> {location}."
                        status = str(e.code)
                    else:
                        message = "The server couldn't fulfill the request."
                        status = str(e.code)
                except URLError as e:
                    parsed_url = urlparse(domain)
                    host = parsed_url.hostname
                    if host:
                        port80_open = is_port_open(host, 80)
                        port443_open = is_port_open(host, 443)
                        if not port80_open and not port443_open:
                            open_ports = scan_ports(host, OTHER_PORTS)
                            if open_ports:
                                port_list = ' '.join(str(p) for p in open_ports)
                                message = (
                                    f"Main ports 80/443 are closed; other open ports: {port_list}."
                                    " Domain may still be in use on non-web services."
                                )
                                status = 'other-ports-open'
                            else:
                                message = (
                                    "No common service ports are open 80 443 8080 8443 22 25 587."
                                    " Candidate stale domain."
                                )
                                status = 'stale-candidate'
                        else:
                            message = "Failed to reach HTTP/S but 80/443 TCP appears open."
                            status = 'tcp-available'
                    else:
                        message = "We failed to reach a server."
                        status = ''
                except Exception as e:
                    parsed_url = urlparse(domain)
                    host = parsed_url.hostname
                    if host is not None and not is_port_open(host, 80) and not is_port_open(host, 443):
                        message = "Unexpected error and 80/443 closed; candidate stale domain."
                        status = 'stale-candidate'
                    else:
                        message = "An unexpected error occurred."
                        status = ''
                writer.writerow([domain, message, status])
                processed += 1
                time.sleep(REQUEST_INTERVAL)

    print(f"Zone file processing complete: {processed} records processed, {skipped} lines skipped (out of {total_lines} lines). ")

# Text/CLI based menu 
menu_options = {
	1: "HTTP check single website",
	2: "HTTP check bulk [Cloudflare zone file]",
    3: "SSL/TLS fingerprint single website",
    4: "Jarm check single website",
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
            result = get_website_status(url_to_check)
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open(LOG_FILE, 'a') as f:
                f.write(f"{timestamp}: {url_to_check} >>> {result}\n")
            print("Check completed. Results logged to "+LOG_FILE)
        elif option == 2:
            file_to_load = input("Enter the path to the file containing URLs to check:\n")
            process_zone_file(file_to_load)
            print("Zone file processed. Results appended to "+BULK_OUTPUT_FILE)
        elif option == 3:
            url_to_check = input("Enter the URL of the website for fingerprint check:\n")
            if not url_to_check.startswith(('http://', 'https://')):
                url_to_check = 'https://' + url_to_check
            fingerprint = get_website_fingerprint(url_to_check)
            if fingerprint:
                print(f"Fingerprint recorded: {fingerprint} (also appended to {LOG_FILE})")
            else:
                print(f"Failed to retrieve fingerprint for {url_to_check}. See {LOG_FILE} for details.")
        elif option == 4:
            print("Jarm check single website - Not implemented yet.")
        elif option == 0:
            print("Exiting...")
            exit()
else:
   print("Invalid selection. Please enter a number between 0 and 4.")