from tkinter import filedialog as fd
from tkinter import PhotoImage
import customtkinter
from tc_send_code import HardwareController  # <-- Import class
from protocol_manager import run_protocol, protocol_dict # <-- Import logic
import csv
import threading
import pathlib  # <-- For cross-platform paths

# --- Setup base directory for assets ---
BASE_DIR = pathlib.Path(__file__).parent
IMAGE_PATH = BASE_DIR / 'HelixCycler.png'
# ICON_PATH = BASE_DIR / 'HelixCycler.ico' # .ico is windows only

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme('blue')


class App(customtkinter.CTk):
    WIDTH = 1200
    HEIGHT = 720

    def __init__(self):
        super().__init__()

        self.title("HelixCycler")
        self.geometry(f"{App.WIDTH}x{App.HEIGHT}")
        self.state('zoomed')
        
        # --- Cross-platform asset loading ---
        # self.iconbitmap(ICON_PATH) # Commented out, .ico is not cross-platform
        try:
            self.bg = PhotoImage(file=IMAGE_PATH)
        except Exception as e:
            print(f"Could not load background image: {e}")
            self.bg = None # Handle missing image
            
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # --- App state ---
        self.controller = HardwareController() # Controller instance
        self.protocol_thread = None
        self.tc_protocol = {}

        # ============ create frames ============
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1) # Connection/Preset frame
        self.grid_rowconfigure(2, weight=2) # Param frame

        self.title_frame = customtkinter.CTkFrame(master=self, corner_radius=0)
        self.title_frame.grid(row=0, column=0, sticky="nswe", padx=10, pady=5)

        self.preset_frame = customtkinter.CTkFrame(master=self)
        self.preset_frame.grid(row=1, column=0, sticky="nswe", padx=5, pady=10)

        self.param_frame = customtkinter.CTkFrame(master=self)
        self.param_frame.grid(row=2, column=0, sticky="nswe", padx=5, pady=10)

        # ============ Title Frame (with Connection) ============
        self.title_frame.grid_columnconfigure(0, weight=1)
        self.title_frame.grid_columnconfigure(1, weight=1)
        self.title_frame.grid_columnconfigure(2, weight=2) # Connection widgets

        self.title_label = customtkinter.CTkLabel(master=self.title_frame,
                                                  text="HelixCycler - OT thermocycler app",
                                                  font=("Roboto Medium", -24))
        self.title_label.grid(row=0, column=0, rowspan=2, pady=10, padx=5, sticky="w")

        self.open_lid_button = customtkinter.CTkButton(master=self.title_frame,
                                                       text="Open Lid", state="disabled",
                                                       font=("Roboto Medium", -24), command=self.opn_lid)
        self.open_lid_button.grid(row=0, column=1, pady=10, padx=5, sticky="e")
        
        self.close_lid_button = customtkinter.CTkButton(master=self.title_frame,
                                                       text="Close Lid", fg_color='red', state="disabled",
                                                       font=("Roboto Medium", -24), command=self.cls_lid)
        self.close_lid_button.grid(row=1, column=1, pady=10, padx=5, sticky="e")

        # --- New Connection Widgets ---
        self.port_label = customtkinter.CTkLabel(master=self.title_frame, text="Serial Port:")
        self.port_label.grid(row=0, column=2, sticky="e", padx=(10,0))
        
        self.port_menu = customtkinter.CTkOptionMenu(master=self.title_frame,
                                                     values=self.controller.get_available_ports())
        self.port_menu.grid(row=0, column=3, sticky="we", padx=10)

        self.connect_button = customtkinter.CTkButton(master=self.title_frame, text="Connect",
                                                      width=150, command=self.toggle_connection)
        self.connect_button.grid(row=1, column=3, sticky="we", padx=10)
        
        self.refresh_ports_button = customtkinter.CTkButton(master=self.title_frame, text="Refresh",
                                                            width=80, command=self.refresh_ports)
        self.refresh_ports_button.grid(row=0, column=4, sticky="w", padx=(0,10))
        
        self.connection_status_label = customtkinter.CTkLabel(master=self.title_frame, text="Disconnected", text_color="grey")
        self.connection_status_label.grid(row=1, column=2, sticky="e", padx=(10,0))


        # ============ Preset Row ============
        # ... (rest of preset_frame layout is unchanged) ...
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
        self.deactivate_button = customtkinter.CTkButton(master=self.preset_frame_left, width=250, height=35, text='Deactivate all', fg_color='dark red', state="disabled", command=self.deactivate_all)
        self.deactivate_button.grid(row=2, column=2, columnspan=1, rowspan=1, pady=10, padx=5, sticky="n")

        self.preset_frame_right = customtkinter.CTkFrame(master=self.preset_frame)
        self.preset_frame_right.grid(row=0, column=1, sticky="nsew", padx=5, pady=10)
        self.preset_frame_right.columnconfigure(0, weight=1)
        self.preset_frame_right.rowconfigure((0, 1, 2, 3, 4, 5), weight=1)
        self.fr_lid_label = customtkinter.CTkLabel(master=self.preset_frame_right, text="Lid Preset Temperature °C", font=("Roboto Medium", -16), text_color='white')
        self.fr_lid_label.grid(row=1, column=0, sticky="n", padx=5, pady=0)
        self.fr_lid_value_label = customtkinter.CTkLabel(master=self.preset_frame_right, text='°C', font=("Roboto Medium", -16), text_color='orange')
        self.fr_lid_value_label.grid(row=2, column=0, sticky="n", padx=0, pady=0)
        self.fr_plate_label = customtkinter.CTkLabel(master=self.preset_frame_right, text="Plate Preset Temperature °C", font=("Roboto Medium", -16), text_color='white')
        self.fr_plate_label.grid(row=3, column=0, sticky="n", padx=5, pady=0)
        self.fr_plate_value_label = customtkinter.CTkLabel(master=self.preset_frame_right, text="°C", font=("Roboto Medium", -16), text_color='light blue')
        self.fr_plate_value_label.grid(row=4, column=0, sticky="n", padx=5, pady=0)

        # ============ Parameter frame ============
        # ... (param_frame layout is unchanged) ...
        self.param_frame.grid_columnconfigure(0, weight=2)
        self.param_frame.grid_columnconfigure(1, weight=1)
        self.param_frame.grid_rowconfigure(0, weight=1)
        self.param_frame_left = customtkinter.CTkFrame(master=self.param_frame)
        self.param_frame_left.grid(row=0, column=0, sticky="nswe", padx=5, pady=10)
        self.param_frame_left.rowconfigure((0, 1, 2, 3, 4), weight=1)
        self.param_frame_left.columnconfigure((0, 1), weight=1)
        self.param_frame_right = customtkinter.CTkFrame(master=self.param_frame)
        self.param_frame_right.grid(row=0, column=1, sticky="nswe", padx=5, pady=10)
        self.param_frame_right.rowconfigure(0, weight=1)
        self.param_frame_right.rowconfigure(1, weight=25)
        self.param_frame_right.columnconfigure(0, weight=1)
        self.param_left_title = customtkinter.CTkLabel(master=self.param_frame_left, text="Import Protocol CSV file", font=("Roboto Medium", -20), text_color='White')
        self.param_left_title.grid(row=0, column=0, columnspan=2, sticky="nswe", padx=5, pady=10)
        self.path_label = customtkinter.CTkLabel(master=self.param_frame_left, text="", font=("Roboto Medium", -13), text_color='White')
        self.path_label.grid(row=1, column=1, columnspan=1, sticky="ew", padx=5, pady=10)
        self.experiment_name_label = customtkinter.CTkEntry(master=self.param_frame_left, placeholder_text='Experiment Name', font=("Roboto Medium", -13), text_color='White')
        self.experiment_name_label.grid(row=1, column=0, columnspan=1, sticky="ew", padx=5, pady=10)
        self.experiment_name_label.bind("<KeyRelease>", self.run_ready_check)
        self.import_button = customtkinter.CTkButton(master=self.param_frame_left, text="Import", font=("Roboto Medium", -20), text_color='White', width=150, command=self.select_file)
        self.import_button.grid(row=2, column=0, columnspan=2, sticky="n", padx=5, pady=5)
        self.run_button = customtkinter.CTkButton(master=self.param_frame_left, text="Run Protocol", font=("Roboto Medium", -20), fg_color='grey', text_color='White', width=250, height=50, state='disabled', command=self.start_run_thread) # <-- Changed command
        self.run_button.grid(row=3, column=0, columnspan=2, sticky="n", padx=5, pady=5)
        self.param_right_title = customtkinter.CTkLabel(master=self.param_frame_right, text="Protocol info", font=("Roboto Medium", -20), text_color='White')
        self.param_right_title.grid(row=0, column=0, sticky="n", padx=5, pady=0)
        self.protocol_label = customtkinter.CTkLabel(master=self.param_frame_right, text='', font=("Roboto Medium", -12), text_color='White', justify='left')
        self.protocol_label.grid(row=1, column=0, sticky="n", padx=5, pady=0)

        # --- Protocol running widgets (will be created in self.run) ---
        self.running_label = None
        self.current_lid_value_label = None
        self.current_plate_value_label = None
        self.step_time_value_label = None
        self.stop_protocol_button = None
        self.are_you_sure_label = None
        self.stop_button = None
        self.cancel_button = None

    # --- New Connection Methods ---
    
    def refresh_ports(self):
        """Updates the list of available serial ports."""
        self.port_menu.configure(values=self.controller.get_available_ports())

    def toggle_connection(self):
        """Connects to or disconnects from the selected serial port."""
        if self.controller.port:
            # --- Disconnect ---
            self.controller.disconnect()
            self.connection_status_label.configure(text="Disconnected", text_color="grey")
            self.connect_button.configure(text="Connect", fg_color=customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])
            self.port_menu.configure(state="normal")
            self.refresh_ports_button.configure(state="normal")
            self.set_controls_state("disabled")
        else:
            # --- Connect ---
            port_name = self.port_menu.get()
            if port_name == "No Ports Found":
                self.connection_status_label.configure(text="No Port", text_color="yellow")
                return
                
            if self.controller.connect(port_name):
                self.connection_status_label.configure(text="Connected", text_color="light green")
                self.connect_button.configure(text="Disconnect", fg_color="dark red")
                self.port_menu.configure(state="disabled")
                self.refresh_ports_button.configure(state="disabled")
                self.set_controls_state("normal")
            else:
                self.connection_status_label.configure(text="Failed", text_color="red")
                
    def set_controls_state(self, state):
        """Enables or disables all hardware controls."""
        self.open_lid_button.configure(state=state)
        self.close_lid_button.configure(state=state)
        self.plate_button.configure(state=state)
        self.lid_button.configure(state=state)
        self.deactivate_button.configure(state=state)
        # Re-apply grey color if disabling
        if state == "disabled":
            self.deactivate_button.configure(fg_color='dark red') # Keep color
            self.close_lid_button.configure(fg_color='red') # Keep color
            self.plate_button.configure(fg_color=customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])
            self.lid_button.configure(fg_color=customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])
        self.run_ready_check() # Check run button state

    # --- Protocol Run Methods ---
    
    def start_run_thread(self):
        """Starts the run_protocol function in a new daemon thread."""
        # Rebuild the run frame
        self.param_frame_left = customtkinter.CTkFrame(master=self.param_frame)
        self.param_frame_left.grid(row=0, column=0, sticky="nswe", padx=5, pady=10)
        self.param_frame_left.rowconfigure((0, 1, 2, 3, 4), weight=1)
        self.param_frame_left.columnconfigure((0, 1, 2, 3), weight=1)

        self.running_label = customtkinter.CTkLabel(master=self.param_frame_left)
        self.running_label.grid(row=0, column=0, columnspan=3, sticky="n", padx=5, pady=5)
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
        self.stop_protocol_button = customtkinter.CTkButton(master=self.param_frame_left, width=250, height=35, text='Stop Protocol', fg_color='dark red', command=self.are_you_sure)
        self.stop_protocol_button.grid(row=3, column=1, sticky="n", padx=10, pady=5)

        # Disable preset controls during run
        self.set_controls_state("disabled")
        self.import_button.configure(state="disabled")
        
        # Start thread
        self.protocol_thread = threading.Thread(target=run_protocol, 
                                                args=(self.controller, self.tc_protocol, self.running_label, 
                                                      self.current_lid_value_label, self.current_plate_value_label, 
                                                      self.step_time_value_label, self.experiment_name_label.get()),
                                                daemon=True) # Daemon=True allows app to exit
        self.protocol_thread.start()

    def run_ready_check(self, event=None):
        """Checks if the app is ready to run a protocol."""
        is_connected = self.controller.port is not None
        has_protocol = len(self.tc_protocol) > 0
        has_name = len(self.experiment_name_label.get()) > 5
        
        if is_connected and has_protocol and has_name:
            self.run_button.configure(state='normal', fg_color='dark red')
        else:
            self.run_button.configure(state='disabled', fg_color='grey')

    def select_file(self):
        # ... (This function is largely unchanged) ...
        self.wm_attributes('-topmost', 1)
        try:
            file = fd.askopenfile(parent=self, initialdir='')
            if not file:
                self.wm_attributes('-topmost', 0)
                return
                
            txt_name = file.name
            self.wm_attributes('-topmost', 0) # Return focus
            
            self.path_label.configure(text=txt_name)
            self.tc_protocol = protocol_dict(txt_name)
            self.run_ready_check()

            string = ""
            with open(txt_name, 'r') as read_file:
                csv_read = csv.reader(read_file, delimiter=',')
                step_count = 1
                stage_count = 1
                for line in csv_read:
                    if line[0] == 'CYCLES':
                        string += f'\n\n\t\tStage - {stage_count}\nCycles - {line[1]}\nStep    Plate_temp    Time(seconds)    Set Lid Target\n'
                        step_count = 1
                        stage_count += 1
                    elif line[0] == 'STEP':
                        time_val = line[3] if line[3] else 'Hold'
                        string += f'  {step_count}                {line[2]}                        {time_val}' \
                                  f'                                  {line[4]}\n'
                        step_count += 1
                    elif line[0] == 'DEACTIVATE_ALL':
                        string += f'  {step_count}                                 Deactivate All\n'
                        step_count += 1
                    elif line[0] == 'END&GRAPH':
                        string += f'  {step_count}                                  End Protocol\n'
                self.protocol_label.configure(text=string, font=("Roboto Medium", -12), text_color='white', justify='left')
        except Exception as e:
            self.wm_attributes('-topmost', 0)
            self.path_label.configure(text='File Error', font=("Roboto Medium", -16))
            self.protocol_label.configure(text=f'Input File Error:\n{e}', font=("Roboto Medium", -16), text_color='yellow')
            self.tc_protocol = {}
        self.run_ready_check()

    def are_you_sure(self):
        # ... (This function is unchanged, but self.deactivate_all is now safe) ...
        self.are_you_sure_label = customtkinter.CTkLabel(master=self.param_frame_left,
                                                         text='Stop Protocol?\nAre You Sure?',
                                                         font=("Roboto Medium", -20), width=300,
                                                         text_color='yellow', justify='center')
        self.are_you_sure_label.grid(row=3, column=1, sticky="n", padx=10, pady=5)
        self.stop_button = customtkinter.CTkButton(master=self.param_frame_left, text='STOP',
                                                   font=("Roboto Medium", -20), fg_color='dark red',
                                                   text_color='white', command=self.deactivate_all)
        self.stop_button.grid(row=4, column=1, columnspan=2, sticky="w", padx=20, pady=10)
        self.cancel_button = customtkinter.CTkButton(master=self.param_frame_left, text='Cancel',
                                                     font=("Roboto Medium", -20), text_color='white',
                                                     command=self.cancel)
        self.cancel_button.grid(row=4, column=0, columnspan=2, sticky="e", padx=20, pady=10)

    # --- Hardware Control Wrappers ---
    
    def deactivate_all(self):
        if self.controller:
            self.controller.deactivate_all()
        self.fr_plate_value_label.configure(text='°C')
        self.fr_lid_value_label.configure(text='°C')
        # Also kill the protocol thread
        # Note: This is not perfectly safe, but deactivate_all() will cause
        # the thread's serial read to fail, which is handled.
        if self.protocol_thread and self.protocol_thread.is_alive():
            print("Stopping protocol thread via deactivation.")
            # Re-enable controls
            self.set_controls_state("normal")
            self.import_button.configure(state="normal")
        if self.are_you_sure_label:
            self.cancel() # Clean up 'are you sure' widgets

    def set_plate_temp(self):
        if self.controller:
            value = self.plate_entry.get()
            self.controller.set_plate_temperature(value)
            self.fr_plate_value_label.configure(text=value + '°C')

    def set_lid_temp(self):
        if self.controller:
            value = self.lid_entry.get()
            self.controller.set_lid_temperature(value)
            self.fr_lid_value_label.configure(text=value + '°C')

    def cancel(self):
        if self.are_you_sure_label:
            self.are_you_sure_label.destroy()
        if self.stop_button:
            self.stop_button.destroy()
        if self.cancel_button:
            self.cancel_button.destroy()

    def opn_lid(self):
        if self.controller:
            self.controller.open_lid()

    def cls_lid(self):
        if self.controller:
            self.controller.close_lid()

    def on_closing(self, event=0):
        if self.controller:
            self.controller.disconnect()
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()