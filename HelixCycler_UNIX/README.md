## HelixCycler
An easy to use python application to run the OT thermocycler independently from an Opentrons Robot.

<img src="https://github.com/helixworks-technologies/HelixCycler/blob/main/HelixCycler.png" width=90% height=85%>





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


## Run a protocol
## See google sheet for an example input.  
https://docs.google.com/spreadsheets/d/1APvXpImfQ8JtOwSfbmaLQZdP6SYDe2T5pF8ugUPLfnM/edit?usp=sharing  

Make a copy of this sheet for yourself and create your own thermocycling protocol.  
*Note sheet must be converted to .csv format to run on the application.

## Notes on csv protocol.
### CYCLES
Always start each stage of a protocol with a CYCLES in the first column and asign the number of cycles in the next column.  
If you do not wish to cycle the following steps, set it to 1.  
A new stage of events occurs everytime CYCLES is called in the first column.  

### STEP
STEP is assigns plate temperature targets, incubation time and lid temperature target. You can place STEP after STEP and they will repeat sequentially until all cycles are completed.  
I don't recommend dynamically updating lid temp throughout the protocol as it is slow and can't actively cool. I recommend presetting the lid temp at the beginning. Once the lid temp has been set/preset you can leave the field blank in the csv and it will hold until DEACTIVATE_ALL is called.  

### DEACTIVATE_ALL
At the end of your protocol if you do not call this the thermocycler will hold  at the final STEP parameters set after completing the protocol. If you wish to switch off the plate and lid call this.  
(This is recommended to be placed just before END&GRAPH. If placed before another STEP the protocol will call it and continue to the next step without the deactivate having any impact.)

### END&GRAPH
END&GRAPH will end the protocol and draw up the graph of temperature throughout the run. Sometimes it may appear behind the app window.

# Setting the serial port


Use the find_serial.py script to get a print out of the ports. Then set the serial_port value in the tc_send_code.py file as the port value given for the Opentrons Thermocycler. 
  
  
On Windows it is formatted as COM(port number).  
On Linux or Mac it may look more like a path /dev/ttyACM(number).  






