from requests import get
import time
import os
import re
import logging

import config

def get_ip(url):
    res = get(url)
    ip_match = re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', res.text)

    if ip_match == None:
        logging.error(f"Cannot match valid IP address from response of {url}")
        raise Exception(f"Cannot match valid IP address from response of {url}")
    else:
        ip = re.search(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", res.text).group(0)
        logging.debug(f"IP {ip} from {url} getting successfully")
    
    return ip


def update_ip(host, domain, password, wan_ip):
    try:
        res = get(f'https://dynamicdns.park-your-domain.com/update?host={host}&domain={domain}&password={password}&ip={wan_ip}')
        
        error = re.search(r'(?:(?:<ResponseString>)(.+)(?:<\/ResponseString>))', res.text)
        if error:
            error = error[1]

    except Exception as e:
        error = e

    if error:
        logging.error(f"Error updating: {host}.{domain}: {error}")
    else:
        logging.info(f"IP {wan_ip} for {host}.{domain} updated successfully")


logging.info("Starting Script")

# CHECK FOR MISSING VARS
missing_vars = config.required_vars - set(os.environ.keys())
if missing_vars:
    logging.critical(f"Missing environ: <{', '.join(missing_vars)}>")
    exit()

# CHECK FOR MIS MATCHED DATA
hosts = os.environ['APP_HOST'].split(';')
domains = os.environ['APP_DOMAIN'].split(';')
passwords = os.environ['APP_PASSWORD'].split(';')
getting_ip_url = os.environ['APP_GETTING_IP_URL']
if not (len(hosts) == len(domains) == len(passwords)):
    logging.error("Mismatched inputs. You must supply the same number of hosts, domains, and passwords.")
    exit()
targets = list(zip(hosts, domains, passwords))


# DEFAULT WANIP 
wan_ip = "0.0.0.0"

while True:

    try:
        new_wan_ip = get_ip(getting_ip_url)

    except Exception as e:
        logging.error(e)
        time.sleep(float(os.getenv('APP_UPDATE_TIME') or 60))
        continue
    
    if new_wan_ip != wan_ip:

        logging.info(f"IP change to {new_wan_ip}")

        for i in targets:
            try:
                update_ip(
                    host=i[0],
                    domain=i[1],
                    password=i[2],
                    wan_ip=new_wan_ip,
                )
                
                wan_ip = new_wan_ip
        
            except Exception as e:
                logging.error(e)

    time.sleep(float(os.getenv('APP_UPDATE_TIME') or 60))
