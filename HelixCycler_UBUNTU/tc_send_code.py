import os
import sys
import time
import csv
import datetime
import serial
from serial.tools import list_ports

# ---- Headless-friendly Matplotlib setup ----
HEADLESS = (sys.platform.startswith("linux") and not os.environ.get("DISPLAY"))
if HEADLESS:
    import matplotlib
    matplotlib.use("Agg")
import matplotlib.pyplot as plt


# ---- Serial port auto-detection (override with env var) ----
def detect_serial_port() -> str | None:
    # Highest priority: explicit override
    env_port = os.environ.get("HC_SERIAL_PORT")
    if env_port:
        return env_port

    ports = list(list_ports.comports())
    candidates = []

    for p in ports:
        dev = p.device
        # Linux
        if sys.platform.startswith("linux"):
            if dev.startswith("/dev/ttyACM") or dev.startswith("/dev/ttyUSB"):
                candidates.append(dev)
        # macOS
        elif sys.platform == "darwin":
            if dev.startswith("/dev/cu.usb") or dev.startswith("/dev/tty.usb"):
                candidates.append(dev)
        # Windows
        elif os.name == "nt":
            if dev.upper().startswith("COM"):
                candidates.append(dev)

    if candidates:
        return candidates[0]

    # If we saw any ports at all, just take the first as a very last resort
    if ports:
        return ports[0].device

    return None


serial_port = detect_serial_port() or "/dev/ttyACM0"   # good default on Ubuntu

try:
    port = serial.Serial(serial_port, baudrate=115200, timeout=40)
except Exception as e:
    raise RuntimeError(
        f"Could not open serial port '{serial_port}'. "
        "Set HC_SERIAL_PORT=/dev/ttyACM0 (or your device) and try again. "
        f"Original error: {e}"
    )

update_sec = 0.05

commands = {
    'open_lid': "\r\nM126",
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
    port.write(string.encode('utf-8'))


def response():
    return port.readline().decode('utf-8', errors='ignore')


def open_lid():
    command('open_lid')


def close_lid():
    command('close_lid')


def get_lid_temperature():
    command('get_lid_temp')
    port_readline = response()
    while True:
        try:
            if port_readline and port_readline[0] == 'T' and ' H:' not in port_readline:
                current_temp = port_readline.split('C:', 1)[1]
                lid_temp = float(current_temp)
                port.reset_input_buffer()
                return lid_temp
            else:
                port_readline = response()
        except (IndexError, ValueError):
            command('get_lid_temp')
            port_readline = response()
            continue


def get_plate_info():
    command('get_plate_temp')
    port_readline = response()
    while True:
        try:
            if port_readline and port_readline[0] == 'T' and ' H:' in port_readline:
                current_temp = port_readline.split('C:', 1)[1].split(' H:', 1)[0]
                seconds_left = port_readline.split('H:', 1)[1].split('\r', 1)[0]
                plate_temp = float(current_temp)
                port.reset_input_buffer()
                return [plate_temp, seconds_left]
            else:
                port_readline = response()
        except (IndexError, ValueError):
            command('get_plate_temp')
            port_readline = response()
            continue


def set_lid_temperature(temp, wait=False):
    command('set_lid_temp', ' S' + str(temp))
    if not wait:
        return

    lid_temp = get_lid_temperature()
    target = float(temp)
    if lid_temp > target:
        print(f"Lid is too hot. Current: {lid_temp}\tTarget: {target}")

    while lid_temp < target * 0.995:
        time.sleep(update_sec)
        lid_temp = get_lid_temperature()

    print(f'Lid temperature achieved: {lid_temp}')


def set_plate_temperature(target, time=None, well_vol=None):
    temp_string = ' S' + str(target)
    time_string = (' H' + str(time)) if time is not None else ''
    vol_string = (' V' + str(well_vol)) if well_vol is not None else ''
    command("set_plate_temp", temp_string + time_string + vol_string)


def deactivate_shaker():
    command('deactivate_shake')
    command('deactivate_heating')


def set_shake_speed(target):
    command("set_shake_speed", ' S' + target)


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
    x, y = [], []
    for key in dictionary.keys():
        y.append(key)
        x.append(dictionary[key][ind])
    plt.plot(y, x, label=line_name)


def create_graph(graph, title):
    plot_line(graph, 1, 'Block_temp')
    plot_line(graph, 0, 'Lid_temp')

    plt.title(title + f' - {datetime.datetime.now().replace(second=0, microsecond=0)}')
    plt.ylabel('Temperature - °C')
    plt.xlabel('Time - minutes')
    plt.ylim(-20, 120)
    plt.legend()

    if HEADLESS:
        # Save to file when no display is available
        out = f"{title.replace(' ', '_')}_{int(time.time())}.png"
        plt.savefig(out, dpi=150, bbox_inches="tight")
        print(f"[HEADLESS] Saved graph to {out}")
        plt.close()
    else:
        plt.show()
        try:
            wm = plt.get_current_fig_manager()
            wm.window.attributes('-topmost', 1)
            wm.window.attributes('-topmost', 0)
        except Exception:
            pass


def incubation(lid_label, plate_label, time_label, start_time, graph,
               plate_temp, inc_time=None, lid_temp=None, well_vol=None):
    if lid_temp is not None:
        set_lid_temperature(lid_temp, True)

    if inc_time is not None:
        time_remaining = inc_time
        set_plate_temperature(plate_temp, inc_time, well_vol)
        try:
            while float(time_remaining) > 0.001:
                current_time = (time.time() - start_time) / 60
                lid_t = get_lid_temperature()
                plate_t, time_remaining = get_plate_info()

                lid_label.configure(text=f"{lid_t} °C")
                plate_label.configure(text=f"{plate_t} °C")
                time_label.configure(text=f"{time_remaining} secs")

                graph[current_time] = [lid_t, plate_t, inc_time]
                time.sleep(update_sec)
        except ValueError:
            print('Deactivated Thermocycler')
            sys.exit()
    else:
        set_plate_temperature(plate_temp)
        while True:
            lid_t = get_lid_temperature()
            plate_t, time_remaining = get_plate_info()

            lid_label.configure(text=f"{lid_t} °C")
            plate_label.configure(text=f"{plate_t} °C")
            time_label.configure(text=f"{time_remaining} secs")
            time.sleep(update_sec)


def protocol_dict(infile):
    protocol = {}
    with open(infile, 'r', newline='') as f:
        csv_file = csv.reader(f, delimiter=',')
        stage_count = 0
        for line in csv_file:
            if line[0] == 'CYCLES':
                stage_count += 1
                protocol[stage_count] = [int(line[1])]
            elif line[0] == 'STEP':
                inc_params = []
                inc_params.append(float(line[2]))                   # plate temp
                inc_params.append(float(line[3]) if line[3] else None)   # time
                inc_params.append(float(line[4]) if line[4] else None)   # lid temp
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
                # NOTE: CustomTkinter v5 → use font= (positive size)
                step_label.configure(
                    text=f"Stage\t\tCycle\t\tStep\n{stage}\t\t{i+1}\t\t{step_counter}",
                    font=("Roboto Medium", 18)
                )
                print(f"Stage-{stage}\t\tCycle-{i+1}\t\tStep-{step_counter}")
                step = prot_dict[stage][step_counter]

                if step[0] == 'DEACTIVATE_ALL':
                    deactivate_all()

                elif step[0] == 'END&GRAPH':
                    create_graph(temp_graph, experiment_title)
                    while True:
                        lid_t = get_lid_temperature()
                        plate_t, time_remaining = get_plate_info()

                        lid_temp_label.configure(text=f"{lid_t} °C")
                        plate_temp_label.configure(text=f"{plate_t} °C")
                        step_time_label.configure(text=f"{time_remaining} secs")
                        time.sleep(update_sec)

                else:
                    incubation(
                        lid_temp_label, plate_temp_label, step_time_label,
                        strt_time, temp_graph, step[0], step[1], step[2]
                    )
