#/bin/bash

curl -k  -X POST http://localhost:443/get_url/ton \
     -H "Content-Type: application/json" \
     -d '{
     "user_id": "1234",
     "wallet_type": "Tonkeeper",
     "target_address": "0QC900YNBw5cuGstLzLQdnuFmORR7zYsrZk2UUXM3Qo5PbH9",
     "amount": 1e8,
     "callback_url": "http://127.0.0.1:7611/callback/pay-server"
     }'

