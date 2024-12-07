'''
This module get information from blockchain using toncenter api
'''
import requests
import json
import time
import services.mydb as mydb
from .config import *
from .bot import *
from aiogram.types import CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from . import mydb
from pytoniq_core import Address
import datetime


def detect_address(address):
    '''
    Detect address
    '''

    url = f"{API_BASE}detectAddress?address={address}&api_key={API_TOKEN}"
    print("url : ", url)
    r = requests.get(url)
    response = json.loads(r.text)
    try:
        return response['result']['bounceable']['b64url']
    except:
        return False


def get_address_information(address):
    '''
    Get information about address
    '''

    url = f"{API_BASE}getAddressInformation?address={address}&api_key={API_TOKEN}"
    r = requests.get(url)
    response = json.loads(r.text)
    return response


def get_address_transactions():
    '''
    Get transactions for address
    '''

    url = f"{API_BASE}getTransactions?address={WALLET}&limit=10&archival=true&api_key={API_TOKEN}"
    r = requests.get(url)

    if r.status_code != 200:
        raise Exception(f"Error fetching transactions: {r.status_code} - {r.text}")

    response = r.json()

    if 'result' not in response:
        raise Exception("Unexpected response format: 'result' not found")

    return response['result']


def compare_address(addr1, addr2):
    try:
        if len(addr1) != 48 and len(addr1) != 64: 
            return False 
        if len(addr2) != 48 and len(addr2) != 64:
            return False 
        if Address(addr1).to_str(is_user_friendly=False) == Address(addr2).to_str(is_user_friendly=False) :
            print("lktest same")
            return True
        else:
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def find_transaction(user_wallet, value, comment):
    '''
    Find transaction by user wallet, value and comment
    '''
    transactions = get_address_transactions()
    for transaction in transactions:
        msg = transaction['in_msg']

        if compare_address(msg['source'] , user_wallet) and int(msg['value']) == value and msg['message'] == comment:
            t = mydb.check_transaction(msg['body_hash'])
            if t == False:
                mydb.add_v_transaction(msg['source'], msg['body_hash'], msg['value'], msg['message'])
                print("find transaction")
                print(
                    f"transaction from: {msg['source']} \nValue: {msg['value']} \nComment: {msg['message']}")
                return True
            else:
                print("该交易已记录")
                pass
    return False


async def check_transaction1(call: CallbackQuery, state: FSMContext):
    print("lktest trans")
    user_data = await state.get_data()
    source = user_data['wallet']
    value = user_data['value_nano']
    comment = user_data['air_type']
    result = find_transaction(source, value, comment)
    if result == False:
        await call.answer("Wait a bit, try again in 10 seconds. You can also check the status of the transaction through the explorer (ton.sh/)", show_alert=True)
    else:
        mydb.v_wallet(call.from_user.id, source)
        await call.message.edit_text("Transaction is confirmed \n/start to restart")
        await state.finish()

def get_latest_block_time():
    # 获取主链最新块的基本信息
    url = "https://toncenter.com/api/v2/getMasterchainInfo"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        latest_seqno = data['result']['last']['seqno']
        
        # 通过块的 seqno 获取详细时间戳
        block_header_url = f"https://toncenter.com/api/v2/getBlockHeader?seqno={latest_seqno}&workchain=-1&shard=-9223372036854775808"
        block_response = requests.get(block_header_url)
        
        if block_response.status_code == 200:
            block_data = block_response.json()
            block_time = block_data['result'].get('gen_utime')
            return block_time
    return None