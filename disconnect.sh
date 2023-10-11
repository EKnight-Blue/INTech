#! /bin/bash

coproc bluetoothctl
echo -e 'disconnect A4:53:85:8C:A3:87\nexit' >&${COPROC[1]}