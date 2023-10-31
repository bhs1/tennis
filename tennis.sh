#!/bin/bash
python3 -m venv ~/projects/tennis/tennis_env
source ~/projects/tennis/tennis_env/bin/activate
python3 ~/projects/tennis/tennis.py --input_date 11/07/2023 --input_interval 60 --input_time_range 7:00pm 11:00pm --api_token "$1" --user_token "$2" --activity_filter "Tennis" #--debug
deactivate
