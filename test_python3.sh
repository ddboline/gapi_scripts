#!/bin/bash

py.test3 `find . -iname '*.py'`
python3 ./parse_physics.py pcal week
python3 ./parse_nycruns.py pcal week
python3 ./parse_hashnyc.py pcal week
python3 ./print_todays_agenda.py
