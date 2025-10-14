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

        self.title("HelixShaker")
        self.geometry(f"{App.WIDTH}x{App.HEIGHT}")
        self.state('zoomed')
        self.iconbitmap('HelixCycler.ico')
        self.protocol("WM_DELETE_WINDOW", self.on_closing)  # call .on_closing() when app gets closed
        self.bg = PhotoImage(file='HelixCycler.png')
        # ============ create two frames ============

        # configure grid layout (4 rows)
        self.grid_columnconfigure(0, weight=1)

        #self.grid_rowconfigure(0, weight=1)
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
                                              text="HelixShaker - OT Heater-Shaker app",
                                              text_font=("Roboto Medium", -24))  # font name and size in px
        self.title_label.grid(row=0, column=0, pady=10, padx=5, sticky="nesw")

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

        #self.preset_frame_left.grid_columnconfigure(5, weight=2)


        self.preset_frame_left_title = customtkinter.CTkLabel(master=self.preset_frame_left,
                                              text="Preset temperatures",
                                              text_font=("Roboto Medium", -20))
        self.preset_frame_left_title.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)



        self.plate_label = customtkinter.CTkLabel(master=self.preset_frame_left,
                                                              text="Set Plate Temperature °C",
                                                              text_font=("Roboto Medium", -16),
                                                              text_color='grey')
        self.plate_label.grid(row=1, column=1, sticky="n", padx=5, pady=0)

        self.plate_entry = customtkinter.CTkEntry(master=self.preset_frame_left, width=90, justify='center', fg_color='black', placeholder_text='°C', placeholder_text_color='grey')
        self.plate_entry.grid(row=2, column=1, sticky="n", padx=5, pady=0)



        self.preset_frame_left_shake_label = customtkinter.CTkLabel(master=self.preset_frame_left,
                                                                    text=" Set Shake Speed RPM",
                                                                    text_font=("Roboto Medium", -16),
                                                                    text_color='grey')
        self.preset_frame_left_shake_label.grid(row=1, column=0, sticky="n", padx=5, pady=0)

        self.shake_entry = customtkinter.CTkEntry(master=self.preset_frame_left, width=90, justify='center', fg_color='black', placeholder_text='RPM', placeholder_text_color='grey')
        self.shake_entry.grid(row=2, column=0, sticky="n", padx=5, pady=0)

        self.plate_button = customtkinter.CTkButton(master=self.preset_frame_left, text='Set Plate Temp', command=self.set_plate_temp)
        self.plate_button.grid(row=3, column=1, columnspan=1, rowspan=2, pady=0, padx=5, sticky="n")

        self.shake_button = customtkinter.CTkButton(master=self.preset_frame_left, text='Set Shake Speed', command=self.set_shake_speed)
        self.shake_button.grid(row=3, column=0, columnspan=1, rowspan=1, pady=0, padx=5, sticky="n")

        self.deactivate_button = customtkinter.CTkButton(master=self.preset_frame_left, width=250, height=35, text='Deactivate all', fg_color='dark red', command=self.deactivate_all)
        self.deactivate_button.grid(row=2, column=3, columnspan=1, rowspan=1, pady=10, padx=5, sticky="n")

        self.latch_open = customtkinter.CTkButton(master=self.preset_frame_left, width=250, height=35,
                                                         text='Open Latch',
                                                         command=self.open_ltch)
        self.latch_open.grid(row=2, column=2, columnspan=1, rowspan=1, pady=10, padx=5, sticky="n")

        self.latch_close = customtkinter.CTkButton(master=self.preset_frame_left, width=250, height=35,
                                                  text='Close Latch',
                                                  command=self.close_ltch)
        self.latch_close.grid(row=3, column=2, columnspan=1, rowspan=1, pady=10, padx=5, sticky="n")
        # ------------------------Frame Right---------------------------------------

       


    


    def deactivate_all(self):
        deactivate_shaker()




    def set_plate_temp(self):
        value = self.plate_entry.get()
        set_plate_temperature(value)



    def set_shake_speed(self):
        value = self.shake_entry.get()
        set_shake_speed(value)

    def open_ltch(self):
        open_latch()

    def close_ltch(self):
        close_latch()


    def cancel(self):
        self.are_you_sure_label.destroy()
        self.stop_button.destroy()
        self.cancel_button.destroy()


    def on_closing(self, event=0):
        self.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()
