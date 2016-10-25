#!/bin/bash

nosetests `find . -iname '*.py'`
./parse_physics.py pcal week
./parse_nycruns.py pcal week
./parse_hashnyc.py pcal week
./print_todays_agenda.py
