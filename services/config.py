'''
This module get information from blockchain using toncenter api
'''
import requests
import json
import time

MAINNET_API_BASE = "https://toncenter.com/api/v2/"
TESTNET_API_BASE = "https://testnet.toncenter.com/api/v2/"
MAINNET_API_TOKEN = "ec798fd69d0dadf0dd65918a2554c2f0b605d7b6f5a71d0ef72f0070998872b8"
TESTNET_API_TOKEN = "690c5524c629b065ca3943fc6ef778bb2d8bddecc9f1436cf74e48c312ad84b9"
BOT_TOKEN = "7446702342:AAEC7OeD4LoOCbhVLwrQ9XdyhtUeii_vzi8"
TESTNET_WALLET =  "0QBAyTa4m1ZEDHhfZOHc1EpNOXf5ZQIsUrCSdpGhjkGG3jWO"
MAINNET_WALLET = "UQBAyTa4m1ZEDHhfZOHc1EpNOXf5ZQIsUrCSdpGhjkGG3o4E"
CHAT_ID =  "5887326921"
WORK_MODE =  "testnet"


if WORK_MODE == "mainnet":
    API_BASE = MAINNET_API_BASE
    API_TOKEN = MAINNET_API_TOKEN
    WALLET = MAINNET_WALLET
else:
    API_BASE = TESTNET_API_BASE
    API_TOKEN = TESTNET_API_TOKEN
    WALLET = TESTNET_WALLET