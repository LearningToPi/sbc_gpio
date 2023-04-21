#!/bin/bash -x

## RX
sudo lircd --driver=default --device=/dev/lirc$1 --output=/var/run/lirc/lircd$1 --pidfile=/var/run/lirc/lircd$1.pid

## TX
sudo lircd --driver=default --device=/dev/lirc$2 --output=/var/run/lirc/lircd$2 --pidfile=/var/run/lirc/lircd$2.pid
