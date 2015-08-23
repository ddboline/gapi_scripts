#!/bin/bash

nosetests3 `find . -iname '*.py'`
python3 ./parse_physics.py pcal week
python3 ./parse_nycruns.py pcal week
python3 ./print_todays_agenda.py
python3 ./list_drive_files.py list 10
