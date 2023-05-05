from tkinter import filedialog as fd
from tkinter import PhotoImage
import customtkinter
from tc_send_code import *
import csv
import threading

customtkinter.set_appearance_mode("Dark")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme('blue')  # Themes: "blue" (standard), "green", "dark-blue"


class App(customtkinter.CTk):
    WIDTH = 1200
    HEIGHT = 720

    def __init__(self):
        super().__init__()

        self.title("HelixCycler")
        self.geometry(f"{App.WIDTH}x{App.HEIGHT}")
        self.state('zoomed')
        self.iconbitmap('HelixCycler.ico')
        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # call .on_closing() when app gets closed
        self.bg = PhotoImage(file='HelixCycler.png')
        # ============ create two frames ============

        # configure grid layout (4 rows)
        self.grid_columnconfigure(0, weight=1)

        # self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=2)

        self.title_frame = customtkinter.CTkFrame(master=self, corner_radius=0)
        self.title_frame.grid(row=0, column=0, sticky="nswe")

        self.preset_frame = customtkinter.CTkFrame(master=self)
        self.preset_frame.grid(row=1, column=0, sticky="nswe", padx=5, pady=10)

        self.param_frame = customtkinter.CTkFrame(master=self)
        self.param_frame.grid(row=2, column=0, sticky="nswe", padx=5, pady=10)

        # ============ Title Frame ============

        # configure grid layout (1x1)

        self.title_frame.grid_columnconfigure(0, weight=1)
        self.title_frame.grid_rowconfigure(0, weight=1)

        # Widgets on the left frame
        self.title_label = customtkinter.CTkLabel(master=self.title_frame,
                                                  text="HelixCycler - OT thermocycler app",
                                                  text_font=("Roboto Medium", -24))  # font name and size in px
        self.title_label.grid(row=0, column=0, pady=10, padx=5, sticky="nesw")

        self.open_lid_button = customtkinter.CTkButton(master=self.title_frame,
                                                       text="Open Lid",
                                                       text_font=("Roboto Medium", -24), command=self.opn_lid)
        self.open_lid_button.grid(row=0, column=1, pady=10, padx=5, sticky="nesw")
        self.open_lid_button = customtkinter.CTkButton(master=self.title_frame,
                                                       text="Close Lid", fg_color='red',
                                                       text_font=("Roboto Medium", -24), command=self.cls_lid)
        self.open_lid_button.grid(row=1, column=1, pady=10, padx=5, sticky="nesw")

        # ============ Preset Row  ============

        # configure grid layout (1x2) left col for temp presets, right for deactivate button
        self.preset_frame.grid_columnconfigure(0, weight=4)
        self.preset_frame.grid_columnconfigure(1, weight=3)
        self.preset_frame.grid_rowconfigure(0, weight=1)

        self.preset_frame_left = customtkinter.CTkFrame(master=self.preset_frame)
        self.preset_frame_left.grid(row=0, column=0, sticky="nswe", padx=5, pady=10)

        # ----------------preset_frame_left widgets----------------
        self.preset_frame_left.grid_columnconfigure((0, 1, 2), weight=1)
        self.preset_frame_left.grid_rowconfigure((0, 1, 2, 3, 4), weight=1)

        # self.preset_frame_left.grid_columnconfigure(5, weight=2)

        self.preset_frame_left_title = customtkinter.CTkLabel(master=self.preset_frame_left,
                                                              text="Preset temperatures",
                                                              text_font=("Roboto Medium", -20))
        self.preset_frame_left_title.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)

        self.plate_label = customtkinter.CTkLabel(master=self.preset_frame_left,
                                                  text="Set Plate Temperature °C",
                                                  text_font=("Roboto Medium", -16),
                                                  text_color='grey')
        self.plate_label.grid(row=1, column=1, sticky="n", padx=5, pady=0)

        self.plate_entry = customtkinter.CTkEntry(master=self.preset_frame_left, width=90, justify='center',
                                                  fg_color='black', placeholder_text='°C',
                                                  placeholder_text_color='grey')
        self.plate_entry.grid(row=2, column=1, sticky="n", padx=5, pady=0)

        self.preset_frame_left_lid_label = customtkinter.CTkLabel(master=self.preset_frame_left,
                                                                  text=" Set Lid Temperature °C",
                                                                  text_font=("Roboto Medium", -16),
                                                                  text_color='grey')
        self.preset_frame_left_lid_label.grid(row=1, column=0, sticky="n", padx=5, pady=0)

        self.lid_entry = customtkinter.CTkEntry(master=self.preset_frame_left, width=90, justify='center',
                                                fg_color='black', placeholder_text='°C', placeholder_text_color='grey')
        self.lid_entry.grid(row=2, column=0, sticky="n", padx=5, pady=0)

        self.plate_button = customtkinter.CTkButton(master=self.preset_frame_left, text='Set Plate Temp',
                                                    command=self.set_plate_temp)
        self.plate_button.grid(row=3, column=1, columnspan=1, rowspan=2, pady=0, padx=5, sticky="n")

        self.lid_button = customtkinter.CTkButton(master=self.preset_frame_left, text='Set Lid Temp',
                                                  command=self.set_lid_temp)
        self.lid_button.grid(row=3, column=0, columnspan=1, rowspan=1, pady=0, padx=5, sticky="n")

        self.deactivate_button = customtkinter.CTkButton(master=self.preset_frame_left, width=250, height=35,
                                                         text='Deactivate all', fg_color='dark red',
                                                         command=self.deactivate_all)
        self.deactivate_button.grid(row=2, column=2, columnspan=1, rowspan=1, pady=10, padx=5, sticky="n")
        # ------------------------Frame Right---------------------------------------

        self.preset_frame_right = customtkinter.CTkFrame(master=self.preset_frame)
        self.preset_frame_right.grid(row=0, column=1, sticky="nsew", padx=5, pady=10)
        self.preset_frame_right.columnconfigure(0, weight=1)
        self.preset_frame_right.rowconfigure((0, 1, 2, 3, 4, 5), weight=1)

        self.fr_lid_label = customtkinter.CTkLabel(master=self.preset_frame_right,
                                                   text="Lid Preset Temperature °C",
                                                   text_font=("Roboto Medium", -16),
                                                   text_color='white')
        self.fr_lid_label.grid(row=1, column=0, sticky="n", padx=5, pady=0)

        self.fr_lid_value_label = customtkinter.CTkLabel(master=self.preset_frame_right,
                                                         text='°C',
                                                         text_font=("Roboto Medium", -16),
                                                         text_color='orange')
        self.fr_lid_value_label.grid(row=2, column=0, sticky="n", padx=0, pady=0)

        self.fr_plate_label = customtkinter.CTkLabel(master=self.preset_frame_right,
                                                     text="Plate Preset Temperature °C",
                                                     text_font=("Roboto Medium", -16),
                                                     text_color='white')
        self.fr_plate_label.grid(row=3, column=0, sticky="n", padx=5, pady=0)

        self.fr_plate_value_label = customtkinter.CTkLabel(master=self.preset_frame_right,
                                                           text="°C",
                                                           text_font=("Roboto Medium", -16),
                                                           text_color='light blue')
        self.fr_plate_value_label.grid(row=4, column=0, sticky="n", padx=5, pady=0)

        # ---------------------------- Parameter frame ----------------------------------------------------

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

        # frame left

        self.param_left_title = customtkinter.CTkLabel(master=self.param_frame_left,
                                                       text="Import Protocol CSV file",
                                                       text_font=("Roboto Medium", -20),
                                                       text_color='White')
        self.param_left_title.grid(row=0, column=0, columnspan=2, sticky="nswe", padx=5, pady=10)

        self.param_left_title = customtkinter.CTkLabel(master=self.param_frame_left,
                                                       text="Import Protocol CSV file",
                                                       text_font=("Roboto Medium", -20),
                                                       text_color='White')
        self.param_left_title.grid(row=0, column=0, columnspan=2, sticky="nswe", padx=5, pady=10)

        self.path_label = customtkinter.CTkLabel(master=self.param_frame_left,
                                                 text="",
                                                 text_font=("Roboto Medium", -13),
                                                 text_color='White')
        self.path_label.grid(row=1, column=1, columnspan=1, sticky="ew", padx=5, pady=10)
        self.experiment_name_label = customtkinter.CTkEntry(master=self.param_frame_left,
                                                            placeholder_text='Experiment Name',
                                                            text_font=("Roboto Medium", -13),
                                                            text_color='White')
        self.experiment_name_label.grid(row=1, column=0, columnspan=1, sticky="ew", padx=5, pady=10)
        self.experiment_name_label.bind("<KeyRelease>", self.run_ready_check)


        self.import_button = customtkinter.CTkButton(master=self.param_frame_left,
                                                     text="Import",
                                                     text_font=("Roboto Medium", -20),
                                                     text_color='White', width=150,
                                                     command=self.select_file)
        self.import_button.grid(row=2, column=0, columnspan=2, sticky="n", padx=5, pady=5)

        self.run_button = customtkinter.CTkButton(master=self.param_frame_left,
                                                  text="Run Protocol",
                                                  text_font=("Roboto Medium", -20), fg_color='grey',
                                                  text_color='White', width=250, height=50, state='disabled',
                                                  command=threading.Thread(target=self.run).start)

        self.run_button.grid(row=3, column=0, columnspan=2, sticky="n", padx=5, pady=5)

        # param right
        self.param_right_title = customtkinter.CTkLabel(master=self.param_frame_right,
                                                        text="Protocol info",
                                                        text_font=("Roboto Medium", -20),
                                                        text_color='White')
        self.param_right_title.grid(row=0, column=0, sticky="n", padx=5, pady=0)

        self.protocol_label = customtkinter.CTkLabel(master=self.param_frame_right,
                                                     text='',
                                                     text_font=("Roboto Medium", -12),
                                                     text_color='White',
                                                     justify='left')
        self.protocol_label.grid(row=1, column=0, sticky="n", padx=5, pady=0)

        self.tc_protocol = {}

    def run(self):
        self.param_frame_left = customtkinter.CTkFrame(master=self.param_frame)
        self.param_frame_left.grid(row=0, column=0, sticky="nswe", padx=5, pady=10)
        self.param_frame_left.rowconfigure((0, 1, 2, 3, 4), weight=1)
        self.param_frame_left.columnconfigure((0, 1, 2, 3), weight=1)

        self.running_label = customtkinter.CTkLabel(master=self.param_frame_left)
        self.running_label.grid(row=0, column=0, columnspan=3, sticky="n", padx=5, pady=5)

        self.current_lid_label = customtkinter.CTkLabel(master=self.param_frame_left,
                                                        text='Current Lid \nTemperature',
                                                        text_font=("Roboto Medium", -18),
                                                        text_color='grey',
                                                        justify='center')
        self.current_lid_label.grid(row=1, column=0, sticky="n", padx=10, pady=5)

        self.current_lid_value_label = customtkinter.CTkLabel(master=self.param_frame_left,
                                                              text='',
                                                              text_font=("Roboto Medium", -24),
                                                              text_color='orange',
                                                              justify='center')
        self.current_lid_value_label.grid(row=2, column=0, sticky="n", padx=10, pady=5)

        self.current_plate_label = customtkinter.CTkLabel(master=self.param_frame_left,
                                                          text='Current Plate \nTemperature',
                                                          text_font=("Roboto Medium", -18),
                                                          text_color='grey',
                                                          justify='center')
        self.current_plate_label.grid(row=1, column=1, sticky="n", padx=10, pady=5)

        self.current_plate_value_label = customtkinter.CTkLabel(master=self.param_frame_left,
                                                                text='',
                                                                text_font=("Roboto Medium", -24),
                                                                text_color='light blue',
                                                                justify='center')
        self.current_plate_value_label.grid(row=2, column=1, sticky="n", padx=10, pady=5)

        self.step_time_label = customtkinter.CTkLabel(master=self.param_frame_left,
                                                      text='Step Time \nRemaining',
                                                      text_font=("Roboto Medium", -18),
                                                      text_color='grey',
                                                      justify='center')
        self.step_time_label.grid(row=1, column=2, sticky="n", padx=10, pady=5)

        self.step_time_value_label = customtkinter.CTkLabel(master=self.param_frame_left,
                                                            text='',
                                                            text_font=("Roboto Medium", -24),
                                                            text_color='light green',
                                                            justify='center')
        self.step_time_value_label.grid(row=2, column=2, sticky="n", padx=10, pady=5)

        self.stop_protocol_button = customtkinter.CTkButton(master=self.param_frame_left, width=250, height=35,
                                                            text='Stop Protocol', fg_color='dark red',
                                                            command=self.are_you_sure)
        self.stop_protocol_button.grid(row=3, column=1, sticky="n", padx=10, pady=5)

        self.deactivate_button.configure(state='disabled', fg_color='grey')
        self.lid_entry.configure(state='disabled')
        self.plate_entry.configure(state='disabled')
        self.lid_button.configure(state='disabled', fg_color='grey')
        self.plate_button.configure(state='disabled', fg_color='grey')

        run_protocol(self.tc_protocol, self.running_label, self.current_lid_value_label, self.current_plate_value_label,
                     self.step_time_value_label, self.experiment_name_label.get())

    def run_ready_check(self, event=None):
        print(len(self.experiment_name_label.get()))
        if len(self.tc_protocol) > 0 and len(self.experiment_name_label.get())>5:
            self.run_button.configure(state='normal', fg_color='dark red')
        else:
            self.run_button.configure(state='disabled', fg_color='grey')
    def select_file(self):
        self.wm_attributes('-topmost', 1)
        try:
            txt = (fd.askopenfile(parent=self, initialdir=''))
            self.path_label.configure(text=txt.name)
            self.tc_protocol = protocol_dict(txt.name)
            #self.run_button.configure(state='enabled')
            self.run_ready_check()

            string = ""
            with open(txt.name, 'r') as read_file:
                csv_read = csv.reader(read_file, delimiter=',')
                step_count = 1
                stage_count = 1
                for line in csv_read:
                    if line[0] == 'CYCLES':
                        string += f'\n\n\t\tStage - {stage_count}\nCycles - {line[1]}\nStep    Plate_temp    Time(seconds)    Set Lid Target\n'
                        step_count = 1
                        stage_count += 1
                    elif line[0] == 'STEP':
                        if line[3] == '':
                            time = 'Hold'
                        else:
                            time = line[3]
                        string += f'  {step_count}                {line[2]}                        {time}' \
                                  f'                                  {line[4]}\n'
                        step_count += 1
                    elif line[0] == 'DEACTIVATE_ALL':
                        string += f'  {step_count}                                 Deactivate All\n'
                        step_count += 1
                    elif line[0] == 'END&GRAPH':
                        string += f'  {step_count}                                  End Protocol\n'
                self.protocol_label.configure(text=string, text_font=("Roboto Medium", -12), text_color='white',
                                              justify='left')



        except AttributeError:
            self.path_label.configure(text='No File Chosen.', text_font=("Roboto Medium", -16))
            self.protocol_label.configure(text='No File Chosen', text_font=("Roboto Medium", -16))
            self.tc_protocol = {}

        except KeyError:
            self.protocol_label.configure(
                text='Input File Error\n\nPlease check ordering of the events\n\nExample\nCycles -->{Step/Deactivate}\nCycles -->{Step/Deactivate/End}.',
                text_font=("Roboto Medium", -20), text_color='yellow', justify='center')
            self.tc_protocol = {}

        except ValueError:
            self.protocol_label.configure(
                text='Input File Error\n\nEnsure file is in CSV format.\nPlease check ordering of the events\n\nExample\nCycles -->{Step/Deactivate}\nCycles -->{Step/Deactivate/End}.',
                text_font=("Roboto Medium", -20), text_color='yellow', justify='center')
            self.tc_protocol = {}

    def are_you_sure(self):
        self.are_you_sure_label = customtkinter.CTkLabel(master=self.param_frame_left,
                                                         text='Stop Protocol?\nAre You Sure?',
                                                         text_font=("Roboto Medium", -20), width=300,
                                                         text_color='yellow', justify='center')
        self.are_you_sure_label.grid(row=3, column=1, sticky="n", padx=10, pady=5)

        self.stop_button = customtkinter.CTkButton(master=self.param_frame_left, text='STOP',
                                                   text_font=("Roboto Medium", -20), fg_color='dark red',
                                                   text_color='white', command=self.deactivate_all)
        self.stop_button.grid(row=4, column=1, columnspan=2, sticky="w", padx=20, pady=10)

        self.cancel_button = customtkinter.CTkButton(master=self.param_frame_left, text='Cancel',
                                                     text_font=("Roboto Medium", -20), text_color='white',
                                                     command=self.cancel)
        self.cancel_button.grid(row=4, column=0, columnspan=2, sticky="e", padx=20, pady=10)

    def deactivate_all(self):
        deactivate_all()
        self.fr_plate_value_label.configure(text='°C')
        self.fr_lid_value_label.configure(text='°C')

    def set_plate_temp(self):
        value = self.plate_entry.get()
        set_plate_temperature(value)
        self.fr_plate_value_label.configure(text=value + '°C')

    def set_lid_temp(self):
        value = self.lid_entry.get()
        set_lid_temperature(value)
        self.fr_lid_value_label.configure(text=value + '°C')

    def cancel(self):
        self.are_you_sure_label.destroy()
        self.stop_button.destroy()
        self.cancel_button.destroy()

    def opn_lid(self):
        open_lid()

    def cls_lid(self):
        close_lid()

    def on_closing(self, event=0):
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
