#!/bin/bash

./make_queue.py list head
./parse_glirc.py pcal week
./parse_physics.py pcal week
./print_todays_agenda.py
./launch_ec2_instance.py list
./get_from_s3.py list
./list_drive_files.py list 10
./system_stats.py
