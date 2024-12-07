#/bin/bash

curl -k -X POST https://localhost:443/send_invoice/star \
     -H "Content-Type: application/json" \
     -d '{
          "user_id" : "111",
          "chat_id" : 5887326921,
          "title": "eSIM card", 
          "description": "Test payment for Star product", 
          "price": 888,
          "payload": "test_star",
          "callback_url": "http://127.0.0.1:7611/callback/pay-server"
     }'
