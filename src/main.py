#!/usr/bin/env python3

import sys
import time
from configuration import getConfig
from requests import Session

if __name__ == '__main__':
    s = Session()
    
    if sys.version_info < (3, 10):
        raise Exception("This script requires Python 3.10+")   

    CONF = getConfig()
    if not CONF:
        raise Exception(f'Failed to setup configuraion.')
    
    while True:
        r = s.get('https://ipv4.icanhazip.com', timeout=10)
        
        ip = r.text.strip()
        
        print(f'Fetched IP: {ip}')
        
        time.sleep(30)
        