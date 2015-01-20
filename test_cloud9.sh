#!/bin/bash

./parse_glirc.py pcal week
./parse_physics.py pcal week
./print_todays_agenda.py
./list_drive_files.py list 10
