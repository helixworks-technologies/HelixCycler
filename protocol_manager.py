import time
import matplotlib.pyplot as plt
import csv
import sys
import datetime

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

def incubation(controller, lid_label, plate_label, time_label, start_time, graph, plate_temp, inc_time=None, lid_temp=None, well_vol=None, update_sec=0.1):
    """Manages a single incubation step and updates GUI labels."""
    if lid_temp is not None:
        controller.set_lid_temperature(lid_temp)

    if inc_time is not None:
        time_remaining = inc_time
        controller.set_plate_temperature(plate_temp, inc_time, well_vol)
        try:
            while float(time_remaining) > 0.001:
                current_time = (time.time() - start_time) / 60
                current_lid_temp = controller.get_lid_temperature()
                plate_info = controller.get_plate_info()
                current_plate_temp, time_remaining = plate_info[0], plate_info[1]

                lid_label.configure(text=f'{current_lid_temp} °C')
                plate_label.configure(text=f'{current_plate_temp} °C')
                time_label.configure(text=f'{time_remaining} secs')

                graph[current_time] = [current_lid_temp, current_plate_temp, inc_time]
                time.sleep(update_sec)
        except (ValueError, TypeError):
            print('Protocol stopped or device disconnected.')
            # Allow thread to exit
            return
    else:
        # This is a 'hold' step
        controller.set_plate_temperature(plate_temp)
        try:
            while True: # Will be interrupted when the thread is stopped
                current_lid_temp = controller.get_lid_temperature()
                plate_info = controller.get_plate_info()
                current_plate_temp, time_remaining = plate_info[0], plate_info[1]

                lid_label.configure(text=f'{current_lid_temp} °C')
                plate_label.configure(text=f'{current_plate_temp} °C')
                time_label.configure(text=f'{time_remaining} secs')
                time.sleep(update_sec)
        except (ValueError, TypeError):
            print('Protocol stopped or device disconnected.')
            return

def run_protocol(controller, prot_dict, step_label, lid_temp_label, plate_temp_label, step_time_label, experiment_title, update_sec=0.1):
    """Runs the full protocol, step by step."""
    if not controller or not controller.port:
        print("Error: Controller not connected.")
        step_label.configure(text="Error: Not Connected")
        return

    temp_graph = {}
    strt_time = time.time()
    
    try:
        for stage in prot_dict:
            cycles = prot_dict[stage][0]
            for i in range(cycles):
                for step_counter in range(1, len(prot_dict[stage])):
                    step_label.configure(text=f'Stage\t\tCycle\t\tStep\n{stage}\t\t{i+1}\t\t{step_counter}', font=("Roboto Medium", -18))
                    print(f'Stage-{stage}\t\tCycle-{i+1}\t\tStep-{step_counter}')
                    step = (prot_dict[stage][step_counter])

                    if step[0] == 'DEACTIVATE_ALL':
                        controller.deactivate_all()
                    elif step[0] == 'END&GRAPH':
                        create_graph(temp_graph, experiment_title)
                        # Hold at last temp
                        incubation(controller, lid_temp_label, plate_temp_label, step_time_label, strt_time, temp_graph, 
                                   plate_temp=temp_graph[max(temp_graph.keys())][1], # Get last plate temp
                                   update_sec=update_sec) 
                    else:
                        incubation(controller, lid_temp_label, plate_temp_label, step_time_label, strt_time, temp_graph, 
                                   plate_temp=step[0], inc_time=step[1], lid_temp=step[2], update_sec=update_sec)
    except Exception as e:
        print(f"Protocol error or manually stopped: {e}")
    finally:
        print("Protocol finished or stopped.")