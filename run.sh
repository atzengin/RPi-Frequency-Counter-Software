#!/bin/bash

# Enable I/O

#if [ ! -e /sys/class/gpio/gpio22 ]; then
#	echo 17 > /sys/class/gpio/export # Pin 11 BCM 17 Wiring 0
#	echo 18 > /sys/class/gpio/export # Pin 12 BCM 18 Wiring 1
#	echo 27 > /sys/class/gpio/export # Pin 13 BCM 27 Wiring 2
#	echo 22 > /sys/class/gpio/export # Pin 15 BCM 22 Wiring 3
#	echo 23 > /sys/class/gpio/export # Pin 16 BCM 23 Wiring 4
#	echo 24 > /sys/class/gpio/export # Pin 18 BCM 24 Wiring 5
#	echo 25 > /sys/class/gpio/export # Pin 22 BCM 25 Wiring 6
#	echo  4 > /sys/class/gpio/export # Pin  7 BCM  4 Wiring 7
#
#	echo 5 > /sys/class/gpio/export  # Pin 29 BCM  5 Wiring 21  GAL
#	echo 6 > /sys/class/gpio/export  # Pin 31 BCM  6 Wiring 22  GAU
#	echo 13 > /sys/class/gpio/export # Pin 33 BCM 13 Wiring 23  GBL
#	echo 19 > /sys/class/gpio/export # Pin 35 BCM 19 Wiring 24  GBU
#
#	echo 20 > /sys/class/gpio/export # Pin 38 BCM 20 Wiring 28  CLR
#	echo 26 > /sys/class/gpio/export # Pin 37 BCM 26 Wiring 25  RCLK
#	echo 12 > /sys/class/gpio/export # Pin 32 BCM 12 Wiring 26  A Relay
#	echo 16 > /sys/class/gpio/export # Pin 36 BCM 16 Wiring 27  B Relay
#
#	echo 2 > /sys/class/gpio/export  # Pin  3 BCM  2 Wiring  8
#	echo 3 > /sys/class/gpio/export  # Pin  5 BCM  3 Wiring  9
#	echo 8 > /sys/class/gpio/export  # Pin 24 BCM  8 Wiring 10
#	echo 7 > /sys/class/gpio/export  # Pin 26 BCM  7 Wiring 11
#	echo 10 > /sys/class/gpio/export # Pin 19 BCM 10 Wiring 12
#	echo 9 > /sys/class/gpio/export  # Pin 21 BCM  9 Wiring 13
#	echo 11 > /sys/class/gpio/export # Pin 23 BCM 11 Wiring 14
#	echo 14 > /sys/class/gpio/export # Pin  8 BCM 14 Wiring 15
#
#
#fi

exec python3 delta_thread.py
