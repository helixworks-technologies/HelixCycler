from tkinter import filedialog as fd
from tkinter import PhotoImage
import customtkinter
from tc_send_code import HardwareController
from protocol_manager import run_protocol, protocol_dict
import csv
import threading
import pathlib
import sys # <-- Import sys to read command-line arguments

# --- Setup base directory for assets ---
BASE_DIR = pathlib.Path(__file__).parent
IMAGE_PATH = BASE_DIR / 'HelixCycler.png'

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme('blue')


class App(customtkinter.CTk):
    WIDTH = 1200
    HEIGHT = 720

    def __init__(self):
        super().__init__()

        # --- Check for command-line argument (serial port) ---
        self.auto_connect_port = None
        if len(sys.argv) > 1:
            self.auto_connect_port = sys.argv[1]
            print(f"Launched for port: {self.auto_connect_port}")

        # --- Update title if launched for a specific port ---
        window_title = "HelixCycler"
        if self.auto_connect_port:
            window_title = f"HelixCycler - {self.auto_connect_port}"
        self.title(window_title)

        self.geometry(f"{App.WIDTH}x{App.HEIGHT}")
        self.state('zoomed')

        try:
            self.bg = PhotoImage(file=IMAGE_PATH)
        except Exception as e:
            print(f"Could not load background image: {e}")
            self.bg = None

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- App state ---
        self.controller = HardwareController()
        self.protocol_thread = None
        self.emergency_stop_event = threading.Event()
        self.tc_protocol = {}
        self.param_frame_left = None

        self.monitor_thread = None
        self.monitor_stop_event = threading.Event()

        # ============ create frames ============
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=2)

        self.title_frame = customtkinter.CTkFrame(master=self, corner_radius=0)
        self.title_frame.grid(row=0, column=0, sticky="nswe", padx=10, pady=5)

        self.preset_frame = customtkinter.CTkFrame(master=self)
        self.preset_frame.grid(row=1, column=0, sticky="nswe", padx=5, pady=10)

        self.param_frame = customtkinter.CTkFrame(master=self)
        self.param_frame.grid(row=2, column=0, sticky="nswe", padx=5, pady=10)

        # ============ Title Frame (with Connection) ============
        self.title_frame.grid_columnconfigure(0, weight=1)
        self.title_frame.grid_columnconfigure(1, weight=1)
        self.title_frame.grid_columnconfigure(2, weight=2)

        self.title_label = customtkinter.CTkLabel(master=self.title_frame, text=window_title, # <-- Use dynamic title
                                                  font=("Roboto Medium", -24))
        self.title_label.grid(row=0, column=0, rowspan=2, pady=10, padx=5, sticky="w")

        self.open_lid_button = customtkinter.CTkButton(master=self.title_frame, text="Open Lid", state="disabled", font=("Roboto Medium", -24), command=self.opn_lid)
        self.open_lid_button.grid(row=0, column=1, pady=10, padx=5, sticky="e")

        self.close_lid_button = customtkinter.CTkButton(master=self.title_frame, text="Close Lid", fg_color='red', state="disabled", font=("Roboto Medium", -24), command=self.cls_lid)
        self.close_lid_button.grid(row=1, column=1, pady=10, padx=5, sticky="e")

        self.port_label = customtkinter.CTkLabel(master=self.title_frame, text="Serial Port:")
        self.port_label.grid(row=0, column=2, sticky="e", padx=(10,0))

        # --- Populate ports, select auto_connect_port if provided ---
        available_ports = self.controller.get_available_ports()
        self.port_menu = customtkinter.CTkOptionMenu(master=self.title_frame, values=available_ports)
        if self.auto_connect_port and self.auto_connect_port in available_ports:
             self.port_menu.set(self.auto_connect_port)
        elif available_ports:
             self.port_menu.set(available_ports[0]) # Default to first port
        self.port_menu.grid(row=0, column=3, sticky="we", padx=10)

        self.connect_button = customtkinter.CTkButton(master=self.title_frame, text="Connect", width=150, command=self.toggle_connection)
        self.connect_button.grid(row=1, column=3, sticky="we", padx=10)

        self.refresh_ports_button = customtkinter.CTkButton(master=self.title_frame, text="Refresh", width=80, command=self.refresh_ports)
        self.refresh_ports_button.grid(row=0, column=4, sticky="w", padx=(0,10))

        self.connection_status_label = customtkinter.CTkLabel(master=self.title_frame, text="Disconnected", text_color="grey")
        self.connection_status_label.grid(row=1, column=2, sticky="e", padx=(10,0))

        # --- Disable port selection if launched for a specific port ---
        if self.auto_connect_port:
            self.port_menu.configure(state="disabled")
            self.refresh_ports_button.configure(state="disabled")


        # ============ Preset Row ============
        # ... (rest of UI layout is unchanged) ...
        self.preset_frame.grid_columnconfigure(0, weight=4)
        self.preset_frame.grid_columnconfigure(1, weight=3)
        self.preset_frame.grid_rowconfigure(0, weight=1)

        self.preset_frame_left = customtkinter.CTkFrame(master=self.preset_frame)
        self.preset_frame_left.grid(row=0, column=0, sticky="nswe", padx=5, pady=10)
        self.preset_frame_left.grid_columnconfigure((0, 1, 2), weight=1)
        self.preset_frame_left.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)

        self.preset_frame_left_title = customtkinter.CTkLabel(master=self.preset_frame_left, text="Preset temperatures", font=("Roboto Medium", -20))
        self.preset_frame_left_title.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        self.plate_label = customtkinter.CTkLabel(master=self.preset_frame_left, text="Set Plate Temperature °C", font=("Roboto Medium", -16), text_color='grey')
        self.plate_label.grid(row=1, column=1, sticky="n", padx=5, pady=0)
        self.plate_entry = customtkinter.CTkEntry(master=self.preset_frame_left, width=90, justify='center', fg_color='black', placeholder_text='°C', placeholder_text_color='grey')
        self.plate_entry.grid(row=2, column=1, sticky="n", padx=5, pady=0)
        self.preset_frame_left_lid_label = customtkinter.CTkLabel(master=self.preset_frame_left, text=" Set Lid Temperature °C", font=("Roboto Medium", -16), text_color='grey')
        self.preset_frame_left_lid_label.grid(row=1, column=0, sticky="n", padx=5, pady=0)
        self.lid_entry = customtkinter.CTkEntry(master=self.preset_frame_left, width=90, justify='center', fg_color='black', placeholder_text='°C', placeholder_text_color='grey')
        self.lid_entry.grid(row=2, column=0, sticky="n", padx=5, pady=0)
        self.plate_button = customtkinter.CTkButton(master=self.preset_frame_left, text='Set Plate Temp', state="disabled", command=self.set_plate_temp)
        self.plate_button.grid(row=3, column=1, columnspan=1, rowspan=2, pady=0, padx=5, sticky="n")
        self.lid_button = customtkinter.CTkButton(master=self.preset_frame_left, text='Set Lid Temp', state="disabled", command=self.set_lid_temp)
        self.lid_button.grid(row=3, column=0, columnspan=1, rowspan=1, pady=0, padx=5, sticky="n")

        self.deactivate_presets_button = customtkinter.CTkButton(master=self.preset_frame_left, width=250, height=35,
                                                                 text='Deactivate all', fg_color='blue',
                                                                 state="disabled", command=self.deactivate_all_presets)
        self.deactivate_presets_button.grid(row=2, column=2, columnspan=1, rowspan=1, pady=10, padx=5, sticky="n")

        self.preset_frame_right = customtkinter.CTkFrame(master=self.preset_frame)
        self.preset_frame_right.grid(row=0, column=1, sticky="nsew", padx=5, pady=10)
        self.preset_frame_right.columnconfigure(0, weight=1)
        self.preset_frame_right.rowconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.fr_lid_label = customtkinter.CTkLabel(master=self.preset_frame_right, text="Lid Actual Temperature °C", font=("Roboto Medium", -16), text_color='white')
        self.fr_lid_label.grid(row=1, column=0, sticky="n", padx=5, pady=0)
        self.fr_lid_value_label = customtkinter.CTkLabel(master=self.preset_frame_right, text='°C', font=("Roboto Medium", -16), text_color='orange')
        self.fr_lid_value_label.grid(row=2, column=0, sticky="n", padx=0, pady=0)
        self.fr_plate_label = customtkinter.CTkLabel(master=self.preset_frame_right, text="Plate Actual Temperature °C", font=("Roboto Medium", -16), text_color='white')
        self.fr_plate_label.grid(row=3, column=0, sticky="n", padx=5, pady=0)
        self.fr_plate_value_label = customtkinter.CTkLabel(master=self.preset_frame_right, text="°C", font=("Roboto Medium", -16), text_color='light blue')
        self.fr_plate_value_label.grid(row=4, column=0, sticky="n", padx=5, pady=0)

        # ============ Parameter frame ============
        self.param_frame.grid_columnconfigure(0, weight=2)
        self.param_frame.grid_columnconfigure(1, weight=1)
        self.param_frame.grid_rowconfigure(0, weight=1)

        self.param_frame_right = customtkinter.CTkFrame(master=self.param_frame)
        self.param_frame_right.grid(row=0, column=1, sticky="nswe", padx=5, pady=10)
        self.param_frame_right.rowconfigure(0, weight=1)
        self.param_frame_right.rowconfigure(1, weight=25)
        self.param_frame_right.columnconfigure(0, weight=1)

        self.param_right_title = customtkinter.CTkLabel(master=self.param_frame_right, text="Protocol info", font=("Roboto Medium", -20), text_color='White')
        self.param_right_title.grid(row=0, column=0, sticky="n", padx=5, pady=0)

        self.protocol_label = customtkinter.CTkLabel(master=self.param_frame_right, text='', font=("Roboto Medium", -12), text_color='White', justify='left')
        self.protocol_label.grid(row=1, column=0, sticky="n", padx=5, pady=0)

        self.dialog_label = None
        self.confirm_button = None
        self.cancel_button = None

        self.show_setup_frame()

        # --- Auto-connect if launched with a port ---
        if self.auto_connect_port:
             self.after(100, self.toggle_connection) # Use 'after' to allow UI to build


    def show_setup_frame(self):
        # ... (this function is unchanged) ...
        if self.param_frame_left:
             self.param_frame_left.destroy()
        self.cancel_dialog()
        self.param_frame_left = customtkinter.CTkFrame(master=self.param_frame)
        self.param_frame_left.grid(row=0, column=0, sticky="nswe", padx=5, pady=10)
        self.param_frame_left.rowconfigure((0, 1, 2, 3, 4), weight=1)
        self.param_frame_left.columnconfigure((0, 1), weight=1)
        self.param_left_title = customtkinter.CTkLabel(master=self.param_frame_left, text="Import Protocol CSV file", font=("Roboto Medium", -20), text_color='White')
        self.param_left_title.grid(row=0, column=0, columnspan=2, sticky="nswe", padx=5, pady=10)
        self.path_label = customtkinter.CTkLabel(master=self.param_frame_left, text="", font=("Roboto Medium", -13), text_color='White')
        self.path_label.grid(row=1, column=1, columnspan=1, sticky="ew", padx=5, pady=10)
        self.experiment_name_label = customtkinter.CTkEntry(master=self.param_frame_left, placeholder_text='Experiment Name', font=("Roboto Medium", -13), text_color='White')
        self.experiment_name_label.grid(row=1, column=0, columnspan=1, sticky="ew", padx=5, pady=10)
        self.experiment_name_label.bind("<KeyRelease>", self.run_ready_check)
        self.import_button = customtkinter.CTkButton(master=self.param_frame_left, text="Import", font=("Roboto Medium", -20), text_color='White', width=150, command=self.select_file)
        self.import_button.grid(row=2, column=0, columnspan=2, sticky="n", padx=5, pady=5)
        self.run_button = customtkinter.CTkButton(master=self.param_frame_left, text="Run Protocol", font=("Roboto Medium", -20), fg_color='grey', text_color='White', width=250, height=50, state='disabled', command=self.start_run_thread)
        self.run_button.grid(row=3, column=0, columnspan=2, sticky="n", padx=5, pady=5)
        self.run_ready_check()
        state = "normal" if self.controller.port else "disabled"
        self.import_button.configure(state=state)


    # --- Connection Methods ---

    def refresh_ports(self):
        # --- Don't allow refresh if launched for specific port ---
        if self.auto_connect_port:
            return
        self.port_menu.configure(values=self.controller.get_available_ports())

    # --- UPDATED FUNCTION ---
    def toggle_connection(self):
        """Connects/disconnects and manages UI state."""
        if self.controller.port:
            # --- Disconnect ---
            self.controller.disconnect()
            self.connection_status_label.configure(text="Disconnected", text_color="grey")
            self.connect_button.configure(text="Connect", fg_color=customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])
            
            # Only enable port selection if NOT launched for a specific port
            if not self.auto_connect_port:
                 self.port_menu.configure(state="normal")
                 self.refresh_ports_button.configure(state="normal")
                 
            self.set_controls_state("disabled")
            self.fr_lid_value_label.configure(text='°C')
            self.fr_plate_value_label.configure(text='°C')
        else:
            # --- Connect ---
            port_name = self.port_menu.get()
            if port_name == "No Ports Found":
                self.connection_status_label.configure(text="No Port", text_color="yellow")
                return

            if self.controller.connect(port_name):
                self.connection_status_label.configure(text="Connected", text_color="light green")
                self.connect_button.configure(text="Disconnect", fg_color="dark red")
                self.port_menu.configure(state="disabled") # Always disable menu when connected
                self.refresh_ports_button.configure(state="disabled") # Always disable refresh when connected
                self.set_controls_state("normal")
            else:
                self.connection_status_label.configure(text="Failed", text_color="red")
                # Ensure controls are disabled on failed connect
                self.set_controls_state("disabled")

    def set_controls_state(self, state):
        # ... (this function is unchanged) ...
        self.open_lid_button.configure(state=state)
        self.close_lid_button.configure(state=state)
        self.plate_button.configure(state=state)
        self.lid_button.configure(state=state)
        self.deactivate_presets_button.configure(state=state)
        if state == "normal":
            self.monitor_stop_event.clear()
            self.monitor_thread = threading.Thread(target=self._monitor_temperatures, args=(self.monitor_stop_event,), daemon=True)
            self.monitor_thread.start()
        else:
            self.monitor_stop_event.set()
            if self.monitor_thread:
                self.monitor_thread.join(timeout=1.0)
            self.deactivate_presets_button.configure(fg_color='blue')
            self.close_lid_button.configure(fg_color='red')
            self.plate_button.configure(fg_color=customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])
            self.lid_button.configure(fg_color=customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])
        if hasattr(self, 'run_button') and self.run_button:
            self.run_ready_check()
        if hasattr(self, 'import_button') and self.import_button:
            self.import_button.configure(state=state)


    def _monitor_temperatures(self, stop_event):
        # ... (this function is unchanged) ...
        print("Starting temperature monitor thread.")
        def safe_configure(widget, text):
            try:
                if widget and widget.winfo_exists():
                    widget.configure(text=text)
            except Exception as e:
                print(f"Safe configure error in monitor: {e}")
        while not stop_event.is_set():
            try:
                if not self.controller or not self.controller.port: break
                lid_temp = self.controller.get_lid_temperature()
                plate_temp, _ = self.controller.get_plate_info()
                self.after(0, lambda t=f"{lid_temp:.1f} °C": safe_configure(self.fr_lid_value_label, t))
                self.after(0, lambda t=f"{plate_temp:.1f} °C": safe_configure(self.fr_plate_value_label, t))
                stop_event.wait(2.0)
            except Exception as e:
                print(f"Monitor thread error (device likely disconnected): {e}")
                break
        print("Stopping temperature monitor thread.")


    # --- Protocol Run Methods ---

    def start_run_thread(self):
        # ... (this function is unchanged) ...
        experiment_title = self.experiment_name_label.get()
        self.set_controls_state("disabled")
        if self.param_frame_left: self.param_frame_left.destroy()
        self.emergency_stop_event.clear()
        self.param_frame_left = customtkinter.CTkFrame(master=self.param_frame)
        self.param_frame_left.grid(row=0, column=0, sticky="nswe", padx=5, pady=10)
        self.param_frame_left.rowconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.param_frame_left.columnconfigure((0, 1, 2, 3), weight=1)
        self.running_label = customtkinter.CTkLabel(master=self.param_frame_left, text="")
        self.running_label.grid(row=0, column=0, columnspan=4, sticky="n", padx=5, pady=5)
        self.current_lid_label = customtkinter.CTkLabel(master=self.param_frame_left, text='Current Lid \nTemperature', font=("Roboto Medium", -18), text_color='grey', justify='center')
        self.current_lid_label.grid(row=1, column=0, sticky="n", padx=10, pady=5)
        self.current_lid_value_label = customtkinter.CTkLabel(master=self.param_frame_left, text='', font=("Roboto Medium", -24), text_color='orange', justify='center')
        self.current_lid_value_label.grid(row=2, column=0, sticky="n", padx=10, pady=5)
        self.current_plate_label = customtkinter.CTkLabel(master=self.param_frame_left, text='Current Plate \nTemperature', font=("Roboto Medium", -18), text_color='grey', justify='center')
        self.current_plate_label.grid(row=1, column=1, sticky="n", padx=10, pady=5)
        self.current_plate_value_label = customtkinter.CTkLabel(master=self.param_frame_left, text='', font=("Roboto Medium", -24), text_color='light blue', justify='center')
        self.current_plate_value_label.grid(row=2, column=1, sticky="n", padx=10, pady=5)
        self.step_time_label = customtkinter.CTkLabel(master=self.param_frame_left, text='Step Time \nRemaining', font=("Roboto Medium", -18), text_color='grey', justify='center')
        self.step_time_label.grid(row=1, column=2, sticky="n", padx=10, pady=5)
        self.step_time_value_label = customtkinter.CTkLabel(master=self.param_frame_left, text='', font=("Roboto Medium", -24), text_color='light green', justify='center')
        self.step_time_value_label.grid(row=2, column=2, sticky="n", padx=10, pady=5)
        self.skip_step_button = customtkinter.CTkButton(master=self.param_frame_left, width=200, height=35, text='Skip Current Step', fg_color='blue', command=self.skip_step_are_you_sure)
        self.skip_step_button.grid(row=3, column=0, columnspan=2, sticky="e", padx=10, pady=5)
        self.emergency_stop_button = customtkinter.CTkButton(master=self.param_frame_left, width=200, height=35, text='Emergency Stop', fg_color='dark red', command=self.emergency_stop_are_you_sure)
        self.emergency_stop_button.grid(row=3, column=2, columnspan=2, sticky="w", padx=10, pady=5)
        self.protocol_thread = threading.Thread(target=self._run_protocol_wrapper, args=(experiment_title,), daemon=True)
        self.protocol_thread.start()


    def _run_protocol_wrapper(self, experiment_title):
        # ... (this function is unchanged) ...
        def safe_configure(widget, **kwargs):
            try:
                if widget and widget.winfo_exists(): widget.configure(**kwargs)
            except Exception as e: print(f"Safe configure error: {e}")
        def update_step_label(text): self.after(0, lambda t=text: safe_configure(self.running_label, text=t, font=("Roboto Medium", -18)))
        def update_lid_label(text): self.after(0, lambda t=text: safe_configure(self.current_lid_value_label, text=t))
        def update_plate_label(text): self.after(0, lambda t=text: safe_configure(self.current_plate_value_label, text=t))
        def update_time_label(text): self.after(0, lambda t=text: safe_configure(self.step_time_value_label, text=t))
        try:
            run_protocol(self.controller, self.tc_protocol, update_step_label, update_lid_label, update_plate_label, update_time_label, self.emergency_stop_event, experiment_title)
        except Exception as e: print(f"Protocol thread encountered an error: {e}")
        finally:
            print("Protocol thread finished. Scheduling UI reset.")
            self.after(100, self._reset_ui_after_run)


    def _reset_ui_after_run(self):
        # ... (this function is unchanged) ...
        if self.protocol_thread is None: print("UI reset skipped; already handled by emergency_stop."); return
        self.protocol_thread = None
        self.emergency_stop_event.clear()
        self.fr_plate_value_label.configure(text='°C')
        self.fr_lid_value_label.configure(text='°C')
        self.show_setup_frame()
        self.set_controls_state("normal")
        print("UI has been reset after normal run.")


    def run_ready_check(self, event=None):
        # ... (this function is unchanged) ...
        if not (hasattr(self, 'run_button') and self.run_button): return
        is_connected = self.controller.port is not None
        has_protocol = len(self.tc_protocol) > 0
        has_name = len(self.experiment_name_label.get()) > 5
        is_running = self.protocol_thread and self.protocol_thread.is_alive()
        if is_connected and has_protocol and has_name and not is_running: self.run_button.configure(state='normal', fg_color='dark red')
        else: self.run_button.configure(state='disabled', fg_color='grey')


    def select_file(self):
        # ... (this function is unchanged) ...
        self.wm_attributes('-topmost', 1)
        try:
            file = fd.askopenfile(parent=self, initialdir='')
            if not file: self.wm_attributes('-topmost', 0); return
            txt_name = file.name
            self.wm_attributes('-topmost', 0)
            self.path_label.configure(text=txt_name)
            self.tc_protocol = protocol_dict(txt_name)
            self.run_ready_check()
            string = ""
            with open(txt_name, 'r') as read_file:
                csv_read = csv.reader(read_file, delimiter=',')
                step_count, stage_count = 1, 1
                for line in csv_read:
                    if line[0] == 'CYCLES': string += f'\n\n\t\tStage - {stage_count}\nCycles - {line[1]}\nStep    Plate_temp    Time(seconds)    Set Lid Target\n'; step_count, stage_count = 1, stage_count + 1
                    elif line[0] == 'STEP': time_val = line[3] if line[3] else 'Hold'; string += f'  {step_count}                {line[2]}                        {time_val}                                  {line[4]}\n'; step_count += 1
                    elif line[0] == 'DEACTIVATE_ALL': string += f'  {step_count}                                 Deactivate All\n'; step_count += 1
                    elif line[0] == 'END&GRAPH': string += f'  {step_count}                                  End Protocol\n'
                self.protocol_label.configure(text=string, font=("Roboto Medium", -12), text_color='white', justify='left')
        except Exception as e:
            self.wm_attributes('-topmost', 0)
            self.path_label.configure(text='File Error', font=("Roboto Medium", -16))
            self.protocol_label.configure(text=f'Input File Error: {e}\n\nCheck CSV format.\nMust start with CYCLES.', font=("Roboto Medium", -16), text_color='yellow')
            self.tc_protocol = {}
        self.run_ready_check()


    # --- "ARE YOU SURE" DIALOGS ---

    def skip_step_are_you_sure(self):
        # ... (this function is unchanged) ...
        self.cancel_dialog()
        self.dialog_label = customtkinter.CTkLabel(master=self.param_frame_left, text='Skip Current Step?\nAre You Sure?', font=("Roboto Medium", -20), width=300, text_color='yellow', justify='center')
        self.dialog_label.grid(row=4, column=0, columnspan=4, sticky="n", padx=10, pady=10)
        self.confirm_button = customtkinter.CTkButton(master=self.param_frame_left, text='Skip', font=("Roboto Medium", -20), fg_color='blue', text_color='white', command=self.skip_step)
        self.confirm_button.grid(row=5, column=0, columnspan=2, sticky="e", padx=20, pady=10)
        self.cancel_button = customtkinter.CTkButton(master=self.param_frame_left, text='Cancel', font=("Roboto Medium", -20), text_color='white', command=self.cancel_dialog)
        self.cancel_button.grid(row=5, column=2, columnspan=2, sticky="w", padx=20, pady=10)


    def emergency_stop_are_you_sure(self):
        # ... (this function is unchanged) ...
        self.cancel_dialog()
        self.dialog_label = customtkinter.CTkLabel(master=self.param_frame_left, text='EMERGENCY STOP?\nThis will halt the entire protocol!', font=("Roboto Medium", -20), width=400, text_color='red', justify='center')
        self.dialog_label.grid(row=4, column=0, columnspan=4, sticky="n", padx=10, pady=10)
        self.confirm_button = customtkinter.CTkButton(master=self.param_frame_left, text='STOP NOW', font=("Roboto Medium", -20), fg_color='dark red', text_color='white', command=self.emergency_stop)
        self.confirm_button.grid(row=5, column=0, columnspan=2, sticky="e", padx=20, pady=10)
        self.cancel_button = customtkinter.CTkButton(master=self.param_frame_left, text='Cancel', font=("Roboto Medium", -20), text_color='white', command=self.cancel_dialog)
        self.cancel_button.grid(row=5, column=2, columnspan=2, sticky="w", padx=20, pady=10)


    # --- Hardware Control Wrappers ---

    def deactivate_all_presets(self):
        # ... (this function is unchanged) ...
        if self.controller: self.controller.deactivate_all()


    def skip_step(self):
        # ... (this function is unchanged) ...
        print("Skip Step button pressed. Deactivating all.")
        if self.controller: self.controller.deactivate_all()
        self.cancel_dialog()


    def emergency_stop(self):
        # ... (this function is unchanged) ...
        print("EMERGENCY STOP button pressed.")
        self.protocol_thread = None
        self.emergency_stop_event.set()
        if self.controller: self.controller.deactivate_all()
        self.show_setup_frame()
        self.set_controls_state("normal")
        self.cancel_dialog()


    def cancel_dialog(self):
        # ... (this function is unchanged) ...
        if self.dialog_label: self.dialog_label.destroy(); self.dialog_label = None
        if self.confirm_button: self.confirm_button.destroy(); self.confirm_button = None
        if self.cancel_button: self.cancel_button.destroy(); self.cancel_button = None


    def set_plate_temp(self):
        # ... (this function is unchanged) ...
        if self.controller: self.controller.set_plate_temperature(self.plate_entry.get())


    def set_lid_temp(self):
        # ... (this function is unchanged) ...
        if self.controller: self.controller.set_lid_temperature(self.lid_entry.get())


    def opn_lid(self):
        # ... (this function is unchanged) ...
        if self.controller: self.controller.open_lid()


    def cls_lid(self):
        # ... (this function is unchanged) ...
        if self.controller: self.controller.close_lid()


    def on_closing(self, event=0):
        # ... (this function is unchanged) ...
        self.emergency_stop_event.set()
        self.monitor_stop_event.set()
        if self.controller: self.controller.deactivate_all(); self.controller.disconnect()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()