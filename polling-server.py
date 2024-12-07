# app.py
from flask import Flask, jsonify, request, session
from services.payment import *
from services.bot import bot
from aiogram import Dispatcher, types
from hypercorn.asyncio import serve
from hypercorn.config import Config
from aiogram import Router
import asyncio
import signal
import sys
from aiogram.utils.keyboard import InlineKeyboardBuilder
from pytonconnect import TonConnect
from aiogram.filters import CommandStart, Command



app = Flask(__name__)
my_router = Router(name=__name__)

# 创建全局事件循环
loop = asyncio.get_event_loop()

g_user_data = {}

# 创建 Dispatcher 实例
dp = Dispatcher()
dp['bot'] = bot
dp.include_router(my_router)

@app.route('/payment/star', methods=['POST'])
def process_payment_star():
    # 在全局事件循环中运行异步任务
    task = asyncio.run_coroutine_threadsafe(payment_star(), loop)
    return task.result()

@app.route('/send_invoice/star', methods=['POST'])
def process_send_invoice_star():
    # 在全局事件循环中运行异步任务
    task = asyncio.run_coroutine_threadsafe(payment_star(), loop)
    return task.result()


@app.route('/get_url/ton', methods=['POST'])
def process_get_url_transaction():

    task = asyncio.run_coroutine_threadsafe(get_transaction_url(), loop)
    return task.result()

@app.route('/show/ton', methods=['POST'])
def show_payment_ton():
    user_address = request.json.get('user_address')
    user_id = request.json.get('user_id')
    value = request.json.get('value')
    value = int(value)
    comment = request.json.get('comment')
    g_user_data[user_id] = {
        "user_address" : user_address,
        "value" : value,
        'comment' : comment,
    }
    task = asyncio.run_coroutine_threadsafe(payment_ton(), loop)
    return task.result()

@dp.message(CommandStart())
async def command_start_handler(message: Message):
    chat_id = message.chat.id

    mk_b = InlineKeyboardBuilder()
    wallets_list = TonConnect.get_wallets()
    
    # 只展示特定的钱包
    specific_wallets = ['Wallet', 'Tonkeeper']
    # specific_wallets = [
    #     'Wallet', 'Tonkeeper', 'MyTonWallet', 'Tonhub', 
    #     'DeWallet', 'Bitget Wallet', 'SafePal', 
    #     'OKX Wallet', 'OKX TR Wallet', 'HOT', 
    #     'Bybit Wallet', 'GateWallet', 'Binance Web3 Wallet', 
    #     'Fintopio'
    # ]
    
    for wallet in wallets_list:
        if wallet['name'] in specific_wallets:  # 过滤条件
            mk_b.button(text=wallet['name'], callback_data=f'connect:{wallet["name"]}')
    
    mk_b.adjust(1)
    await message.answer(text='Choose wallet to connect', reply_markup=mk_b.as_markup())


async def shutdown():
    print("Shutting down gracefully...")
    sys.exit(0)

def signal_handler(signal, frame):
    loop.create_task(shutdown())  # 使用协程处理关机逻辑
    print("Signal received, shutting down...")

def start_command():
    pass


@my_router.message()
async def start_message_handler(message: types.Message):
    if message.text == '/start':
        #print("message: ", message)
        await message.answer(f"欢迎 {message.from_user.id}，这是 lukas 用于支付的测试 bot。")


@my_router.message()
async def successful_payment_handler(message: types.Message):
    if message.content_type == types.ContentType.PRE_CHECKOUT:
        # 处理成功支付的逻辑
        await message.answer("支付成功！感谢您的支持。")

@my_router.message()
async def successful_payment_handler(message: types.Message):
    if message.content_type == types.ContentType.SUCCESSFUL_PAYMENT:
        # 处理成功支付的逻辑
        await message.answer("支付成功！感谢您的支持。")

@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True,
                                  error_message="Aliens tried to steal your card's CVV, but we successfully protected your credentials,"
                                                " try to pay again in a few minutes, we need a small rest.")


@bot.message_handler(content_types=['successful_payment'])
def got_payment(message):
    bot.send_message(message.chat.id,
                     'Hoooooray! Thanks for payment! We will proceed your order for `{} {}` as fast as possible! '
                     'Stay in touch.\n\nUse /buy again to get a Time Machine for your friend!'.format(
                         message.successful_payment.total_amount / 100, message.successful_payment.currency),
                     parse_mode='Markdown')


async def start_services():
    bot_task = asyncio.create_task(bot.infinity_polling(skip_pending=True))
    config = Config()
    config.bind = ["0.0.0.0:7601"]
    flask_task = serve(app, config)

    await asyncio.gather(bot_task, flask_task)

if __name__ == "__main__":
    asyncio.run(start_services())

