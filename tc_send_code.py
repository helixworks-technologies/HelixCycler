import serial
import serial.tools.list_ports
import time
import sys

class HardwareController:
    """
    Manages the low-level serial communication with the Opentrons hardware.
    """
    COMMANDS = {
        'open_lid': "M126",
        'close_lid': "M127",
        "get_lid_status": "M119",
        "set_lid_temp": "M140",
        "get_lid_temp": "M141",
        "edit_pid_params": "M301",
        "set_plate_temp": "M104",
        "get_plate_temp": "M105",
        "set_ramp_rate": "M566",
        "deactivate_all": "M18",
        "deactivate_heating": "M106",
        "set_shake_speed": "M3",
        "get_shake_speed": "M123",
        "deactivate_shake": "G28",
        'open_latch': 'M242',
        'close_latch': 'M243',
        "deactivate_lid": "M108",
        "deactivate_block": "M14",
        "device_info": "M115",
        "enter_programming": "dfu",
        "enter_debug_mode": "M111",
        "exit_debug": "M111 S0"
    }

    def __init__(self):
        self.port = None

    def connect(self, port_name):
        """
        Connects to the specified serial port.
        Returns True on success, False on failure.
        """
        try:
            self.port = serial.Serial(port_name, baudrate=115200, timeout=2, write_timeout=2)
            return True
        except serial.SerialException as e:
            print(f"Error connecting to {port_name}: {e}")
            self.port = None
            return False

    def disconnect(self):
        """Closes the serial port connection."""
        if self.port and self.port.is_open:
            self.port.close()
            self.port = None
            print("Disconnected.")

    def _command(self, com, extra=''):
        """Sends a command to the device."""
        if not self.port or not self.port.is_open:
            print("Error: Not connected.")
            return
        string = f"\r\n{self.COMMANDS[com]}{extra}\r\n"
        self.port.write(str.encode(string))

    def _response(self):
        """Reads a response from the device."""
        if not self.port or not self.port.is_open:
            return ""
        string = str(self.port.readline().decode('utf-8'))
        return string

    @staticmethod
    def get_available_ports():
        """
        Returns a list of available serial port device names.
        This is a static method so it can be called before connecting.
        """
        ports = serial.tools.list_ports.comports()
        if not ports:
            return ["No Ports Found"]
        return [port.device for port in ports]

    # --- Public Hardware Commands ---

    def open_lid(self):
        self._command('open_lid')

    def close_lid(self):
        self._command('close_lid')

    def get_lid_temperature(self):
        self._command('get_lid_temp')
        port_readline = self._response()
        temp_received = False
        while not temp_received:
            try:
                if port_readline.startswith('T') and ' H:' not in port_readline:
                    current_temp = port_readline.split('C:', 1)[1]
                    lid_temp = float(current_temp)
                    temp_received = True
                    self.port.reset_input_buffer()
                else:
                    port_readline = self._response()
                    if not port_readline:
                        raise serial.SerialException("Device read failed (lid temp).")
            except (IndexError, ValueError, TypeError):
                self._command('get_lid_temp') 
                port_readline = self._response()
                if not port_readline:
                    raise serial.SerialException("Device read failed (lid temp retry).")
                continue 
        return lid_temp

    def get_plate_info(self):
        self._command('get_plate_temp')
        port_readline = self._response()
        temp_received = False
        while not temp_received:
            try:
                if port_readline.startswith('T') and ' H:' in port_readline:
                    current_temp = port_readline.split('C:', 1)[1].split(' H:', 1)[0]
                    seconds_left = port_readline.split('H:', 1)[1].split('\r', 1)[0]
                    plate_temp = float(current_temp)
                    temp_received = True
                    self.port.reset_input_buffer()
                else:
                    port_readline = self._response()
                    if not port_readline:
                        raise serial.SerialException("Device read failed (plate info).")
            except (IndexError, ValueError, TypeError):
                self._command('get_plate_temp')
                port_readline = self._response()
                if not port_readline:
                    raise serial.SerialException("Device read failed (plate info retry).")
                continue 
        return [plate_temp, seconds_left]

    def set_lid_temperature(self, temp):
        self._command('set_lid_temp', ' S' + str(temp))

    def set_plate_temperature(self, target, time_val=None, well_vol=None):
        temp_string = ' S' + str(target)
        time_string = f' H{time_val}' if time_val is not None else ''
        vol_string = f' V{well_vol}' if well_vol is not None else ''
        self._command("set_plate_temp", temp_string + time_string + vol_string)

    def deactivate_shaker(self):
        self._command('deactivate_shake')
        self._command('deactivate_heating')

    def set_shake_speed(self, target):
        self._command("set_shake_speed", ' S' + str(target))

    def open_latch(self):
        self._command('open_latch')

    def close_latch(self):
        self._command('close_latch')

    def deactivate_all(self):
        self._command('deactivate_all')

    def deactivate_plate(self):
        self._command('deactivate_block')

    def deactivate_lid(self):
        self._command('deactivate_lid')