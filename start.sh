#! /bin/bash

cd "$(dirname "$0")"
source ./venv/bin/activate
echo -e "load loic\nshow\nexit" | python3 shell.py
python3 ps_controll.py