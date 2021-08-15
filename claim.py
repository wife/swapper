import ast
import json
import logging
import os
import random
import sys
import time

import requests

from steamapi import SteamCommunity
from threading import Thread
from functools import wraps

def run_async(func):
	@wraps(func)
	def async_func(*args, **kwargs):
		func_hl = Thread(target = func, args = args, kwargs = kwargs)
		func_hl.start()
		return func_hl

	return async_func

logging.basicConfig(level=getattr(logging, "INFO"), 
                    format="%(msecs)03d MS - %(message)s", 
                    datefmt="%H:%M:%S %p")
log = logging.getLogger(__name__)


USER_AGENT = "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Mobile Safari/537.36"


USERNAME = input("Steam Username (account releasing /id/): ")
PASSWORD = input("Steam Password (account releasing /id/): ")
release_account = SteamCommunity(username=USERNAME, password=PASSWORD, user_agent=USER_AGENT)

print("\n")

CLAIM_ACCOUNT_USERNAME = input("Steam Username (account claiming /id/): ")
CLAIM_ACCOUNT_PASSWORD = input("Steam Password (account claiming /id/): ")
claim_account = SteamCommunity(username=CLAIM_ACCOUNT_USERNAME, password=CLAIM_ACCOUNT_PASSWORD, user_agent=USER_AGENT)

vanity_url = release_account.vanity_url
release_id_url = f"https://steamcommunity.com/profiles/{release_account.steamid64}/edit?sessionID={release_account.sessionid}&type=profileSave&customURL="
claim_id_url = f"https://steamcommunity.com/profiles/{claim_account.steamid64}/edit?sessionID={claim_account.sessionid}&type=profileSave&customURL={vanity_url}"

log.info(f"The Vanity URL that will be swapped is /id/{vanity_url} from {release_account.steamid64} to {claim_account.steamid64}")

confirmation = input("Confirm (y/n): ")
if confirmation.lower().startswith("y"):
    log.info("Swapping in 3 seconds...")
else:
    log.info("Exiting script...")
    quit()

for i in range(3, 0, -1):
    print(str(i) + "...", end="\r")
    time.sleep(1)

grabbed = False
@run_async
def func1(sleep):
    global grabbed
    time.sleep(sleep)
    log.info(f"Attempting to claim {vanity_url} - {sleep} sleep version")
    if f"/id/{vanity_url}" in claim_account._session.get(claim_id_url).text:
        if grabbed is False:
            grabbed = True
            log.info(f"{sleep} sleep version grabbed it!")

func1(sleep=0.700)
func1(sleep=0.540)
func1(sleep=0.480)
func1(sleep=0.430)
func1(sleep=0.375)
func1(sleep=0.325)
func1(sleep=0.275)
func1(sleep=0.220)
func1(sleep=0.175)
func1(sleep=0.125)

log.info(f"Releasing /id/{vanity_url}")
release_account._session.get(release_id_url)
log.info(f"Released /id/{vanity_url}")
if claim_account.vanity_url == vanity_url:
    log.info(f"Successfully swapped /id/{vanity_url} from {release_account.steamid64} to {claim_account.steamid64}")
else:
    log.info(f"Failed to swap /id/{vanity_url}")
quit()