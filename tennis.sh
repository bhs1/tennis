#!/bin/bash
source ~/Projects/tennis/venv/bin/activate
python3 ~/Projects/tennis/tennis.py --input_date 06/24/2024 --input_interval 60 --input_time_range 12:00am 11:00pm  --activity_filter "Pickleball / Mini Tennis" --debug
deactivate
