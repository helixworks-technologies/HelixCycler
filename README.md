# HelixCycler
An easy to use python application to run the OT thermocycler independently from an Opentrons Robot.


See google sheet for an example input.
https://docs.google.com/spreadsheets/d/1APvXpImfQ8JtOwSfbmaLQZdP6SYDe2T5pF8ugUPLfnM/edit?usp=sharing
Make a copy of this sheet for yourself and create your own thermocycling protocol.
*Note sheet must be converted to .csv format to run on the application.

Written and tested in python 3.7.

Prerequisites:
tkinter
csv
threading
pyserial
time
matplotlib

edit the variable 'serial_port' in tc_send_code.py to match the port your port
before running.


