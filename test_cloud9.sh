#!/bin/bash

./parse_physics.py pcal week
./parse_glirc.py pcal week
./parse_nycruns.py pcal week
./print_todays_agenda.py
./list_drive_files.py list 10
