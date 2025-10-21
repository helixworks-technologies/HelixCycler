import time
import matplotlib.pyplot as plt
import csv
import sys
import datetime
import serial # <-- IMPORT ADDED
import threading # <-- IMPORT ADDED

def protocol_dict(infile_path):
    """Parses a CSV protocol file into a dictionary."""
    protocol = {}
    with open(infile_path, 'r') as infile:
        csv_file = csv.reader(infile, delimiter=',')
        stage_count = 0
        for line in csv_file:
            if line[0] == 'CYCLES':
                stage_count += 1
                protocol[stage_count] = [int(line[1])]
            elif line[0] == 'STEP':
                inc_params = []
                # add plate temp
                inc_params.append(float(line[2]))
                # add incubation time
                if len(line[3]) > 0:
                    inc_params.append(float(line[3]))
                else:
                    inc_params.append(None)
                # add lid temp
                if len(line[4]) > 0:
                    inc_params.append(float(line[4]))
                else:
                    inc_params.append(None)
                # add step to current stage
                protocol[stage_count].append(inc_params)
            elif line[0] == 'DEACTIVATE_ALL':
                protocol[stage_count].append(['DEACTIVATE_ALL'])
            elif line[0] == 'END&GRAPH':
                protocol[stage_count].append(['END&GRAPH'])
    return protocol

def plot_line(dictionary, ind, line_name):
    x = []
    y = []
    for key in dictionary.keys():
        y.append(key)
        x.append(dictionary[key][ind])
    plt.plot(y, x, label=line_name)

def create_graph(graph, title):
    """Creates and displays the temperature graph."""
    plot_line(graph, 1, 'Block_temp')
    plot_line(graph, 0, 'Lid_temp')

    plt.title(title + f' - {datetime.datetime.now().replace(second=0, microsecond=0)}')
    plt.ylabel('Temperature - °C')
    plt.xlabel('Time - minutes')
    plt.ylim(-20, 120)
    plt.legend()
    plt.show()
    wm = plt.get_current_fig_manager()
    if wm:
        # Try to bring window to front
        try:
            wm.window.attributes('-topmost', 1)
            wm.window.attributes('-topmost', 0)
        except Exception:
            pass # Fails on some platforms, but that's ok

# --- UPDATED FUNCTION ---
def incubation(controller, 
               update_lid_fn, update_plate_fn, update_time_fn, # <-- Callback functions
               emergency_stop_event, # <-- New event
               start_time, graph, plate_temp, 
               inc_time=None, lid_temp=None, well_vol=None, update_sec=0.1):
    """Manages a single incubation step and updates GUI labels via callbacks."""
    if lid_temp is not None:
        controller.set_lid_temperature(lid_temp)

    if inc_time is not None:
        time_remaining = inc_time
        controller.set_plate_temperature(plate_temp, inc_time, well_vol)
        try:
            while float(time_remaining) > 0.001:
                # --- Emergency Stop Check ---
                if emergency_stop_event.is_set():
                    raise Exception("Emergency Stop Triggered")

                current_time = (time.time() - start_time) / 60
                current_lid_temp = controller.get_lid_temperature() 
                plate_info = controller.get_plate_info() 
                current_plate_temp, time_remaining = plate_info[0], plate_info[1]

                update_lid_fn(f'{current_lid_temp} °C')
                update_plate_fn(f'{current_plate_temp} °C')
                update_time_fn(f'{time_remaining} secs')

                graph[current_time] = [current_lid_temp, current_plate_temp, inc_time]
                time.sleep(update_sec)
        except serial.SerialException as e:
            # --- This is the "Skip Step" logic ---
            print(f'Step Skipped: SerialException ({e})')
            # Breaking loop skips to the next step
        except (ValueError, TypeError) as e: 
            print(f'Protocol step value error: {e}')
            # This is a real error, so we re-raise it to stop the protocol
            raise
    else:
        # This is a 'hold' step
        controller.set_plate_temperature(plate_temp)
        try:
            while True: 
                # --- Emergency Stop Check ---
                if emergency_stop_event.is_set():
                    raise Exception("Emergency Stop Triggered")
                    
                current_lid_temp = controller.get_lid_temperature() 
                plate_info = controller.get_plate_info() 
                current_plate_temp, time_remaining = plate_info[0], plate_info[1]

                update_lid_fn(f'{current_lid_temp} °C')
                update_plate_fn(f'{current_plate_temp} °C')
                update_time_fn(f'{time_remaining} secs')
                
                time.sleep(update_sec)
        except serial.SerialException as e:
            # --- This is the "Skip Step" logic ---
            print(f'Step Skipped: SerialException ({e})')
            # Breaking loop skips to the next step
        except (ValueError, TypeError) as e: 
            print(f'Protocol hold error: {e}')
            raise 

# --- UPDATED FUNCTION ---
def run_protocol(controller, prot_dict, 
                 update_step_fn, update_lid_fn, update_plate_fn, update_time_fn, # <-- Callbacks
                 emergency_stop_event, # <-- New event
                 experiment_title, update_sec=0.1):
    """Runs the full protocol, step by step."""
    if not controller or not controller.port:
        print("Error: Controller not connected.")
        update_step_fn("Error: Not Connected") 
        return

    temp_graph = {}
    strt_time = time.time()
    
    try:
        for stage in prot_dict:
            # --- Emergency Stop Check ---
            if emergency_stop_event.is_set():
                raise Exception("Emergency Stop Triggered")
                
            cycles = prot_dict[stage][0]
            for i in range(cycles):
                # --- Emergency Stop Check ---
                if emergency_stop_event.is_set():
                    raise Exception("Emergency Stop Triggered")
                    
                for step_counter in range(1, len(prot_dict[stage])):
                    # --- Emergency Stop Check ---
                    if emergency_stop_event.is_set():
                        raise Exception("Emergency Stop Triggered")

                    step_text = f'Stage\t\tCycle\t\tStep\n{stage}\t\t{i+1}\t\t{step_counter}'
                    update_step_fn(step_text)
                    print(f'Stage-{stage}\t\tCycle-{i+1}\t\tStep-{step_counter}')
                    
                    step = (prot_dict[stage][step_counter])

                    if step[0] == 'DEACTIVATE_ALL':
                        controller.deactivate_all()
                    elif step[0] == 'END&GRAPH':
                        create_graph(temp_graph, experiment_title)
                        incubation(controller, 
                                   update_lid_fn, update_plate_fn, update_time_fn, 
                                   emergency_stop_event, # <-- Pass event
                                   strt_time, temp_graph, 
                                   plate_temp=temp_graph[max(temp_graph.keys())][1], 
                                   update_sec=update_sec) 
                    else:
                        incubation(controller, 
                                   update_lid_fn, update_plate_fn, update_time_fn, 
                                   emergency_stop_event, # <-- Pass event
                                   strt_time, temp_graph, 
                                   plate_temp=step[0], inc_time=step[1], lid_temp=step[2], 
                                   update_sec=update_sec)
    except Exception as e:
        # This will now *only* catch the Emergency Stop or real ValueErrors
        print(f"Protocol run stopped: {e}") 
    finally:
        print("Protocol finished or stopped.")