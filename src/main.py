#!/usr/bin/env python3

import sys
import time
from configuration import getConfig
from requests import Session
from datetime import datetime




def main():
    s = Session()
    if sys.version_info < (3, 10):
        raise Exception("This script requires Python 3.10+")   

    CONF = getConfig()
    if not CONF:
        sys.stderr.write(f'Failed to setup configuration.\n')
        sys.exit(1)
    
    print(f'API TOKEN: {CONF["accounts"][0]["authentication"].get("api_token","")}')
    
    while True:
        r = s.get('https://ipv4.icanhazip.com', timeout=10)
        
        ip = r.text.strip()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f'[{timestamp}] - Fetched IP: {ip}')
        
        time.sleep(CONF.get("interval",120))
        


if __name__ == '__main__':
    main()
