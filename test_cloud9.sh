#!/bin/bash

py.test `find . -iname '*.py' ! -path './send_to_gtalk.py' ! -path './hangups_common.py'`
./parse_physics.py pcal week
./parse_nycruns.py pcal week
./parse_hashnyc.py pcal week
./print_todays_agenda.py
