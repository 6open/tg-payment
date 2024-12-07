#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import time
from quart import Quart, jsonify, request
from services.bot import *
from services.payment import *
from services.config import BOT_TOKEN

app = Quart(__name__)  # 将Flask改为Quart

API_TOKEN = BOT_TOKEN
WEBHOOK_HOST = '8fc4-129-150-53-117.ngrok-free.app'
WEBHOOK_PORT = 443
WEBHOOK_LISTEN = '0.0.0.0'
WEBHOOK_URL_BASE = f"https://{WEBHOOK_HOST}"
WEBHOOK_URL_PATH = f"/{API_TOKEN}/"
WEBHOOK_SSL_CERT = './cfg/webhook_cert.pem'
WEBHOOK_SSL_PRIV = './cfg/webhook_pkey.pem'
DOMAIN = '1.2.3.4'

logger = telebot.logger
telebot.logger.setLevel(logging.INFO)

@app.route('/', methods=['GET', 'HEAD'])
async def index():
    return ''

@app.route('/get_url/ton', methods=['POST'])
async def process_get_url_transaction():
    response = await get_transaction_url()  # 异步调用
    return response

@app.route('/send_invoice/star', methods=['POST'])
async def process_send_invoice_star():
    request_data = await request.get_json()
    response = payment_star(request_data)  # 异步调用
    return response

@bot.pre_checkout_query_handler(func=lambda query: True)
def handle_pre_checkout_query(pre_checkout_query):
    bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot.message_handler(content_types=['successful_payment'])
async def handle_successful_payment(message):
    bot.send_message(message.chat.id, "✅ Payment accepted, please wait for the eSIM card. It will arrive soon!")
    return await successful_payment_callback(message.successful_payment)

    
@app.route(WEBHOOK_URL_PATH, methods=['POST'])
async def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = await request.get_data()  # Quart的异步方式获取数据
        update = telebot.types.Update.de_json(json_string.decode('utf-8'))
        bot.process_new_updates([update])
        return ''
    else:
        return ('Forbidden', 403)

@bot.message_handler(commands=['help', 'start'])
def send_welcome(message):
    bot.reply_to(message, "Hi there, I am EchoBot. I am here to echo your kind words back to you.")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def echo_message(message):
    bot.reply_to(message, message.text)

# Remove webhook, it fails sometimes the set if there is a previous webhook
bot.remove_webhook()
time.sleep(0.1)

# Set webhook
# bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH,certificate=open(WEBHOOK_SSL_CERT, 'r'))
bot.set_webhook(url=WEBHOOK_URL_BASE + WEBHOOK_URL_PATH)

# Start Quart server
# app.run(host=WEBHOOK_LISTEN,
#         port=WEBHOOK_PORT,
#         ssl_context=(WEBHOOK_SSL_CERT, WEBHOOK_SSL_PRIV),
#         debug=True)

app.run(host=WEBHOOK_LISTEN, port=WEBHOOK_PORT, ssl_context=None, debug=True)