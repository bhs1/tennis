#!/bin/bash
python3 ~/projects/tennis/tennis.py --input_date 09/20/2023 --input_interval 60 --input_time_range 7:00am 11:00pm --api_token "$1" --user_token "$2" --activity_filter "Tennis" --debug
