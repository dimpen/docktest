import os
import sys
from pathlib import Path
from string import Template
import json5
from jsonschema import validate
from schema import SCHEMA


DEFAULTS = {
    "updater": {
        "priority": ["1111", "1001"],
        "A": True,
        "AAAA": False,
        "ttl": 300,
        "blacklist": None,
        "onlyOnChange": False,
        "tmpIpFile": "./tmpip.txt",
        "requestTimeout": 20,
    },
    "logging": {
        "stdout": {"level": "DEBUG"},
        "logfile": {
            "level": "INFO",
            "filename": "./cloudflare-ddns.log",
            "max_bytes": 5*1024*1024, # 5MB
            "max_count": 1,
            "format": "text"
        },
        "iplog": {
            "filename": "./cloudflare-ddns-ip.log", 
            "max_bytes": 1*1024, # 100KB
            "max_count": 1,
            "onlyIpChange": True,
            "format": "text"
        }
    },
}


_CONF = None

def getConfig():
    global _CONF
    if _CONF is None:
        setup_config()
    return _CONF


def setup_config():
    global _CONF
    config_file = None
    config = None
    cnf = {}
    try:      
        if len(sys.argv) > 1:
            if len(sys.argv)> 2 and sys.argv[1] == "--config" and sys.argv[2]:
                config_path = Path(sys.argv[2]) 
                if config_path.is_file() and os.access(config_path, os.R_OK):
                    config_file = sys.argv[2]
                else:
                    raise Exception(f'Cannot read config file {sys.argv[2]}')
                    # return None
            else:
                raise Exception(f'Usage: {sys.argv[0]} --config <config_filename>\n')
                # return None

        if not config_file: 
            config_file = os.path.join(os.environ.get('CONFIG_PATH', os.getcwd()), "config-example.json")
        # Read in all environment variables that have the correct prefix
        env_vars = {key: value for (key, value) in os.environ.items() if key.startswith('CF_DDNS_')}

    
        with open(config_file) as cfile:
            if len(env_vars) != 0:
                config = json5.loads(Template(cfile.read()).safe_substitute(env_vars))
            else:
                config = json5.loads(cfile.read())

        if not config:
            raise Exception(f'Cannot read configuration from: {config_file}') 

        try:
            validate(instance=config, schema=SCHEMA)
        except Exception as e:
            raise Exception(f'Error validating config: {e}')
        
        cnf.update({**DEFAULTS["updater"], **config.get("updater",{})})                                

        if cnf.get("consensus"):
            majority = max(int(len(cnf.get("consensus"))/2)+1, cnf.get("majority",0))
            majority = min(majority, len(cnf.get("consensus")))
            cnf.update({"majority": majority})
        
        if config.get("logging"):
            # iterate all the expected keys
            for k in DEFAULTS["logging"].keys():
                # if a matching key is provided in the config
                if config["logging"].get(k) is not None:
                    # transfer the provided values to the defaults and add them to cnf
                    cnf.update({k: {**DEFAULTS["logging"].get(k), **config["logging"].get(k)}})
        else:
            # if "logging" isn't provided go with the default
            cnf.update({"stdout": DEFAULTS["logging"]["stdout"]})   
        
        # create filepaths for all files that are in the config 
        for fp in [cnf.get("tmpIpFile"), cnf.get("logfile",{}).get("filename"), cnf.get("iplog",{}).get("filename")]:
            if fp:
                try:
                    Path(fp).parent.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    raise Exception(f'Cannot create path for: {fp}\n Error: {e}') 
        
        
        cnf["accounts"]=config.get("accounts")
        for account in cnf["accounts"]:
            for zone in account.get("zones"):
                zone.update({"purgeUnknownRecords": zone.get("purgeUnknownRecords", False)})
                # set global settings if they're missing from individual records
                for subdomain in zone.get("subdomains"):
                    cnf.update({subdomain.get("type"): True})
                    
                    subd_ttl = subdomain.get("ttl", cnf["ttl"])
                    if subd_ttl != 1 and subd_ttl < 30: subd_ttl = 30
                    subdomain.update({"ttl": subd_ttl})
        
        _CONF=cnf   

    except Exception as e:
        sys.stderr.write(f'Configuration Error:\n {e} \nCheck config-example.json for correct configuration. https://www.example.com')
        _CONF=None

