#!/bin/bash
source venv/bin/activate
python3 tennis.py --input_date 04/27/2023 --input_interval 60 --input_time_range 7:00am 9:00am --pb_token $1 # --debug
