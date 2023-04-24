#!/bin/bash
source ~/Documents/tennis/venv/bin/activate
python3 ~/Documents/tennis/tennis.py --input_date 04/30/2023 --input_interval 60 --input_time_range 10:00am 8:00pm --api_token "$1" --user_token "$2" #--debug
