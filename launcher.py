import customtkinter
import subprocess
import sys
import threading
import time
try:
    from tc_send_code import HardwareController
except ImportError as e:
    print(f"Error importing HardwareController: {e}")
    print("Make sure 'tc_send_code.py' is in the same directory as 'launcher.py'.")
    sys.exit(1)
except Exception as e:
    print(f"An unexpected error occurred during import: {e}")
    sys.exit(1)


customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("blue")

# Define highlight color (adjust as needed)
SELECTED_BG_COLOR = "#303F9F" # A darker blue

class LauncherApp(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("HelixCycler Launcher")
        self.geometry("500x350") # Slightly taller for clarity

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- Title ---
        self.title_label = customtkinter.CTkLabel(self, text="Select Thermocycler Port", font=("Roboto Medium", -18))
        self.title_label.grid(row=0, column=0, columnspan=2, pady=(10, 5))

        # --- Port Selection ---
        self.port_list_frame = customtkinter.CTkFrame(self)
        self.port_list_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)
        self.port_list_frame.grid_columnconfigure(0, weight=1)
        self.port_list_frame.grid_rowconfigure(0, weight=1)

        self.port_listbox = customtkinter.CTkTextbox(self.port_list_frame, activate_scrollbars=True, wrap="none")
        self.port_listbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.port_listbox.bind("<Button-1>", self.on_listbox_click)
        self.port_listbox.configure(state="disabled")

        # --- Configure the selection tag ---
        self.port_listbox.tag_config("selected", background=SELECTED_BG_COLOR)

        # --- Buttons ---
        self.button_frame = customtkinter.CTkFrame(self)
        self.button_frame.grid(row=2, column=0, columnspan=2, pady=10)

        self.refresh_button = customtkinter.CTkButton(self.button_frame, text="Refresh Ports", command=self.refresh_ports)
        self.refresh_button.grid(row=0, column=0, padx=10)

        self.launch_button = customtkinter.CTkButton(self.button_frame, text="Launch Control Window", state="disabled", command=self.launch_control_window)
        self.launch_button.grid(row=0, column=1, padx=10)

        # --- State Tracking ---
        self.launched_windows = {}
        self.selected_port = None
        self.selected_line_num = None # Store the highlighted line number

        # --- Initial Refresh ---
        self.refresh_ports()

        # --- Start Thread to Check for Closed Windows ---
        self.check_processes_thread = threading.Thread(target=self._check_launched_processes, daemon=True)
        self.check_processes_thread.start()

        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    # --- UPDATED FUNCTION ---
    def refresh_ports(self):
        """Scans for available serial ports and updates the listbox."""
        print("Refreshing ports...")
        self.port_listbox.configure(state="normal")
        # Remove previous selection highlight
        if self.selected_line_num is not None:
             self.port_listbox.tag_remove("selected", f"{self.selected_line_num}.0", f"{self.selected_line_num}.end")
        self.selected_line_num = None

        self.port_listbox.delete("1.0", "end")
        self.selected_port = None
        self.launch_button.configure(state="disabled")

        try:
            ports = HardwareController.get_available_ports()
            print(f"Found ports: {ports}")
            if ports == ["No Ports Found"]:
                self.port_listbox.insert("1.0", "No Ports Found")
            else:
                line_index = 1 # Keep track of line numbers
                for port in ports:
                    status = ""
                    if port in self.launched_windows:
                        if self.launched_windows[port] and self.launched_windows[port].poll() is None:
                            status = " (Running)"
                        else:
                            del self.launched_windows[port]
                    # Insert text *and* add a newline tag for easier targeting
                    self.port_listbox.insert(f"{line_index}.0", f"{port}{status}\n", f"line_{line_index}")
                    line_index += 1

        except Exception as e:
            print(f"Error getting available ports: {e}")
            self.port_listbox.insert("1.0", f"Error scanning ports: {e}")

        self.port_listbox.configure(state="disabled")
        print("Port refresh finished.")

    # --- UPDATED FUNCTION ---
    def on_listbox_click(self, event):
        """Handles clicks in the listbox to select a port and highlight it."""
        try:
            # Get the line number clicked
            index = self.port_listbox.index(f"@{event.x},{event.y}")
            line_num = int(index.split('.')[0])

            # Get the text of the clicked line
            line_text = self.port_listbox.get(f"{line_num}.0", f"{line_num}.end").strip()

            # Extract port name (remove status if present)
            port_name = line_text.split(" (Running)")[0]

            # Basic validation
            if not port_name or port_name == "No Ports Found" or line_text.startswith("Error"):
                # Clicked an invalid line, remove selection
                if self.selected_line_num is not None:
                    self.port_listbox.tag_remove("selected", f"{self.selected_line_num}.0", f"{self.selected_line_num}.end+1c")
                self.selected_port = None
                self.selected_line_num = None
                self.launch_button.configure(state="disabled")
                return

            # Remove previous highlight if different line clicked
            if self.selected_line_num is not None and self.selected_line_num != line_num:
                self.port_listbox.tag_remove("selected", f"{self.selected_line_num}.0", f"{self.selected_line_num}.end+1c")

            # Apply new highlight
            self.port_listbox.tag_add("selected", f"{line_num}.0", f"{line_num}.end+1c") # end+1c includes newline

            # Store selection
            self.selected_port = port_name
            self.selected_line_num = line_num
            print(f"Selected port: {self.selected_port} on line {self.selected_line_num}")

            # Enable button only if the selected port is not already running
            if "(Running)" not in line_text:
                self.launch_button.configure(state="normal")
            else:
                self.launch_button.configure(state="disabled")

        except Exception as e:
             # Handle clicks outside text lines
             print(f"Listbox click error (likely clicked empty area): {e}")
             if self.selected_line_num is not None:
                  self.port_listbox.tag_remove("selected", f"{self.selected_line_num}.0", f"{self.selected_line_num}.end+1c")
             self.selected_port = None
             self.selected_line_num = None
             self.launch_button.configure(state="disabled")

    # --- UPDATED FUNCTION ---
    def launch_control_window(self):
        """Launches a new helixcycler.py process for the selected port."""
        if not self.selected_port:
            return

        # Double-check if already launched and running (should be prevented by button state, but good practice)
        if self.selected_port in self.launched_windows:
            process = self.launched_windows[self.selected_port]
            if process and process.poll() is None:
                print(f"Control window for {self.selected_port} is already running.")
                return
            else:
                del self.launched_windows[self.selected_port]

        print(f"Launching control window for {self.selected_port}...")
        try:
            command = [sys.executable, "helixcycler.py", self.selected_port]
            process = subprocess.Popen(command)
            self.launched_windows[self.selected_port] = process
            print(f"Launched PID: {process.pid}")

        except Exception as e:
            print(f"Error launching process for {self.selected_port}: {e}")
            if self.selected_port in self.launched_windows: del self.launched_windows[self.selected_port]

        # Refresh list immediately after attempting launch
        self.refresh_ports()
        # Ensure button is disabled and selection cleared after launch attempt
        self.launch_button.configure(state="disabled")
        self.selected_port = None
        self.selected_line_num = None


    def _check_launched_processes(self):
        # ... (unchanged) ...
        while True:
            try:
                ports_to_remove = []
                for port in list(self.launched_windows.keys()):
                    process = self.launched_windows.get(port)
                    if process and process.poll() is not None:
                        print(f"Detected control window for {port} closed.")
                        ports_to_remove.append(port)
                if ports_to_remove:
                    for port in ports_to_remove: del self.launched_windows[port]
                    self.after(0, self.refresh_ports)
            except Exception as e: print(f"Error in process check thread: {e}")
            time.sleep(5)


    def on_closing(self):
        # ... (unchanged) ...
        print("Launcher closing. Subprocesses will continue running.")
        self.destroy()

if __name__ == "__main__":
    app = LauncherApp()
    app.mainloop()