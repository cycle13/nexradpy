#!/usr/bin/env python3

#import requests
from urllib.request import urlopen
import json
import time
from datetime import datetime

## see: https://github.com/akrherz/iem/blob/master/scripts/asos/iem_scraper_example.py
## globals
MAX_ATTEMPTS = 6
BASE_URL = "http://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?"
STATES = """AK AL AR AZ CA CO CT DE FL GA HI IA ID IL IN KS KY LA MA MD ME
 MI MN MO MS MT NC ND NE NH NJ NM NV NY OH OK OR PA RI SC SD TN TX UT VA VT
 WA WI WV WY""".replace("\n", "").replace("\t", "").split(" ")

def get_stations_from_networks(state_list):
    """
    takes list of states (state abbrev. strings, e.g., "VA")
    returns list of stations?
    """
    stations = []
    networks = [f"{state}_ASOS" for state in state_list]
       
    print(networks)

    ## IEM has Iowa AWOS sites in own labeled network
    if "IA" in state_list:
        networks.append("AWOS")
    
    for network in networks:
        # get metadata
        print("Getting site IDs for ", network)
        uri = f"https://mesonet.agron.iastate.edu/geojson/network/{network}.geojson"
        data = urlopen(uri)
        jdict = json.load(data)
        
        for site in jdict["features"]:
            stations.append(site["properties"]["sid"])

    return stations


if __name__ == "__main__":
    print(get_stations_from_networks(STATES))
