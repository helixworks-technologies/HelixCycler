## HelixCycler
An easy to use python application to run the OT thermocycler independently from an Opentrons Robot.


## See google sheet for an example input.  
https://docs.google.com/spreadsheets/d/1APvXpImfQ8JtOwSfbmaLQZdP6SYDe2T5pF8ugUPLfnM/edit?usp=sharing  

Make a copy of this sheet for yourself and create your own thermocycling protocol.  
*Note sheet must be converted to .csv format to run on the application.


# Prerequisites:
Written and tested in python 3.7.

tkinter 
customtkinter  
threading  
csv  
pyserial  
time    
matplotlib  

# Running the Thermocycler

Before running the helixcycler.py app, edit the variable 'serial_port' in tc_send_code.py to match the port your port before running.  

Once connected, all that is required to run a protocol is importing a csv file.  
## Presets
You can stablize the Thermocyclers lid and plate temperature before running an experiment.  
You may deactivate these presets 
### The Lid
Temp range: 37°C - 110°C  

The lid does not have a cooling function, it cools ambiently.  
Setting a lid temperature lower than its current temp will switch it off until it cools to the target.  

If you wish to preheat the lid before running please allow a few minutes before running the starting the protocol for it to reach it's target temperature.


### The Plate
Temp range: 4°C - 99°C 

The plate presets work exactly like the lid temperature presets but faster, i.e. less time needed to stablize before beginning your protocol.






