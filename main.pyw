from tkinter import *
from PIL import Image, ImageTk
from base64 import decodebytes
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
from threading import Thread
from io import BytesIO
import urllib.request
import subprocess
import paramiko
import calendar
import zipfile
import ftplib
import pysftp
import gzip
import glob
import json
import nbt
import sys
import os

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0]))) # Si un raccourcie est créer, alors le programme se lance dans son dossier malgré les indications.

class Main:
    def __init__(self):
        self.root = Tk()
        self.root.title("inspecteur de logs")
        try: self.root.iconbitmap("icon.ico")
        except: pass
        self.root.resizable(width=False, height=False)

        self.frame_game_dir = Frame(self.root)  # Menu de sélection du dossier de jeu
        self.frame_game_dir.grid(row=1, column=1)

        Label(self.frame_game_dir, text="Sélectionné votre dossier de jeu").grid(row=1, column=1, columnspan=2)
        self.entry_game_dir = Entry(self.frame_game_dir, width=50)
        self.entry_game_dir.grid(row=2, column=1)
        self.entry_game_dir.insert(0, "%s\\.minecraft" % os.getenv("APPDATA"))
        Button(self.frame_game_dir, text="...", command=self.select_game_dir, relief = RIDGE).grid(row=2, column=2)

        def option_calendar():
            self.frame_button_game_dir_action.grid_forget()
            self.progressbar_game_dir.grid(row=3, column=1, columnspan=2, sticky="NEWS")

            if self.update_log_data() != -1: self.update_calendar()

            self.frame_button_game_dir_action.grid(row=3, column=1, columnspan=2, sticky="NEWS")
            self.progressbar_game_dir.grid_forget()

        self.frame_button_game_dir_action = Frame(self.frame_game_dir)
        self.frame_button_game_dir_action.grid(row = 3, column = 1, columnspan = 2, sticky = "NEWS")
        Button(self.frame_button_game_dir_action, text="Recherche", command=lambda: Thread(target = option_calendar).start(), relief=RIDGE).grid(row = 1, column = 1)
        Button(self.frame_button_game_dir_action, text="Recherche avancée", command=self.search_log, relief=RIDGE).grid(row=1, column=2)
        Button(self.frame_button_game_dir_action, text="Connexion via FTP...", command=self.connect_ftp, relief=RIDGE).grid(row=1, column=3)

        self.progressbar_game_dir = ttk.Progressbar(self.frame_game_dir)

        self.variable_use_SFTP = BooleanVar(value=True)

        self.variable_search_screenshot_only = BooleanVar(value = False)
        self.variable_search_replay_only = BooleanVar(value = False)

        self.frame_calendar_log = Frame(self.root)

        self.frame_calendar_year_panel = Frame(self.frame_calendar_log)
        self.frame_calendar_year_panel.grid(row=1, column=1, columnspan=3, sticky = "EW")
        self.frame_calendar_year_panel.columnconfigure(2, weight = 1)

        self.label_calendar_year = Label(self.frame_calendar_year_panel, text = "YEAR", font = ("System", 30))
        self.label_calendar_year.grid(row=1, column=2, sticky = "NEWS")
        self.button_calendar_year_before = Button(self.frame_calendar_year_panel, text = "<", relief = SOLID)
        self.button_calendar_year_before.grid(row=1, column=1, sticky = "NEWS")
        self.button_calendar_year_after = Button(self.frame_calendar_year_panel, text=">", relief = SOLID)
        self.button_calendar_year_after.grid(row=1, column=3, sticky = "NEWS")

        self.frame_calendar_month_panel = Frame(self.frame_calendar_log)
        self.frame_calendar_month_panel.columnconfigure(2, weight = 1)

        self.month_id_to_name = {
            1: "Janvier",
            2: "Février",
            3: "Mars",
            4: "Avril",
            5: "Mai",
            6: "Juin",
            7: "Juillet",
            8: "Août",
            9: "Septembre",
            10: "Octobre",
            11: "Novembre",
            12: "Décembre"
        }

        self.button_calendar_month = Button(self.frame_calendar_month_panel, text="MONTH", font=("System", 24), relief = FLAT)
        self.button_calendar_month.grid(row=2, column=2, sticky = "NEWS")
        self.button_calendar_month_before = Button(self.frame_calendar_month_panel, text="<", relief = SOLID)
        self.button_calendar_month_before.grid(row=2, column=1, sticky = "NEWS")
        self.button_calendar_month_after = Button(self.frame_calendar_month_panel, text=">", relief = SOLID)
        self.button_calendar_month_after.grid(row=2, column=3, sticky = "NEWS")

        self.labelframe_calendar = LabelFrame(self.frame_calendar_log)
        self.labelframe_calendar.grid(row=3, column=1, columnspan=3)

        self.dict_button_day_calendar = []
        for day in range(7 * 5):
            self.dict_button_day_calendar.insert(day, Button(self.labelframe_calendar, text=day, width=4, height=2, relief=RIDGE))

        self.dict_button_month_calendar = []
        for month in range(1, 12 + 1):
            self.dict_button_month_calendar.insert(month, Button(self.labelframe_calendar, text=month, width = 6, height=3, relief=RIDGE))

        self.button_global_statistic = Button(self.frame_calendar_log, text = "Statistiques globales", relief=RIDGE)
        self.button_global_statistic.grid(row=4, column=1, columnspan=3, sticky = "NEWS")

        self.frame_day_log = Frame(self.root)

        self.label_day_total_log = Label(self.frame_day_log)
        self.label_day_total_log.grid(row = 1, column = 1, columnspan = 2)

        self.frame_day_log_button = LabelFrame(self.frame_day_log)
        self.frame_day_log_button.grid(row = 2, column = 1)
        self.dict_button_day_log = []

        self.canvas_day_log_historic = Canvas(self.frame_day_log, width = 80, height = 300, bg = "lightgray")
        self.canvas_day_log_historic.grid(row=2, column=2)

        self.frame_log_read = Frame(self.root)

        self.label_log_read_metadata = Label(self.frame_log_read, text = "FILE_NAME, DATE")
        self.label_log_read_metadata.grid(row = 1, column = 1, columnspan = 2)

        self.frame_log_read_format = LabelFrame(self.frame_log_read)
        self.frame_log_read_format.grid(row = 2, column = 1, columnspan = 2)

        self.last_format_used = "chat"
        self.button_log_read_format_raw = Button(self.frame_log_read_format, text = "Brut", relief = RIDGE)
        self.button_log_read_format_raw.grid(row = 1, column = 1)
        self.button_log_read_format_chat = Button(self.frame_log_read_format, text = "Chat", relief = RIDGE)
        self.button_log_read_format_chat.grid(row = 1, column = 2)
        self.button_log_read_format_server = Button(self.frame_log_read_format, text="Serveur", relief = RIDGE)
        self.button_log_read_format_server.grid(row = 1, column = 3)

        self.variable_log_read_search = StringVar()
        self.entry_log_read_search = Entry(self.frame_log_read, font = ("System", 12), width = 30, fg="gray70")
        self.entry_log_read_search.insert(0, "Faire une recherche")
        self.entry_log_read_search.grid(row = 3, column = 1, columnspan = 2, sticky = "E")
        self.entry_log_read_search.bind("<Key>", self.reset_log_read_search)

        self.scrollbar_text_log_read = Scrollbar(self.frame_log_read)
        self.scrollbar_text_log_read.grid(row = 4, column = 2, sticky = "NS")

        self.text_log_read_data = Text(self.frame_log_read, width = 100, height = 30, yscrollcommand = self.scrollbar_text_log_read.set)
        self.text_log_read_data.grid(row=4, column=1,sticky = "NEWS")

        self.text_log_read_data.tag_config('chat_message', background="gray10", foreground="white", font=("System", 16))
        self.text_log_read_data.tag_config('server_connection', background="red", foreground="white", font=("System", 16))
        self.text_log_read_data.tag_config('server_warn', background="orange", foreground="white", font=("System", 16))

        self.text_log_read_data.tag_config('§0', background="gray30", foreground="black")
        self.text_log_read_data.tag_config('§1', background="gray10", foreground="darkblue")
        self.text_log_read_data.tag_config('§2', background="gray10", foreground="darkgreen")
        self.text_log_read_data.tag_config('§3', background="gray10", foreground="turquoise")
        self.text_log_read_data.tag_config('§4', background="gray10", foreground="darkred")
        self.text_log_read_data.tag_config('§5', background="gray10", foreground="darkviolet")
        self.text_log_read_data.tag_config('§6', background="gray10", foreground="gold")
        self.text_log_read_data.tag_config('§7', background="gray10", foreground="lightgray")
        self.text_log_read_data.tag_config('§8', background="gray10", foreground="gray")
        self.text_log_read_data.tag_config('§9', background="gray10", foreground="royalblue")
        self.text_log_read_data.tag_config('§a', background="gray10", foreground="lime")
        self.text_log_read_data.tag_config('§b', background="gray10", foreground="cyan")
        self.text_log_read_data.tag_config('§c', background="gray10", foreground="red")
        self.text_log_read_data.tag_config('§d', background="gray10", foreground="magenta")
        self.text_log_read_data.tag_config('§e', background="gray10", foreground="yellow")
        self.text_log_read_data.tag_config('§l', font=("System", 16, "bold"))
        self.text_log_read_data.tag_config('§m', overstrike = True)
        self.text_log_read_data.tag_config('§n', underline = True)
        self.text_log_read_data.tag_config('§o', font=("System italic", 16))
        self.text_log_read_data.tag_config('§r', background="gray10", foreground="white", font=("System", 16), overstrike = False, underline = False)


        self.scrollbar_text_log_read.config(command=self.text_log_read_data.yview)

        self.frame_screenshot_intersect = LabelFrame(self.root, text = "Capture d'écran")

        self.scrollbar_canvas_screenshot = Scrollbar(self.frame_screenshot_intersect)
        self.scrollbar_canvas_screenshot.grid(row = 1, column = 2, sticky = "NS")

        self.canvas_screenshot = Canvas(self.frame_screenshot_intersect, height = 950, bg = "lightgray",
                                        yscrollcommand = self.scrollbar_canvas_screenshot.set)
        self.canvas_screenshot.grid(row = 1, column = 1, sticky = "NS")
        self.scrollbar_canvas_screenshot.config(command=self.canvas_screenshot.yview)

        self.frame_replay_intersect = LabelFrame(self.root, text="ReplayMod")

        self.scrollbar_canvas_replay = Scrollbar(self.frame_replay_intersect)
        self.scrollbar_canvas_replay.grid(row=1, column=2, sticky="NS")

        self.canvas_replay = Canvas(self.frame_replay_intersect, height=950, bg="lightgray",
                                        yscrollcommand=self.scrollbar_canvas_replay.set)
        self.canvas_replay.grid(row=1, column=1, sticky="NS")
        self.scrollbar_canvas_replay.config(command=self.canvas_replay.yview)

        self.frame_player_intersect = LabelFrame(self.root, text="Joueurs")

        self.scrollbar_canvas_player = Scrollbar(self.frame_player_intersect)
        self.scrollbar_canvas_player.grid(row=1, column=2, sticky="NS")

        self.canvas_player = Canvas(self.frame_player_intersect, height=950, bg="lightgray",
                                    yscrollcommand=self.scrollbar_canvas_player.set)
        self.canvas_player.grid(row=1, column=1, sticky="NS")
        self.scrollbar_canvas_player.config(command=self.canvas_player.yview)

    def reset_log_read_search(self, event = None):
        self.variable_log_read_search.set("")
        self.entry_log_read_search.config(fg = "black", textvariable = self.variable_log_read_search)
        self.entry_log_read_search.bind("<Key>", lambda event: self.update_read_log_format())

    def select_game_dir(self):
        """Demande à l'utilisateur de sélectionner son dossier de jeu (celui dans lequel se trouve le dossier /logs/)"""
        game_dir = filedialog.askdirectory(initialdir=lambda: self.entry_game_dir.get())
        if os.path.exists(game_dir):
            self.entry_game_dir.delete(0, END)
            self.entry_game_dir.insert(0, os.path.realpath(game_dir))

    def update_log_data(self, func_log_sort_selection = None, ftp_log_list = None):
        """Met à jour les métadonnées des logs en fonction du dossier de jeu sélectionné"""
        self.log_metadata = {}  # dictionnaire contenant les métadonnées des logs
        self.latest_log_year = -1
        self.latest_log_month = -1
        self.oldest_log_year = -1
        self.oldest_log_month = -1
        self.total_log = 0
        self.max_log_total = -1
        self.max_log_total_day = -1
        self.max_log_total_month = -1
        self.path = self.entry_game_dir.get()

        self.canvas_player.delete(ALL)
        canvas_width = self.canvas_screenshot.winfo_width()

        self.world_name = None
        self.player_list = []

        if not(ftp_log_list):
            if os.path.exists(self.path + "\\server.properties"):
                self.last_format_used = "server"
                with open(self.path + "\\server.properties", "r") as file:
                    self.world_name = file.read().split("level-name=")[-1].split("\n")[0]
                    self.frame_player_intersect.grid(row=1, column=5, rowspan=3, sticky="NS")
                    self.frame_replay_intersect.grid_forget()
                    self.frame_screenshot_intersect.grid_forget()

                if os.path.exists(self.path + "\\%s\\playerdata\\" % self.world_name):
                    self.player_list = os.listdir(self.path + "\\%s\\playerdata\\" % self.world_name)

            else: self.frame_player_intersect.grid_forget()

        else:
            for tentative in range(5):
                try:
                    if not(self.variable_use_SFTP.get()):
                        server_properties_data = BytesIO()
                        self.server_FTP.retrbinary("RETR server.properties", server_properties_data.write)
                        server_properties_data.seek(0)
                    else:
                        server_properties_data = self.server_FTP.open("server.properties", "rb")

                    self.world_name = server_properties_data.read().decode().split("level-name=")[-1].split("\n")[0]
                    self.frame_player_intersect.grid(row=1, column=5, rowspan=3, sticky="NS")
                    self.frame_replay_intersect.grid_forget()
                    self.frame_screenshot_intersect.grid_forget()

                    break

                except Exception as e: print("Tentative %i (server.properties) (%s)" % (tentative, str(e)))

            for tentative in range(5):
                try:
                    if not(self.variable_use_SFTP.get()): player_file_list = self.server_FTP.nlst(self.world_name.replace("\r", "") + "/playerdata/")
                    else: player_file_list = self.server_FTP.listdir(self.world_name + "/playerdata/")

                    self.player_list = [os.path.basename(x) for x in player_file_list]
                    self.progressbar_messagebox_ftp.config(maximum=len(self.player_list) + 1)
                    break
                except Exception as e: print("Tentative %i (playerdata) (%s)" % (tentative, str(e)))

        if not(ftp_log_list):
            if not (os.path.exists(self.path + "\\logs\\")):
                messagebox.showerror("Erreur", "Ce dossier de jeu ne contient pas de dossier /logs/")
                return -1
            list_log = glob.glob(self.path + "\\logs\\" + "*.log.gz")

        else: list_log = ftp_log_list

        self.progressbar_game_dir.config(maximum = len(list_log) + len(self.player_list))

        for file in list_log:
            log_date = os.path.basename(file).split("-")
            if file[-7:] == ".log.gz" and len(log_date) == 4: # Vérifie si le fichier en log.gz est bien un log de jeu
                year, month, day, part = int(log_date[0]), int(log_date[1]), int(log_date[2]), int(log_date[3].split(".")[0])  # clé du dictionnaire

                if func_log_sort_selection != None:
                    if not(func_log_sort_selection(file = file)): continue

                    if self.variable_search_screenshot_only.get():
                        if not(self.find_screenshot(year,month,day, 0, 24 * 3600) > 0): # Timestamp Max # Si il n'a pas de screenshot associé.
                            continue

                    if self.variable_search_replay_only.get():
                        if not(self.find_replay(year,month,day, 0, 24 * 3600) > 0): # Timestamp Max # Si il n'a pas de replay associé.
                            continue


                if not(year in self.log_metadata):
                    _day_dict = {"total": 0}
                    _month_dict = {}
                    for _month in range(1, 12 + 1):
                        for _day in range(1, calendar.monthrange(year, _month)[1] + 1):
                            _day_dict.update({_day: 0})
                        _month_dict.update({_month: _day_dict.copy()})

                    self.log_metadata.update({year: _month_dict.copy()})
                    del _day_dict, _month_dict

                self.total_log += 1
                self.log_metadata[year][month][day] += 1
                self.log_metadata[year][month]["total"] += 1
                if self.max_log_total < self.log_metadata[year][month][day]: self.max_log_total = self.log_metadata[year][month][day]
                if self.max_log_total_day < self.log_metadata[year][month][day]: self.max_log_total_day = self.log_metadata[year][month][day]
                if self.max_log_total_month < self.log_metadata[year][month]["total"]: self.max_log_total_month = self.log_metadata[year][month]["total"]

                if self.latest_log_year == -1 or self.latest_log_year <= year:
                    if self.latest_log_month == -1 or self.latest_log_month <= month or self.latest_log_year < year:
                        self.latest_log_month = month
                    self.latest_log_year = year

                if self.oldest_log_year == -1 or self.oldest_log_year >= year:
                    if self.oldest_log_month == -1 or self.oldest_log_month >= month or self.oldest_log_year > year:
                        self.oldest_log_month = month
                    self.oldest_log_year = year

            self.progressbar_game_dir.step()

        index = 0
        for index, player_uuid in enumerate(self.player_list):
            try:
                request = urllib.request.urlopen("https://api.mojang.com/user/profiles/%s/names" % player_uuid.replace("-", "").split(".")[0])
                text, font = json.loads(request.read())[-1]["name"], ("System", 18)
            except: text, font = player_uuid, ("System", 16)

            self.canvas_player.create_rectangle(0, 100 * (index), canvas_width, 100 * (index + 1), fill = "gray80", tags = "player-%i" % index)
            self.canvas_player.create_text(canvas_width / 2, 100 * (index + 1) - 50, text=text, font=font, tags = "player-%i" % index)
            self.canvas_player.tag_bind("player-%i" % index, "<Button-1>", lambda event, p=player_uuid: self.player_nbt_inventory(player_uuid=p, ftp_log_list=ftp_log_list))

            if ftp_log_list: self.progressbar_messagebox_ftp.step()
            self.progressbar_game_dir.step()

        self.canvas_player.config(scrollregion=self.canvas_player.bbox(ALL))

    def update_calendar(self, year = None, month = None, mode = "day", ftp_log_list = None):
        """Met à jour l'interface du calendrier"""

        self.frame_calendar_log.grid(row=2, column=1)

        if not(year): year = self.latest_log_year
        if not(month): month = self.latest_log_month
        try: day_offset, day_number = calendar.monthrange(year, month)
        except calendar.IllegalMonthError:
            return -1

        self.label_calendar_year.config(text = str(year))
        self.button_calendar_month.config(text = self.month_id_to_name[month])

        if year > self.oldest_log_year: command = lambda: self.update_calendar(year = year - 1, month = 12, mode = mode, ftp_log_list = ftp_log_list)
        else: command = lambda: "pass"
        self.button_calendar_year_before.config(command = command)
        if year < self.latest_log_year: command = lambda: self.update_calendar(year = year + 1, month = 1, mode = mode, ftp_log_list = ftp_log_list)
        else: command = lambda: "pass"
        self.button_calendar_year_after.config(command = command)
        if month > 1: command = lambda: self.update_calendar(year = year, month = month - 1, ftp_log_list = ftp_log_list)
        else: command = lambda: "pass"
        self.button_calendar_month_before.config(command = command)
        if month < 12: command = lambda: self.update_calendar(year = year, month = month + 1, ftp_log_list = ftp_log_list)
        else: command = lambda: "pass"
        self.button_calendar_month_after.config(command = command)

        for button in self.dict_button_month_calendar: button.grid_forget()
        for button in self.dict_button_day_calendar: button.grid_forget()

        if mode == "day":
            self.frame_calendar_month_panel.grid(row=2, column=1, columnspan=3, sticky = "EW")
            self.button_calendar_month.config(command = lambda year=year, month=month: self.update_calendar(year, month, mode = "month"))

            for day in range(1, day_number + 1): # Pour chaque jour dans le mois
                day_pos = day + day_offset - 1
                command = lambda: "pass"

                if not(year in self.log_metadata): # Si l'année même ne contient pas de log
                    bg = "lightgray"
                elif self.log_metadata[year][month][day] > 0: # Si il a au moins 1 log ce jour
                    bg = "#00%sFF" % hex(255 - (self.log_metadata[year][month][day] * 128 // self.max_log_total_day))[2:].zfill(2)
                    command = lambda year=year, month=month, day=day, cll=ftp_log_list: self.update_day(year, month, day, cll)
                else:
                    bg = "lightgray"

                self.dict_button_day_calendar[day].config(text=day, bg=bg, command=command)
                self.dict_button_day_calendar[day].grid(row=day_pos // 7, column=day_pos % 7)

        if mode == "month":
            self.frame_calendar_month_panel.grid_forget()
            self.button_calendar_month.config(command = lambda year=year, month=month: self.update_calendar(year, month, mode = "day"))

            for index, month_button in enumerate(self.dict_button_month_calendar):
                month_button.grid(row=index//3,column=index%3)
                if not (year in self.log_metadata): bg = "lightgray"
                elif self.log_metadata[year][index + 1]["total"] > 0:
                    bg = "#00%sFF" % hex(255 - (self.log_metadata[year][index + 1]["total"] * 128 // self.max_log_total_month))[2:].zfill(2)
                else: bg = "lightgray"
                month_button.config(bg = bg, command = lambda month = index + 1: self.update_calendar(year = year, month = month, mode = "day"))


        self.button_global_statistic.config(command = self.global_statistic)

    def timestamp_to_hms(self, timestamp):
        hour, rest = divmod(timestamp, 3600)
        min, sec = divmod(rest, 60)
        return hour, min, sec

    def hms_to_timestamp(self, hour, min, sec):
        return hour * 3600 + min * 60 + sec

    def update_day(self, year, month, day, ftp_log_list = None):
        """Met à jour l'interface affichant les différents logs"""
        for button in self.dict_button_day_log: button.destroy()
        self.canvas_day_log_historic.delete(ALL)
        canvas_height, canvas_width = self.canvas_day_log_historic.winfo_height(), self.canvas_day_log_historic.winfo_width()

        step_time_offset = canvas_height / 24
        for step in range(1, 24 + 1):
            self.canvas_day_log_historic.create_line(0, step_time_offset * step, canvas_width, step_time_offset * step, fill = "gray65")

        self.frame_day_log.grid(row = 1, column = 2, rowspan = 2)
        self.label_day_total_log.config(text = "fichier logs trouvé : %i" % self.log_metadata[year][month][day])

        if not(ftp_log_list): list_log = glob.iglob(self.path + "\\logs\\" + "%04i-%02i-%02i-*.log.gz" % (year, month, day))
        else:
            list_log = []
            for log in ftp_log_list:
                if "%04i-%02i-%02i" % (year, month, day) in log:
                    list_log.append(log)

        for index, file in enumerate(list_log):

            self.dict_button_day_log.append(Button(self.frame_day_log_button, text = os.path.basename(file), command = lambda f=file: self.update_log(f,ftp_log_list=ftp_log_list)))
            self.dict_button_day_log[-1].grid(row = index + 2, column = 1)

            try:
                if not(ftp_log_list):
                    with gzip.open(file) as log_file:
                        log_line = log_file.readlines()
                else:
                    for tentative in range(5):
                        try:
                            if not(self.variable_use_SFTP.get()):
                                log_file_data = BytesIO()
                                self.server_FTP.retrbinary("RETR %s" % file, log_file_data.write)
                                log_file_data.seek(0)
                            else: log_file_data = self.server_FTP.open("logs/%s" % file, "rb")

                            with gzip.GzipFile(fileobj = log_file_data) as log_file:
                                log_line = log_file.readlines()

                            break
                        except: print("Tentative %i" % tentative)

                first_time = log_line[0][1:9].decode("cp1252")
                for index in range(1, len(log_line)):
                    last_time_line = log_line[-index].decode("cp1252")
                    if last_time_line[0] == "[" and last_time_line[9] == "]":
                        last_time = last_time_line[1:9]
                        break

                first_hour, first_min, first_sec = (int(x) for x in first_time.split(":"))
                first_timestamp = self.hms_to_timestamp(first_hour,first_min,first_sec)
                last_hour, last_min, last_sec = (int(x) for x in last_time.split(":"))
                last_timestamp = self.hms_to_timestamp(last_hour,last_min,last_sec)

                first_time_offset = first_timestamp * canvas_height / (24 * 3600)
                last_time_offset = last_timestamp * canvas_height / (24 * 3600)
                median_time_offset = (first_time_offset + last_time_offset) // 2
                duration_time = last_time_offset - first_time_offset

                duration_hour, duration_min, duration_sec = self.timestamp_to_hms(last_timestamp-first_timestamp)

                command = lambda e=None, args=[file,year,month,day,first_timestamp,last_timestamp,ftp_log_list]: self.update_log(*args)
                self.dict_button_day_log[-1].config(command = command)

                log_canvas_ID = self.canvas_day_log_historic.create_rectangle(0, first_time_offset, canvas_width, last_time_offset,
                                                                              fill="cyan", width=1)
                self.canvas_day_log_historic.tag_bind(log_canvas_ID, "<Button-1>", command)

                if duration_time > canvas_height / 20:
                    log_text_canvas_ID = self.canvas_day_log_historic.create_text(canvas_width / 2, median_time_offset,
                                                                                  text = "%02i:%02i:%02i" %
                                                                                  (duration_hour, duration_min, duration_sec),
                                                                                  font = ("System", 16))
                    self.canvas_day_log_historic.tag_bind(log_text_canvas_ID, "<Button-1>", command)

            except Exception as e: print(e)

    def update_read_log_format(self, format = None, log_data = None):
        if not(log_data): log_data = self.last_log_data_used
        if not(format): format = self.last_format_used
        self.last_log_data_used = log_data
        self.last_format_used = format
        formated_data = ""
        self.text_log_read_data.delete(0.0, END)

        if format == "raw":
            for line in log_data.split("\n"):

                if self.variable_log_read_search.get() in line:

                    self.text_log_read_data.config(font = ("Purisa", 11), bg = "white", fg = "black")
                    self.text_log_read_data.insert(END, line + "\n")

        elif format == "chat":
            self.text_log_read_data.config(font = ("System", 10), bg = "gray10", fg = "white")

            for line in log_data.split("\n"):
                if "[CHAT]" in line:
                    line_text = "".join(line.split("[CHAT]")[1:])

                    if self.variable_log_read_search.get() in line_text: # Si le critère de recherche est bon

                        if "§" in line_text:
                            self.text_log_read_data.insert(END, line[:10] + " ", "chat_message")
                            for line_part in line_text.split("§"):
                                self.text_log_read_data.insert(END, line_part[1:], "§" + line_part[0])
                            self.text_log_read_data.insert(END, "\n")

                        else: self.text_log_read_data.insert(END, "%s %s\n" % (line[:10], line_text), "chat_message")

                elif "Connecting to " in line: self.text_log_read_data.insert(END, "%s Connexion à %s\n" %
                                                                              (line[:10], "".join(line.split("Connecting to ")[1:])),
                                                                              "server_connection")

        elif format == "server":
            for line in log_data.split("\n"):
                if "INFO]" in line:
                    line_text = "".join(line.split("INFO]")[1:])

                    if self.variable_log_read_search.get() in line_text:

                        if "§" in line_text:
                            self.text_log_read_data.insert(END, line[:10] + " ", "chat_message")
                            for line_part in line_text.split("§"):
                                self.text_log_read_data.insert(END, line_part[1:], "§" + line_part[0])
                            self.text_log_read_data.insert(END, "\n")
                        else:
                            self.text_log_read_data.insert(END, "%s %s\n" % (line[:10], line_text), "chat_message")

                    elif "WARN]" in line:
                        self.text_log_read_data.insert(END, "%s %s\n" % (line[:10],"".join(line.split("WARN]")[1:])),'server_warn')

        # Lors d'une recherche, le mot afficher est surligné (en jaune ou rouge)

    def update_log(self,file,year=0,month=0,day=0,first_timestamp=0,last_timestamp=0,ftp_log_list=None):
        """Met à jour l'interface affichant les différents logs"""
        first_hour,first_min,first_sec = self.timestamp_to_hms(first_timestamp)
        last_hour,last_min,last_sec = self.timestamp_to_hms(last_timestamp)
        # Permet d'afficher un mode simplifier pemettant de voir les connexions / déconnexion
        self.frame_log_read.grid(row = 3, column = 1, columnspan = 2)
        self.label_log_read_metadata.config(text = "Nom du fichier : %s\nDate : %02i/%02i/%04i %02i:%02i:%02i" %
                                            (file,day,month,year,first_hour,first_min,first_sec))

        if not(ftp_log_list):
            with gzip.open(file) as log_file: log_data = log_file.read().decode("cp1252")
        else:
            for tentative in range(5):
                try:
                    if not(self.variable_use_SFTP.get()):
                        log_file_data = BytesIO()
                        self.server_FTP.retrbinary("RETR /logs/%s" % os.path.basename(file), log_file_data.write)
                        log_file_data.seek(0)
                    else: log_file_data = self.server_FTP.open("logs/%s" % os.path.basename(file), "rb")

                    with gzip.GzipFile(fileobj=log_file_data) as log_file:
                        log_data = log_file.read().decode("cp1252")

                    break
                except:
                    print("Tentative %i" % tentative)

        self.button_log_read_format_raw.config(command = lambda format = "raw": self.update_read_log_format(format, log_data))
        self.button_log_read_format_chat.config(command = lambda format = "chat": self.update_read_log_format(format, log_data))
        self.button_log_read_format_server.config(command = lambda format = "server": self.update_read_log_format(format, log_data))

        self.update_read_log_format(self.last_format_used, log_data)
        if not (ftp_log_list): self.intersect_otherdata(year,month,day,first_timestamp,last_timestamp)

    def find_screenshot(self,year,month,day,first_timestamp,last_timestamp,update_canvas=False):
        first_hour,first_min,first_sec = self.timestamp_to_hms(first_timestamp)
        last_hour,last_min,last_sec = self.timestamp_to_hms(last_timestamp)

        canvas_width, canvas_height = self.canvas_screenshot.winfo_width(), self.canvas_screenshot.winfo_height()
        index = 0

        for file in glob.iglob(self.path + "\\screenshots\\" + "%04i-%02i-%02i_*.png" % (year, month, day)):
            filename = os.path.basename(file)

            try:
                screenshot_hour, screenshot_min, screenshot_sec = (int(x) for x in filename.split("_")[1].split(".")[:3])
                screenshot_timestamp = self.hms_to_timestamp(screenshot_hour,screenshot_min,screenshot_sec)
                first_timestamp = self.hms_to_timestamp(first_hour,first_min,first_sec)
                last_timestamp = self.hms_to_timestamp(last_hour,last_min,last_sec)
            except Exception as e: # Ceci se produit si la screenshot à été renommé, ...
                continue

            if first_timestamp < screenshot_timestamp < last_timestamp:  # On calcul et vérifie les timestamps pour être précis sur les screenshots associés
                if update_canvas:
                    with Image.open(file) as screenshot_image:
                        screenshot_image = screenshot_image.resize((canvas_width - 10 - 10, 9 * canvas_width // 16))
                        self.screenshot_imagetk[file] = ImageTk.PhotoImage(screenshot_image)
                        canvas_image_ID = self.canvas_screenshot.create_image(canvas_width/2, (screenshot_image.height/2+5)*(index*2+1)+5,
                                                                              image=self.screenshot_imagetk[file])
                    self.canvas_screenshot.tag_bind(canvas_image_ID, "<Button-1>", lambda event, file=file: os.startfile(file))
                index += 1

        self.canvas_screenshot.config(scrollregion=self.canvas_screenshot.bbox(ALL))
        return index

    def find_replay(self,year,month,day,first_timestamp,last_timestamp,update_canvas=False):
        first_hour,first_min,first_sec = self.timestamp_to_hms(first_timestamp)
        last_hour,last_min,last_sec = self.timestamp_to_hms(last_timestamp)

        canvas_width, canvas_height = self.canvas_replay.winfo_width(), self.canvas_replay.winfo_height()
        index = 0

        for file in glob.iglob(self.path + "\\replay_recordings\\" + "%04i_%02i_%02i_*.mcpr" % (year, month, day)):
            filename = os.path.basename(file)

            try:
                replay_hour, replay_min, replay_sec = (int(x) for x in
                                                       "".join(filename.split(".")[:-1]).split("_")[-3:])
                replay_timestamp = self.hms_to_timestamp(replay_hour,replay_min,replay_sec)
                first_timestamp =  self.hms_to_timestamp(first_hour,first_min,first_sec)
                last_timestamp =  self.hms_to_timestamp(last_hour,last_min,last_sec)
            except Exception as e:
                print(e)
                continue

            if first_timestamp < replay_timestamp < last_timestamp:
                if update_canvas:
                    with zipfile.ZipFile(file) as replay_file:
                        with replay_file.open("metaData.json") as replay_metadata_file:
                            replay_metadata = json.load(replay_metadata_file)

                    replay_duration_hour, replay_duration_min, replay_duration_sec = self.timestamp_to_hms(replay_metadata["duration"] // 1000)
                    self.canvas_replay.create_text(canvas_width / 2, 100 * (index + 1) - 50, text=filename, font=("System", 18))
                    self.canvas_replay.create_text(canvas_width / 2, 100 * (index + 1),
                                                   text="IP du serveur : %s\n" % (replay_metadata["serverName"]) + \
                                                        "Version du jeu : %s\n" % (replay_metadata["mcversion"]) + \
                                                        "Durée : %02i:%02i:%02i\n" % (
                                                        replay_duration_hour, replay_duration_min, replay_duration_sec),
                                                   font=("System", 16))

                index += 1 # On n'utilise pas d'enumerate parce que ce compteur ne doit être incrémenter que si la condition est remplie

        self.canvas_replay.config(scrollregion=self.canvas_replay.bbox(ALL))
        return index

    def intersect_otherdata(self,year,month,day,first_timestamp,last_timestamp):
        if os.path.exists(self.path + "\\screenshots\\"):
            self.frame_screenshot_intersect.grid(row = 1, column = 3, rowspan = 3, sticky = "NS") # Si on trouve un dossier de screenshots, ont affiche l'interface associé
        else: self.frame_screenshot_intersect.grid_forget() # Sinon on l'efface si un autre dossier de jeu le contenait
        if os.path.exists(self.path + "\\replay_recordings\\"):
            self.frame_replay_intersect.grid(row = 1, column = 4, rowspan = 3, sticky = "NS") # Si on trouve un dossier de replay, ont affiche l'interface associé
        else: self.frame_replay_intersect.grid_forget() # Sinon on l'efface si un autre dossier de jeu le contenait

        self.canvas_screenshot.delete(ALL) # Réinitilisation des screenshots affiché
        self.canvas_replay.delete(ALL) # Réinitilisation des replay affiché

        self.screenshot_imagetk = {} # Permet de garder "vivant" les screenshots (sinon, elles disparaissent instantanément)
        if first_timestamp==0 and last_timestamp==0:
            messagebox.showwarning("Attention", "Le programme n'à pas réussi à déterminer l'heure de ce log, il se peut "+\
                                                "que certaines fonctionnalitées soient alors indisponible.")

        self.find_screenshot(year,month,day,first_timestamp,last_timestamp,update_canvas=True)
        self.find_replay(year,month,day,first_timestamp,last_timestamp,update_canvas=True)

    def search_log(self):
        "permet de rechercher quelque chose dans les logs"
        toplevel_messagebox_search = Toplevel(self.root) # Nouvelle fenêtre pour ne pas surchargé l'interface principal
        toplevel_messagebox_search.grab_set() # On empêche d'intéragir avec la fenêtre principal
        toplevel_messagebox_search.resizable(width = False, height = False)
        try: toplevel_messagebox_search.iconbitmap("icon.ico")
        except: pass

        def search_by_server(file):
            """Renvoie True si le nom du serveur est trouvé, sinon False"""
            progressbar_action_bar.step(1)

            try:
                with gzip.open(file) as log_file: log_data = log_file.read().decode(encoding="cp1252", errors='ignore')
            except: return False
            if "Connecting to %s" % self.search_entry_data in log_data: return True
            else: return False

        def search_by_term(file):
            """Renvoie True si le terme, sinon False"""
            progressbar_action_bar.step(1)

            try:
                with gzip.open(file) as log_file: log_data = log_file.read().decode(encoding="cp1252", errors='ignore')
            except: return False
            if self.search_entry_data in log_data: return True
            else: return False

        search_option = {
            "Tout les logs": lambda file: True,
            "Rechercher les connexions à un serveur": search_by_server,
            "Rechercher un pseudo, un mot, un terme, une phrase": search_by_term,
        } # Différent moyen de trie associer à leur fonction

        Label(toplevel_messagebox_search, text = "Je souhaite...").grid(row = 1, column = 1)
        combobox_search_mode = ttk.Combobox(toplevel_messagebox_search, values = list(search_option.keys()),
                                            width = 50, font = ("Purisa", 20)) # Combobox dans lequel ont choisi sont type de tri
        combobox_search_mode.insert(0, list(search_option.keys())[0])
        combobox_search_mode.grid(row = 2, column = 1)
        Label(toplevel_messagebox_search, text = "...qui est...").grid(row = 3, column = 1)
        search_entry = Entry(toplevel_messagebox_search, font = ("System", 18)) # Entry dans lequel on tape notre requête
        search_entry.grid(row = 4, column = 1, sticky = "NEWS")

        def back():
            """fonction appelé par le bouton retour"""
            toplevel_messagebox_search.grab_release()
            toplevel_messagebox_search.destroy()

        def search():
            """fonction appelé par le bouton rechercher"""
            path = self.entry_game_dir.get()
            search_mode = combobox_search_mode.get()
            search_entry_data = search_entry.get()

            if search_mode == "":
                messagebox.showerror("Erreur", "Veuillez sélectionner un type de filtre")
                return -1

            elif search_entry_data == "" and not(search_mode == list(search_option.keys())[0]):
                messagebox.showerror("Erreur", "Veuillez entrer un filtre")
                return -1

            self.reset_log_read_search()
            self.variable_log_read_search.set(search_entry_data)

            max_step = len(glob.glob(path + "\\logs\\????-??-??-*.log.gz"))
            progressbar_action_bar.config(maximum = max_step)

            self.search_entry_data = search_entry_data
            if self.update_log_data(search_option[search_mode]) == -1:
                return -1

            if self.update_calendar() == -1:
                messagebox.showerror("Erreur", "Aucune correspondance trouvé")
                return -1

            back()

        def pre_search():
            "ligne éxécuter avant la recherche, pour l'esthétisme"
            progressbar_action_bar.grid(row = 5, column = 1, sticky = "NEWS")
            label_action_bar.grid_forget()

            if search() == -1:
                progressbar_action_bar.grid_forget()
                label_action_bar.grid(row=5, column=1, sticky="NEWS")

        label_action_bar = LabelFrame(toplevel_messagebox_search) # Barre dans laquelle sont les boutons
        label_action_bar.grid(row = 5, column = 1, sticky = "NEWS")
        label_action_bar.columnconfigure(2, weight = 1) # Permet de créer l'espace entre les deux boutons et de les coller aux bords
        Button(label_action_bar, text="Retour", relief=RIDGE, command = back).grid(row=1, column=1)
        Button(label_action_bar, text="Rechercher", relief = RIDGE, command = lambda: Thread(target=pre_search).start()).grid(row=1, column=3)

        Checkbutton(label_action_bar, text="Uniquement si il contient des screenshots", variable = self.variable_search_screenshot_only).grid(row=2, column=1, columnspan=3)
        Checkbutton(label_action_bar, text="Uniquement si il contient des replays", variable = self.variable_search_replay_only).grid(row=3, column=1, columnspan=3)

        progressbar_action_bar = ttk.Progressbar(toplevel_messagebox_search)

    def connect_ftp(self):
        toplevel_messagebox_ftp = Toplevel(self.root)  # Nouvelle fenêtre pour ne pas surchargé l'interface principal
        toplevel_messagebox_ftp.grab_set()  # On empêche d'intéragir avec la fenêtre principal
        toplevel_messagebox_ftp.resizable(width=False, height=False)
        try: self.root.iconbitmap("icon.ico")
        except: pass

        self.variable_ftp_server_saved = {}
        def load_ftp_server_saved():
            if os.path.exists("ftp_server_saved.json"):
                try:
                    with open("ftp_server_saved.json", "r") as file:
                        self.variable_ftp_server_saved = json.load(file)
                except Exception as e: print(e)

        load_ftp_server_saved()

        def save_ftp_server_saved(data = None):
            if data: self.variable_ftp_server_saved[data["ip"]] = data
            with open("ftp_server_saved.json", "w") as file: json.dump(self.variable_ftp_server_saved, file)
            combobox_ftp_server_saved.config(values = list(self.variable_ftp_server_saved.keys()))

        def load_ftp_server_selected():
            selected_ftp_server_profil = combobox_ftp_server_saved.get()
            ftp_server_data = self.variable_ftp_server_saved[selected_ftp_server_profil]

            entry_ftp_host_ip.delete(0, END)
            entry_ftp_host_ip.insert(END, ftp_server_data["ip"])
            entry_ftp_host_port.delete(0, END)
            entry_ftp_host_port.insert(END, ftp_server_data["port"])
            entry_ftp_user.delete(0, END)
            entry_ftp_user.insert(END, ftp_server_data["user"])
            self.variable_use_SFTP.set(ftp_server_data["use_sftp"])

        def delete_ftp_server_selected():
            selected_ftp_server_profil = combobox_ftp_server_saved.get()
            self.variable_ftp_server_saved.pop(selected_ftp_server_profil)
            save_ftp_server_saved()
            if len(list(self.variable_ftp_server_saved.keys())) > 0: combobox_ftp_server_saved.current(0)
            else: combobox_ftp_server_saved.delete(0, END)

        frame_ftp_server_saved = Frame(toplevel_messagebox_ftp)
        frame_ftp_server_saved.grid(row = 1, column = 1, columnspan = 4)

        Label(frame_ftp_server_saved, text = "Serveur enregistré : ", font = ("System", 18)).grid(row = 1, column = 1)
        combobox_ftp_server_saved = ttk.Combobox(frame_ftp_server_saved, values = list(self.variable_ftp_server_saved.keys()), font = ("System", 18))
        combobox_ftp_server_saved.grid(row = 1, column = 2)
        if len(list(self.variable_ftp_server_saved.keys())) > 0: combobox_ftp_server_saved.current(0)

        Button(frame_ftp_server_saved, text="Charger", font = ("System", 16), relief = RIDGE, command = load_ftp_server_selected).grid(row=1, column=3, sticky = "NEWS")

        Button(frame_ftp_server_saved, text="Sauver", font = ("System", 16), relief = RIDGE, command = lambda: save_ftp_server_saved(
            {"ip": entry_ftp_host_ip.get(),
             "port": entry_ftp_host_port.get(),
             "user": entry_ftp_user.get(),
             "use_sftp": self.variable_use_SFTP.get()})
               ).grid(row=1, column=4, sticky = "NEWS")

        Button(frame_ftp_server_saved, text="Supprimer", font = ("System", 16), relief = RIDGE, command = delete_ftp_server_selected).grid(row=1, column=5, sticky = "NEWS")

        Label(toplevel_messagebox_ftp, text = "IP du serveur : ").grid(row = 2, column = 1)
        entry_ftp_host_ip = Entry(toplevel_messagebox_ftp, font = ("System", 18))
        entry_ftp_host_ip.insert(END, "127.0.0.1")
        entry_ftp_host_ip.grid(row = 2, column = 2)
        Label(toplevel_messagebox_ftp, text="Port : ").grid(row=2, column=3)
        entry_ftp_host_port = Entry(toplevel_messagebox_ftp, font = ("System", 18))
        entry_ftp_host_port.insert(END, "22")
        entry_ftp_host_port.grid(row = 2, column = 4)

        Label(toplevel_messagebox_ftp, text="Utilisateur : ").grid(row=3, column=1)
        entry_ftp_user = Entry(toplevel_messagebox_ftp, font=("System", 18))
        entry_ftp_user.grid(row=3, column=2)
        Label(toplevel_messagebox_ftp, text="Mot de passe : ").grid(row=3, column=3)
        entry_ftp_password = Entry(toplevel_messagebox_ftp, font=("System", 18), show = "*")
        entry_ftp_password.grid(row=3, column=4)

        def back():
            """fonction appelé par le bouton retour"""
            toplevel_messagebox_ftp.grab_release()
            toplevel_messagebox_ftp.destroy()

        def connexion():
            host_ip, host_port = entry_ftp_host_ip.get(), entry_ftp_host_port.get()
            user, password = entry_ftp_user.get(), entry_ftp_password.get()

            if not(self.variable_use_SFTP.get()):
                self.server_FTP = ftplib.FTP(timeout = 15)

                try: self.server_FTP.connect(host_ip, int(host_port), timeout = 15)
                except:
                    messagebox.showerror("Erreur", "L'hôte n'a pas été trouvé")
                    return -1
                try: self.server_FTP.login(user, password)
                except:
                    messagebox.showerror("Erreur", "Les identifiants ne sont pas correct")
                    return -1

                try: ftp_log_list = self.server_FTP.nlst("logs/")
                except:
                    messagebox.showerror("Erreur", "Ce serveur ne contient pas de dossier /logs/")
                    return -1
            else:
                try:
                    process = subprocess.Popen(["ssh-keyscan", "-t", "rsa", "-p", str(host_port), host_ip], stdout=subprocess.PIPE, shell=True)
                    hash_type, keydata = process.communicate()[0].split(b" ")[1:] # Le premier est l'ip de nouveau, mais avec le port dans un mauvais format, donc [1:]
                    key = paramiko.RSAKey(data=decodebytes(keydata))
                    cnopts = pysftp.CnOpts("known_hosts")
                    cnopts.hostkeys.add(host_ip, hash_type, key)
                except Exception as e:
                    messagebox.showerror("Erreur", "Une erreur est survenue pendant la récupération de la clé RSA\n"+\
                                         "\nPlus d'information sur l'erreur : \n\n%s" % str(e))
                    return -1

                try: self.server_FTP = pysftp.Connection(host_ip, username=user, password=password, cnopts=cnopts, port = int(host_port))
                except Exception as e:
                    messagebox.showerror("Erreur", "Une erreur est survenue pendant la connexion au serveur, \n" +\
                                         "vérifier vos identifiants.\n\n Plus d'information sur l'erreur :\n\n%s" % str(e))
                    return -1

                try: ftp_log_list = self.server_FTP.listdir("logs/")
                except:
                    messagebox.showerror("Erreur", "Ce serveur ne contient pas de dossier /logs/")
                    return -1

            try:
                self.progressbar_messagebox_ftp.step()
                for tentative in range(1, 5 + 1):
                    if self.update_log_data(ftp_log_list = ftp_log_list) == -1:
                        if tentative == 5: raise Exception()
                        continue
                    else: break
            except ftplib.error_temp:
                messagebox.showerror("Erreur", "Impossible de faire une requête au serveur FTP\n"+\
                                     "Vérifier que aucun autre processus n'est connecté au même\n"+\
                                     "Serveur FTP, puis réessayer.")
                return -1
            except: return -1
            if self.update_calendar(ftp_log_list = ftp_log_list) == -1:
                messagebox.showerror("Erreur", "Aucune correspondance trouvé")
                return -1

            back()

        def pre_connexion():
            frame_messagebox_ftp_action_bar.grid_forget()
            self.progressbar_messagebox_ftp.grid(row = 4, column = 1, columnspan = 4, sticky = "NEWS")

            if connexion() == -1:
                frame_messagebox_ftp_action_bar.grid(row = 4, column = 1, columnspan = 4, sticky = "NEWS")
                self.progressbar_messagebox_ftp.grid_forget()


        frame_messagebox_ftp_action_bar = Frame(toplevel_messagebox_ftp)
        frame_messagebox_ftp_action_bar.grid(row = 4, column = 1, columnspan = 4, sticky = "NEWS")
        frame_messagebox_ftp_action_bar.columnconfigure(2, weight = 1)
        Button(frame_messagebox_ftp_action_bar, text = "Retour", relief = RIDGE, command = back).grid(row = 1, column = 1, sticky = "NEWS")
        Button(frame_messagebox_ftp_action_bar, text = "Connexion", relief = RIDGE, command = lambda: Thread(target=pre_connexion).start()).grid(row = 1, column = 3, sticky = "NEWS")
        Checkbutton(frame_messagebox_ftp_action_bar, text = "Utiliser le protocole SFTP", variable = self.variable_use_SFTP).grid(row = 1, column = 2)

        self.progressbar_messagebox_ftp = ttk.Progressbar(toplevel_messagebox_ftp)


    def player_nbt_inventory(self, player_uuid, ftp_log_list):
        toplevel_messagebox_player_inventory = Toplevel(self.root)  # Nouvelle fenêtre pour ne pas surchargé l'interface principal
        toplevel_messagebox_player_inventory.grab_set()  # On empêche d'intéragir avec la fenêtre principal
        toplevel_messagebox_player_inventory.resizable(width=False, height=False)
        toplevel_messagebox_player_inventory.title(player_uuid)
        try: self.root.iconbitmap("icon.ico")
        except: pass

        player_inventory_image = Image.open("assets\\inventory.png")
        ratio = player_inventory_image.height / player_inventory_image.width
        player_inventory_image = player_inventory_image.resize((500, round(500 * ratio)))
        self.player_inventory_image_tk = ImageTk.PhotoImage(player_inventory_image)
        width_inventory, height_inventory = player_inventory_image.width, player_inventory_image.height

        item_not_found_image = Image.open("assets\\not_found_icon.png").resize((46,46))
        item_not_found_image_tk = ImageTk.PhotoImage(item_not_found_image)

        container_9x3_image = Image.open("assets\\container_9x3.png").resize((500, 250))
        self.container_9x3_image_tk = ImageTk.PhotoImage(container_9x3_image)

        width_container_9x3, height_container_9x3 = container_9x3_image.width, container_9x3_image.height

        Label(toplevel_messagebox_player_inventory, text = "Inventaire", font = ("System", 20)).grid(row = 1, column = 1)
        canvas_player_inventory = Canvas(toplevel_messagebox_player_inventory, width = width_inventory, height = height_inventory)
        canvas_player_inventory.create_image(width_inventory // 2, height_inventory // 2, image = self.player_inventory_image_tk)
        canvas_player_inventory.grid(row = 2, column = 1, rowspan = 3)

        Label(toplevel_messagebox_player_inventory, text="Ender Chest", font=("System", 20)).grid(row=1, column=2)
        canvas_player_enderchest = Canvas(toplevel_messagebox_player_inventory, width=width_container_9x3, height=height_container_9x3)
        canvas_player_enderchest.create_image(width_container_9x3 // 2, height_container_9x3 // 2, image=self.container_9x3_image_tk)
        canvas_player_enderchest.grid(row=2, column=2)

        Label(toplevel_messagebox_player_inventory, text="Shulker", font=("System", 20)).grid(row=3, column=2)
        canvas_player_shulker = Canvas(toplevel_messagebox_player_inventory, width=width_container_9x3, height=height_container_9x3)
        canvas_player_shulker.create_image(width_container_9x3 // 2, height_container_9x3 // 2, image=self.container_9x3_image_tk)
        canvas_player_shulker.grid(row=4, column=2)

        self.slot_id_to_canvas_inventory = {}
        for index, slot_id in enumerate(range(9)): self.slot_id_to_canvas_inventory[slot_id] = (index * 51 + 22, 403) # Constante obtenu pour une image de 500x500
        for index, slot_id in enumerate(range(9, 18)): self.slot_id_to_canvas_inventory[slot_id] = (index * 51 + 22, 238) # Constante obtenu pour une image de 500x500
        for index, slot_id in enumerate(range(18, 27)): self.slot_id_to_canvas_inventory[slot_id] = (index * 51 + 22, 290) # Constante obtenu pour une image de 500x500
        for index, slot_id in enumerate(range(27, 36)): self.slot_id_to_canvas_inventory[slot_id] = (index * 51 + 22, 341) # Constante obtenu pour une image de 500x500
        for index, slot_id in enumerate(range(103, 99, -1)): self.slot_id_to_canvas_inventory[slot_id] = (22, index * 51 + 22) # Constante obtenu pour une image de 500x500
        self.slot_id_to_canvas_inventory[-106] = (218, 176)

        self.slot_id_to_canvas_container_9x3 = {}
        for index in range(27): self.slot_id_to_canvas_container_9x3[index] = ((index % 9) * 51 + 22, (index // 9) * 51 + 51)  # Constante obtenu pour une image de 500x500

        label_item_information = Label(toplevel_messagebox_player_inventory, text = "Cliquer sur un objet pour voir ses statistiques", font = ("System", 12))
        label_item_information.grid(row = 5, column = 1)

        self.texture_assets = {}
        nbt_data = None
        if not(ftp_log_list): nbt_data = nbt.nbt.NBTFile(self.path + "\\%s\\playerdata\\%s" % (self.world_name, player_uuid))
        else:
            for tentative in range(5):
                try:
                    if not(self.variable_use_SFTP.get()):
                        nbt_data_file = BytesIO()
                        self.server_FTP.retrbinary("RETR " + self.world_name[:-1] + "/playerdata/" + player_uuid, nbt_data_file.write) # [:-1 car le dernier caractère est un \n]
                        nbt_data_file.seek(0)
                    else: nbt_data_file = self.server_FTP.open(self.world_name + "/playerdata/" + player_uuid, "rb")

                    nbt_data = nbt.nbt.NBTFile(fileobj = nbt_data_file)
                    break
                except Exception as e:
                    print("Tentative %i (playerdata) (%s)" % (tentative, str(e)))

        if not(nbt_data):
            messagebox.showerror("Erreur", "Impossible de récupérer les données du joueur")
            toplevel_messagebox_player_inventory.destroy()
            return -1

        def load_item_texture(item):
            if "minecraft:" in item:
                if not(item in self.texture_assets):
                    if "_slab" in item: item_name = item.split(":")[-1].split("_slab")[0]
                    elif "_stairs" in item: item_name = item.split(":")[-1].split("_stairs")[0]
                    elif "_fence" in item: item_name = item.split(":")[-1].split("_fence")[0]
                    else: item_name = item.split(":")[-1]

                    if "smooth" in item: item_name = item_name.split("smooth_")[1]

                    item_texture_path = "assets\\item\\%s.png" % item_name
                    item_texture_path_side = "assets\\item\\%s_side.png" % item_name
                    item_texture_path_front = "assets\\item\\%s_front.png" % item_name
                    item_texture_path_planks = "assets\\item\\%s_planks.png" % item_name

                    if os.path.exists(item_texture_path): self.texture_assets[item] = ImageTk.PhotoImage(Image.open(item_texture_path).resize((46,46)))
                    elif os.path.exists(item_texture_path_side): self.texture_assets[item] = ImageTk.PhotoImage(Image.open(item_texture_path_side).resize((46,46)))
                    elif os.path.exists(item_texture_path_front): self.texture_assets[item] = ImageTk.PhotoImage(Image.open(item_texture_path_front).resize((46, 46)))
                    elif os.path.exists(item_texture_path_planks): self.texture_assets[item] = ImageTk.PhotoImage(Image.open(item_texture_path_planks).resize((46, 46)))
                    elif "spawn_egg" in item: self.texture_assets[item] = ImageTk.PhotoImage(Image.open("assets\\item\\spawn_egg.png").resize((46, 46)))
                    else: self.texture_assets[item] = item_not_found_image_tk
            else: return -1

        def show_more_information(item):
            if "tag" in item:
                Tags = "\n"
                if "Damage" in item["tag"]:
                    try: Tags += "Damage : %s\n" % str(item["tag"]["Damage"].value)
                    except: Tags += "Damage : ?"
                if "Enchantments" in item["tag"]:
                    Tags += "Enchanté avec : \n"
                    try:
                        for enchant in item["tag"]["Enchantments"]: Tags += "- %s (niveau %i)\n" % (enchant["id"].value, enchant["lvl"].value)
                    except: Tags += "- ?\n"
                if "display" in item["tag"]:
                    if "Name" in item["tag"]["display"]:
                        try: Tags += "Renommée en : %s\n" % item["tag"]["display"]["Name"].value
                        except: "Renommée en : ?\n"
                    if "Lore" in item["tag"]["display"]:
                        try: Tags += "Lore : %s\n" % item["tag"]["display"]["Lore"].value
                        except: "Lore : ?\n"
                if "SkullOwner" in item["tag"]:
                    try: Tags += "Tête de : %s\n" % item["tag"]["SkullOwner"].value
                    except: Tags += "Tête de : ?\n"
                if "BlockEntityTag" in item["tag"]:
                    Tags += "Contient :\n"
                    try:
                        canvas_player_shulker.delete(ALL)
                        canvas_player_shulker.create_image(width_container_9x3 // 2, height_container_9x3 // 2, image=self.container_9x3_image_tk)
                        for index, container_item in enumerate(item["tag"]["BlockEntityTag"]["Items"].tags):
                            try:
                                if not(load_item_texture(container_item["id"].value) == -1):
                                    canvas_player_shulker.create_image(
                                        *self.slot_id_to_canvas_container_9x3[container_item["Slot"].value],
                                        image=self.texture_assets[container_item["id"].value], anchor="nw",
                                        tags="slot-shulker-%i" % index)

                                    canvas_player_shulker.create_text(
                                        *[x + 48 for x in self.slot_id_to_canvas_container_9x3[container_item["Slot"].value]],
                                        text=str(container_item["Count"].value), font=("System", 18), anchor="se",
                                        fill="white", tags="slot-shulker-%i" % index)

                                    canvas_player_shulker.tag_bind("slot-shulker-%i" % index, "<Button-1>",
                                                                    lambda e, item=container_item: show_more_information(item))

                            except Exception as e:
                                print("Inventaire : " + str(e))
                    except: Tags += "?\n"
            else: Tags = "Aucun"

            label_item_information.config(text = "Nom de l'objet : %s\n" % item["id"].value +\
                                          "Quantité : %i\n" % item["Count"].value +\
                                          "Tags : %s\n" % Tags)

        for index, item in enumerate(nbt_data["Inventory"].tags):
            try:
                if not(load_item_texture(item["id"].value) == -1):
                    canvas_player_inventory.create_image(*self.slot_id_to_canvas_inventory[item["Slot"].value], image = self.texture_assets[item["id"].value], anchor="nw", tags = "slot-inventory-%i" % index)
                    canvas_player_inventory.create_text(*[x + 48 for x in self.slot_id_to_canvas_inventory[item["Slot"].value]],
                                                        text = str(item["Count"].value), font = ("System", 18), anchor="se", fill = "white", tags = "slot-inventory-%i" % index)
                    canvas_player_inventory.tag_bind("slot-inventory-%i" % index, "<Button-1>", lambda e, item = item: show_more_information(item))
            except Exception as e:
                print("Inventaire : " + str(e))

        for index, item in enumerate(nbt_data["EnderItems"].tags):
            try:
                if not(load_item_texture(item["id"].value) == -1):
                    canvas_player_enderchest.create_image(*self.slot_id_to_canvas_container_9x3[item["Slot"].value], image = self.texture_assets[item["id"].value], anchor="nw", tags = "slot-enderchest-%i" % index)
                    canvas_player_enderchest.create_text(*[x + 48 for x in self.slot_id_to_canvas_container_9x3[item["Slot"].value]],
                                                         text = str(item["Count"].value), font = ("System", 18), anchor="se", fill = "white", tags = "slot-enderchest-%i" % index)
                    canvas_player_enderchest.tag_bind("slot-enderchest-%i" % index, "<Button-1>", lambda e, item=item: show_more_information(item))
            except Exception as e:
                print("Enderchest : " + str(e))

        player_metadata_text = ""
        if "Pos" in nbt_data: player_metadata_text += "Coordonées : x = %i | y = %i | z = %i\n" % (nbt_data["Pos"][0].value, nbt_data["Pos"][1].value, nbt_data["Pos"][2].value)
        if "Health" in nbt_data: player_metadata_text += "Vie : %i / 20\n" % nbt_data["Health"].value
        if "SpawnX" in nbt_data: player_metadata_text += "Spawnpoint : x = %i | y = %i | z = %i\n" % (nbt_data["SpawnX"].value, nbt_data["SpawnY"].value, nbt_data["SpawnZ"].value)

        Label(toplevel_messagebox_player_inventory, text = player_metadata_text, font =("System", 8)).grid(row = 5, column = 2)

    def global_statistic(self):
        toplevel_messagebox_global_statistic = Toplevel(self.root)  # Nouvelle fenêtre pour ne pas surchargé l'interface principal
        toplevel_messagebox_global_statistic.grab_set()  # On empêche d'intéragir avec la fenêtre principal
        toplevel_messagebox_global_statistic.resizable(width=False, height=False)
        try: self.root.iconbitmap("icon.ico")
        except: pass

        canvas_messagebox_global_statistic = Canvas(toplevel_messagebox_global_statistic, width = 500, height = 200)
        canvas_messagebox_global_statistic.grid(row = 1, column = 1)
        canvas_messagebox_global_statistic.update()

        width, height = canvas_messagebox_global_statistic.winfo_width(), canvas_messagebox_global_statistic.winfo_height()

        list_year = list(self.log_metadata.keys())
        first_year = list_year[0]
        max_year = list_year[-1] - first_year + 1

        for year_index, year in enumerate(range(first_year, first_year + max_year)):
            if year in self.log_metadata:
                list_month = list(self.log_metadata[year].keys())
                max_month = list_month[-1] - list_month[1]
                for month_index, month in enumerate(self.log_metadata[year]):
                    list_day = list(self.log_metadata[year][month].keys())
                    max_day = list_day[-1] - list_day[1]
                    for day_index, day in enumerate(self.log_metadata[year][month]):
                        if day != "total":
                            offset_width = width * year_index / max_year + \
                                           (width / max_month) * month_index / max_month + \
                                           (width / (max_month * max_day)) * day_index / (max_month * max_day)

                            offset_next_day = width / (max_month * max_day) ** 2

                            offset_height = height - self.log_metadata[year][month][day] * height // self.max_log_total

                            canvas_messagebox_global_statistic.create_polygon(
                                offset_width, height,
                                offset_width, offset_height,
                                offset_width + offset_next_day, offset_height,
                                offset_width + offset_next_day, height,
                                fill = "cyan", outline = "cyan"
                                )

            canvas_messagebox_global_statistic.create_text(width * (year_index + 0.5) / max_year, height // 2, text = year, angle=90, font = ("Purisa", 18))
            canvas_messagebox_global_statistic.create_line(width * year_index / max_year, height,
                                                           width * year_index / max_year, 0,
                                                           fill = "gray70", dash=(100, 1), width = 2)

            Label(toplevel_messagebox_global_statistic, text = "Nombre total de log : %i" % self.total_log).grid(row = 2, column = 1)

main = Main()
mainloop()
