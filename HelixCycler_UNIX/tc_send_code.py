import serial
import time
import matplotlib.pyplot as plt
import csv
import sys
import datetime


serial_port = "/dev/cu.usbmodem1101"

port = serial.Serial(serial_port, baudrate=115200, timeout=40)
update_sec = 0.05

commands = {'open_lid': "\r\nM126",
            'close_lid': "\r\nM127",
            "get_lid_status": "\r\nM119",
            "set_lid_temp": "\r\nM140",
            "get_lid_temp": "\r\nM141",
            "edit_pid_params": "\r\nM301",
            "set_plate_temp": "\r\nM104",
            "get_plate_temp": "\r\nM105",
            "set_ramp_rate": "\r\nM566",
            "deactivate_all": "\r\nM18",
            "deactivate_heating": "\r\nM106",
            "set_shake_speed": "\r\nM3",
            "get_shake_speed": "\r\nM123",
            "deactivate_shake": "\r\nG28",
            'open_latch': '\r\nM242',
            'close_latch': '\r\nM243',
            "deactivate_lid": "\r\nM108",
            "deactivate_block": "\r\nM14",
            "device_info": "\r\nM115",
            "enter_programming": "\r\ndfu",
            "enter_debug_mode": "\r\nM111",
            "exit_debug": "\r\nM111 S0"
            }



def command(com, extra=''):
    string = commands[com] + extra + '\r\n'
    port.write(str.encode(string))


def response():
    string = str(port.readline().decode('utf-8'))
    return string


def open_lid():
    command('open_lid')
    '''port_readline = response()
    while port_readline != "Lid:open\r\n":
        command('get_lid_status')
        port_readline = response()
        time.sleep(0.1)

    port.reset_output_buffer()
    time.sleep(1)'''


def close_lid():
    command('close_lid')
    '''port_readline = response()
    while port_readline != "Lid:closed\r\n":
        command('get_lid_status')
        port_readline = str(port.readline().decode('utf-8'))
        time.sleep(0.2)
    port.reset_input_buffer()
    port.reset_output_buffer()
    time.sleep(1)'''


def get_lid_temperature():
    # Send gcode for the command
    command('get_lid_temp')
    port_readline = response()
    temp_received = False
    while temp_received == False:

        try:
            if port_readline[0] == 'T' and ' H:' not in port_readline:
                current_temp = port_readline.split('C:', 1)[1]
                lid_temp = float(current_temp)
                temp_received = True
                port.reset_input_buffer()


            else:
                port_readline = response()


        except IndexError:
            command('get_lid_temp')
            port_readline = response()
            continue
    return lid_temp


def get_plate_info():
    # Send gcode for the command
    command('get_plate_temp')
    port_readline = response()
    temp_received = False
    while temp_received == False:

        try:
            if port_readline[0] == 'T' and ' H:' in port_readline:
                #print('Plate temp output', port_readline)
                current_temp = port_readline.split('C:', 1)[1].split(' H:', 1)[0]
                seconds_left =port_readline.split('H:', 1)[1].split('\r', 1)[0]
                #print(current_temp, seconds_left)
                #print(port_readline)
                plate_temp = float(current_temp)
                temp_received = True
                port.reset_input_buffer()


            else:
                port_readline = response()


        except IndexError:
            command('get_plate_temp')
            port_readline = response()
            continue
    return [plate_temp, seconds_left]



# setting lid temperature.
def set_lid_temperature(temp, wait=False):
    command('set_lid_temp', ' S' + str(temp))
    if not wait:
        pass

    else:
        # Get a single lid tem reading
        lid_temp = get_lid_temperature()
        target = float(temp)

        # Warning that lid temp is above target temp and deactivates the lid
        # Fix an option to wait for the lid to reach temp before beginning.
        if lid_temp > target:
            print(f"Lid is too hot. \n\nCurrent: {lid_temp}\tTarget: {target}")
            #command('deactivate_lid')
        print(f'Current: {lid_temp}\tTarget: {target}')

        # Wait until lid temp is almost there
        while lid_temp < target*0.995:
            time.sleep(update_sec)
            print(lid_temp)
            lid_temp = get_lid_temperature()

        print(f'Lid temperature achieved: {lid_temp}')


def set_plate_temperature(target, time=None, well_vol=None):
    temp_string = ' S' + str(target)

    if time != None:
        time_string = ' H' + str(time)
    else:
        time_string = ''
    if well_vol != None:
        vol_string = ' V' + str(well_vol)
    else:
        vol_string = ''
    command("set_plate_temp", temp_string + time_string + vol_string)



def deactivate_shaker():
    command('deactivate_shake')
    command('deactivate_heating')


def set_shake_speed(target):
    command("set_shake_speed", ' S'+target)
    print(target)

def open_latch():
    command('open_latch')


def close_latch():
    command('close_latch')

def deactivate_all():
    command('deactivate_all')


def deactivate_plate():
    command('deactivate_block')

def deactivate_lid():
    command('deactivate_lid')



def plot_line(dictionary, ind, line_name):
    x = []
    y = []
    for key in dictionary.keys():
        y.append(key)
        x.append(dictionary[key][ind])

    plt.plot(y, x, label=line_name)


# plot the graph lines
def create_graph(graph, title):
    plot_line(graph, 1, 'Block_temp')
    plot_line(graph, 0, 'Lid_temp')

    plt.title(title + f' - {datetime.datetime.now().replace(second=0, microsecond=0)}')
    plt.ylabel('Temperature - °C')
    plt.xlabel('Time - minutes')
    plt.ylim(-20, 120)
    plt.legend()
    plt.show()
    wm = plt.get_current_fig_manager()
    wm.window.attributes('-topmost', 1)
    wm.window.attributes('-topmost', 0)




def incubation(lid_label, plate_label, time_label, start_time, graph, plate_temp, inc_time=None, lid_temp=None, well_vol=None):
    # set_lid temp
    if lid_temp != None:
        set_lid_temperature(lid_temp, True)

    # start incubation time with countdown
    if inc_time != None:
        time_remaining = inc_time
        set_plate_temperature(plate_temp, inc_time, well_vol)
        try:
            while float(time_remaining) > 0.001:

                # Fix this to work
                # Add to graph, and wait until timer is done
                current_time = (time.time() - start_time) / 60
                lid_temp = get_lid_temperature()
                inc_temp = get_plate_info()[0]
                time_remaining = get_plate_info()[1]

                lid_label.configure(text=str(lid_temp) + ' °C')
                plate_label.configure(text=str(inc_temp) + ' °C')
                time_label.configure(text=str(time_remaining) + ' secs')


                graph[current_time] = [lid_temp, inc_temp, inc_time]
                time.sleep(update_sec)
        except ValueError:
            print('Deactivated Thermocycler')
            sys.exit()

    else:
        set_plate_temperature(plate_temp)

        while True:
            lid_temp = get_lid_temperature()
            inc_temp = get_plate_info()[0]
            time_remaining = get_plate_info()[1]

            lid_label.configure(text=str(lid_temp) + ' °C')
            plate_label.configure(text=str(inc_temp) + ' °C')
            time_label.configure(text=str(time_remaining) + ' secs')
            time.sleep(update_sec)



def protocol_dict(infile):
    protocol = {}
    with open(infile, 'r') as infile:
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


def run_protocol(prot_dict, step_label, lid_temp_label, plate_temp_label, step_time_label, experiment_title):
    temp_graph = {}
    strt_time = time.time()
    for stage in prot_dict:
        cycles = prot_dict[stage][0]
        for i in range(cycles):
            for step_counter in range(1, len(prot_dict[stage])):
                step_label.configure(text=f'Stage\t\tCycle\t\tStep\n{stage}\t\t{i+1}\t\t{step_counter}', text_font=("Roboto Medium", -18))
                print(f'Stage-{stage}\t\tCycle-{i+1}\t\tStep-{step_counter}')
                step = (prot_dict[stage][step_counter])

                if step[0] == 'DEACTIVATE_ALL':
                    deactivate_all()

                elif step[0] == 'END&GRAPH':
                    create_graph(temp_graph, experiment_title)
                    while True:

                        lid_temp = get_lid_temperature()
                        inc_temp = get_plate_info()[0]
                        time_remaining = get_plate_info()[1]

                        lid_temp_label.configure(text=str(lid_temp) + ' °C')
                        plate_temp_label.configure(text=str(inc_temp) + ' °C')
                        step_time_label.configure(text=str(time_remaining) + ' secs')
                        time.sleep(update_sec)

                else:
                    incubation(lid_temp_label, plate_temp_label, step_time_label, strt_time, temp_graph, step[0],
                               step[1], step[2])
