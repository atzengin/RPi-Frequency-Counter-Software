#!/bin/bash

# Enable I/O

if [ ! -e /sys/class/gpio/gpio22 ]; then
	echo 22 > /sys/class/gpio/export
	echo 23 > /sys/class/gpio/export
	echo 24 > /sys/class/gpio/export
	echo 25 > /sys/class/gpio/export
	echo 4 > /sys/class/gpio/export
	echo 5 > /sys/class/gpio/export
	echo 6 > /sys/class/gpio/export
	echo 13 > /sys/class/gpio/export
	echo 19 > /sys/class/gpio/export
	echo 20 > /sys/class/gpio/export
	echo 12 > /sys/class/gpio/export
fi

exec python3 delta_thread.py
