#/bin/bash

curl -k -X POST https://localhost:443/show/ton \
     -H "Content-Type: application/json" \
     -d '{
     "item": "Ton Product", 
     "description": "Test payment for toncoin product", 
     "value": 0.5e9,
     "user_id": 5887326921,
     "comment": "test3",
     "user_address" : "0QC900YNBw5cuGstLzLQdnuFmORR7zYsrZk2UUXM3Qo5PbH9"
     }'

