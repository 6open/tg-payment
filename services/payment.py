# services/payment.py
import random
from flask import jsonify, request
from .config import *
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, PreCheckoutQuery
from .bot import *
from .check import *
from aiogram.fsm.state import StatesGroup, State
from pytonconnect import TonConnect
from pytonconnect.exceptions import UserRejectsError
import asyncio
from pytoniq_core.boc import Cell
from datetime import datetime
# from telebot.types import LabeledPrice
from telebot import types
import httpx  # 异步请求库，替换 requests 库
from quart import jsonify, request
import asyncio


ton_user_connections = {}  # 存储每个ton用户的TonConnect实例
star_payload = {} # 存储每个star用户的payload信息

class DataInput(StatesGroup):
    firstState = State()
    secondState = State()
    WalletState = State()
    PayState = State()

async def refunded_payment(message: types.Message):
    payment_info = message.successful_payment
    amount_in_stars = payment_info.total_amount
    currency = payment_info.currency
    transaction_id = payment_info.provider_payment_charge_id

    await message.reply(
        f"*💔 Payment refunded!*\n"  # 修改为退款成功的消息
        f"💲 *Amount:* {amount_in_stars}⭐️\n"
        f"*Currency:* {currency}\n"  # 取消注释以显示货币
        f"🆔 *Transaction ID:* `{transaction_id}`",
        parse_mode='Markdown'
    )

def payment_star(request_data):
    try:
        user_id = request_data.get("user_id")
        chat_id = request_data.get("chat_id")
        title = request_data.get("title")
        description = request_data.get("description")
        payload = request_data.get("payload")
        price = request_data.get("amount")
        prices = [types.LabeledPrice(label="XTR", amount=price)]
        callback_url = request_data.get("callback_url")
        
        if not price or not description:
            return jsonify({"error": "Missing price or description"}), 400

        # bot.send_photo(chat_id, open('cfg/eSIM.png', 'rb'), caption="Check out this item!")
        invoice_result = bot.send_invoice(

            chat_id,

            title=title,

            description=description,

            invoice_payload=payload,

            provider_token="",  # For XTR, this token can be empty

            currency="XTR",

            prices=prices,

        )
        star_payload[payload] = {
            "callback_url": callback_url,
            "amount" : price
        }

        response_data = {
            "user_id": user_id,
            "status": "success",
            "message_id": invoice_result.message_id, 
            "chat_id": invoice_result.chat.id, 
            "amount": invoice_result.invoice.total_amount
        }

        return jsonify(response_data), 200 
    except Exception as e:
        return jsonify({"error": str(e)}), 500

async def successful_payment_callback(successful_payment):
    star_data = star_payload[successful_payment['invoice_payload']]
    callback_url = star_data['callback_url']
    callback_data = {
        "status" : "success",
        "payload": successful_payment['invoice_payload'],
        "amount": successful_payment['total_amount'],
        "telegram_payment_charge_id": successful_payment['telegram_payment_charge_id']
    }

     # 使用httpx发送POST请求
    async with httpx.AsyncClient() as client:
        response = await client.post(callback_url, json=callback_data)  # 异步POST请求

    # 检查并打印响应
    if response.status_code == 200:
        print("Request successful:", response.json())
    else:
        print("Failed with status code:", response.status_code)



async def get_transaction_url():
    try:
        data = await request.get_json()  # 使用 await 以异步方式获取 JSON 数据
        user_id = data.get("user_id")
        amount = data.get('amount')
        wallet_type = data.get('wallet_type')
        target_address = data.get('target_address')
        callback_url = data.get('callback_url')

        # 创建或获取连接
        if user_id not in ton_user_connections:
            ton_user_connections[user_id] = TonConnect(
                manifest_url="https://raw.githubusercontent.com/XaBbl4/pytonconnect/main/pytonconnect-manifest.json"
            )
        connector = ton_user_connections[user_id]
        
        # 获取 URL 并立即返回
        if not await connector.restore_connection():
            await asyncio.sleep(1)
            print("lktest sleep1")
            wallets_list = connector.get_wallets()
            user_wallet = next((w for w in wallets_list if w['name'] == wallet_type), None)
            if not user_wallet:
                raise Exception("指定钱包未找到")
            
            generated_url = await connector.connect(user_wallet)
            
            response_data = {
                "user_id": user_id,
                "status": "success",
                "connect_url": generated_url
            }
            asyncio.create_task(monitor_connection(connector, user_id, target_address, amount, callback_url))
            return jsonify(response_data), 200 
        else:
            return jsonify({"user_id": user_id, "status": "failed", "connect_url": "连接恢复失败"}), 500 
    except Exception as e:
        return jsonify({"user_id": user_id, "error": str(e)}), 500


async def monitor_connection(connector, user_id, address, amount, callback_url):
    """异步后台任务，监听连接和交易状态"""
    print("lktest monitor")
    for _ in range(120):
        print("lktest inrang")
        await asyncio.sleep(1)
        print("lktest sleep2")
        
        if connector.connected and connector.account and connector.account.address:
            print(f"用户 {user_id} 已连接钱包 {connector.account.address}")
            # 更新状态，标记连接成功
            break
    else:
        print(f"用户 {user_id} 连接失败，超时")

    await asyncio.sleep(1)

    transaction = {
        "valid_until": int(datetime.now().timestamp()) + 900,
        "messages": [
            {
                "address": address,
                "amount": amount,
            },
        ],
    }

    print(f"lktest amount, {address}, {amount}")
    try:
        print("Sending transaction...")
        result = await connector.send_transaction(transaction)
        print("Transaction was sent successfully")

    except UserRejectsError:
        raise Exception("You rejected the transaction")

    finally:
        print("Waiting 2 minutes to disconnect...")
        asyncio.create_task(connector.disconnect())
        for _ in range(120):
            await asyncio.sleep(1)
            if not connector.connected:
                print("Disconnected")
                break
        print("App is closed")

    await asyncio.sleep(1)

    msg_hash = Cell.one_from_boc(result["boc"]).hash.hex()
    print(f"Transaction info -> https://toncenter.com/api/v3/transactionsByMessage?direction=out&msg_hash={msg_hash}&limit=128&offset=0")
    print("Done")

    data = {
        "user_id": user_id,
        "target_address": address,
        "amount": amount, 
        "status_code": 200,
        "msg": "transact successful"
    }

    # 使用httpx发送POST请求
    async with httpx.AsyncClient() as client:
        response = await client.post(callback_url, json=data)  # 异步POST请求

    # 检查并打印响应
    if response.status_code == 200:
        print("Request successful:", response.json())
    else:
        print("Failed with status code:", response.status_code)

async def payment_ton():
    try: 
        data = request.json
        price = data.get("value")
        ton_price = float(data.get("value")) * 1e-9  # 将价格乘以10的负九次方
        description = data.get("description")
        item_id = data.get("item_id")

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Check transaction", callback_data="check")]
        ])
        
        keyboard1 = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="callback_test", callback_data="pay_ton")],
            [InlineKeyboardButton(
                    text="Ton Wallet", url=f"ton://transfer/{WALLET}?amount=1000000000&text='test_ton_wallet'")],
            [InlineKeyboardButton(text="Tonkeeper", url=f"https://app.tonkeeper.com/transfer/{WALLET}?amount={price}&text='test'")],
        ])

        keyboard3 = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Check test", callback_data="pay_ton")]
        ])
        

        await bot.send_message(CHAT_ID, f"Send <code>{ton_price}</code> toncoin to address \n<code>{WALLET}</code>  \nfrom your wallet", reply_markup=keyboard1, parse_mode="HTML")
        await bot.send_message(CHAT_ID, "Click the button after payment", reply_markup=keyboard)
        #await bot.send_message(CHAT_ID, "Click the button after payment", reply_markup=keyboard3)

        response_data = {
            "status": "success",
        }

        return jsonify(response_data), 200 
    except Exception as e:
        return jsonify({"error": str(e)}), 500
