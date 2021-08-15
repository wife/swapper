import base64
import logging
import random
import sys
import time

from bs4 import BeautifulSoup
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
import requests


log = logging.getLogger(__name__)


class SteamCommunity(object):
    """A custom wrapper around the Steamcommunity website
    Includes base functions for various types of Steam autoclaimers
    """

    def __init__(self, username: str, password: str, user_agent: str = None) -> None:
        """Constructs a Steam account instance

        username - The username of the Steam account
        password - The password of the Steam account
        user_agent - (optional) User Agent of the application
        """
        self._session = requests.Session()
        if user_agent is None:
            user_agent = "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/537.12 (KHTML, like Gecko) Chrome/62.0.3754.85 Safari/537.48"
        self._session.headers["User-Agent"] = user_agent
        self._sessionid = ""
        self._steamid64 = ""
        self.login(username, password)
        self._username = username
        self._password = password


    @property
    def sessionid(self) -> str:
        """Get the Session ID of the account instance"""
        return self._sessionid


    @property
    def steamid64(self) -> str:
        """Get the SteamID64 of the account instance"""
        return self._steamid64


    @property
    def vanity_url(self) -> str:
        """Get the Vanity URL of the account instance"""
        return self._session.get("https://steamcommunity.com/my/edit").url.split("/")[-2].lower()


    def encrypt_password(self, username: str, password: str) -> bytes:
        """Fetch RSA key data to encrypt password
        :return: Base64-encoded encrypted password
        """
        rsa_data = self._session.post("https://steamcommunity.com/login/getrsakey/", 
                                     data=dict(username=username, donotcache=time.time()*1000)).json()
        mod = int(rsa_data["publickey_mod"], 16)
        exp = int(rsa_data["publickey_exp"], 16)
        rsa = RSA.construct((mod, exp))
        cipher = PKCS1_v1_5.new(rsa)
        return base64.b64encode(cipher.encrypt(password.encode("utf-8"))), rsa_data["timestamp"]


    def login(self, username: str, password: str, emailauth="", emailsteamid="", 
                captchagid="-1", captcha_text="", twofactorcode="") -> requests.Session():
        """Log into Steamcommunity"""
        encrypted_password, rsatimestamp = self.encrypt_password(username, password)

        login_payload = {
            "username": username,
            "password": encrypted_password,
            "rsatimestamp": rsatimestamp,
            "remember_login": True,
            "captchagid": captchagid,
            "captcha_text": captcha_text,
            "emailauth": emailauth,
            "emailsteamid": emailsteamid,
            "twofactorcode": twofactorcode,
            "donotcache": time.time()*1000
        }

        resp = self._session.post("https://steamcommunity.com/login/dologin/", data=login_payload).json()

        if not resp["success"]:
            if resp.get("captcha_needed"):
                log.error(resp["message"])
                captcha_url = "https://steamcommunity.com/public/captcha.php?gid=" + resp["captcha_gid"]
                log.info(captcha_url)
                captcha_text = input("Enter the Captcha Text: ")
            elif resp.get("requires_twofactor"):
                log.info("2FA authentication required. Please enter the auth code.\n")
                twofactorcode = input("Auth Code: ")
            elif resp.get("emailauth_needed"):
                log.info("Please enter the auth code sent to your " + resp["emaildomain"] + " email.\n")
                emailauth = input("Auth Code: ")                
            else:
                if resp["message"] == "The account name or password that you have entered is incorrect.":
                    log.info(resp["message"] + " Please try again.")
                    username = input("Steam Username: ")
                    password = input("Steam Password: ")
                else:
                    raise Exception(resp)

            return self.login(username, password,
                              emailauth=emailauth,
                              emailsteamid = resp.get("emailsteamid"),
                              captcha_text=captcha_text,
                              captchagid=captchagid,
                              twofactorcode=twofactorcode)

        elif not resp["login_complete"]:
            raise Exception(resp)    
        
        self._session.get("https://steamcommunity.com/my/edit")
        self._sessionid = self._session.cookies["sessionid"]
        if len(self._sessionid) != 24:
            raise Exception("Malformed SessionID")

        self._steamid64 = resp["transfer_parameters"]["steamid"]
        if len(self._steamid64) != 17 or not self._steamid64.isdigit():
            raise Exception("Malformed SteamID64")
        
        return log.info(f"Logged in as {username} - SteamID64: {self._steamid64} - Session ID: {self._sessionid}")