#! /bin/bash

source ./venv/bin/activate
echo -e "load loic\nshow\exit" | python3 shell.py
python3 ps_controll.py