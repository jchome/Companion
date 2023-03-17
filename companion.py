#!/usr/bin/env python3

from pynput import mouse
import json
import subprocess
import re
import configparser
import os

from tkinter import *
import tkinter.font as font

class Companion:

    def __init__(self, config_ini):
        self.config_companion = config_ini
        with open(self.config_companion['CONFIG']['app_config_file'], 'r') as f:
            self.conf = json.load(f)

        self.current_module = self._get_module(self.conf["start"])
        self.listener = None
        self.window = None

    def start(self):
        ## Collect events until released
        self.listener = mouse.Listener(
                on_move=self.on_move,
                on_click=self.on_click,
                on_scroll=self.on_scroll)
        self.listener.start()
        ## Open the GUI
        self._open_window()
        
    def _open_window(self):
        self.window = Tk()

        self.window.title(self.config_companion['UI']['title'])
        self.window.geometry(self.config_companion['UI']['geometry'])
        self.window.resizable(False, False)
        ## Does not work
        #self.window.attributes('-alpha',0.5)

        if self.config_companion.has_option('UI','background'):
            option_background = self.config_companion['UI']['background'].strip()
            self.window.configure(background=option_background)

        if self.config_companion.has_option('UI','button_image') \
                and len(self.config_companion['UI']['button_image'].strip()) > 0:
            button_image = PhotoImage(file=self.config_companion['UI']['button_image'].strip())
            button = Button(self.window, image=button_image, command=self._open_help, borderwidth=0)
        else:

            ## Default button text
            button_title = "Help"
            if self.config_companion.has_option('UI','button_title'):
                button_title = self.config_companion['UI']['button_title'].strip()

            ## Button's font
            font_description = 'Arial 12'
            if self.config_companion.has_option('UI','button_font'):
                font_description = self.config_companion['UI']['button_font'].strip()
            
            fg_color = '#000000'
            if self.config_companion.has_option('UI','button_foreground'):
                fg_color = self.config_companion['UI']['button_foreground'].strip()

            bg_color = '#a0a0a0'
            if self.config_companion.has_option('UI','button_background'):
                bg_color = self.config_companion['UI']['button_background'].strip()

            button = Button(self.window, text=button_title, command=self._open_help, 
                            fg=fg_color,
                            bg=bg_color,
                            font=(font_description))
        button.pack(padx = 10, pady = 50)

        ## Always on top
        if self.config_companion.has_option('UI','always_on_top') and \
                self.config_companion['UI']['always_on_top'].strip() == 'True':
            self.window.attributes('-topmost', 1)

        ## Icon
        if self.config_companion.has_option('UI','icon_file'):
            self.window.iconbitmap(self.config_companion['UI']['icon_file'])

        if self.config_companion.has_option('UI','no_decoration') and \
                self.config_companion['UI']['no_decoration'].strip() == 'True':
            self.window.overrideredirect(True)

        ## Does not work
        #self.window.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.window.mainloop()
        ## -- Not reachable code --



    def on_move(self, x, y):
        pass

    def on_scroll(self, x, y, dx, dy):
        pass

    def on_click(self, x, y, button, pressed):
        if pressed:
            return
        ## Get the current active window corners
        script_corners = self.config_companion['SCRIPTS']['corners'].split(' ')
        resultCorners = subprocess.run(script_corners, stdout=subprocess.PIPE)
        window_corners = [int(i) for i in resultCorners.stdout.decode('utf8').strip().split(' ')]
        win_x = x - window_corners[0]
        win_y = y - window_corners[1]

        script_identify = self.config_companion['SCRIPTS']['identify'].split(' ')
        resultNameOfWindow = subprocess.run(script_identify, stdout=subprocess.PIPE)
        nameOfWindow = re.search(r'_NET_WM_NAME\(UTF8_STRING\) = "(.*)"', resultNameOfWindow.stdout.decode('utf8')).group(1)
        print('{0} at {1} on window <{2}>'.format(
            'Released',
            (win_x, win_y),
            nameOfWindow
            ))
        self.move_to_module_at(win_x, win_y, nameOfWindow)
        
    def move_to_module_at(self, win_x, win_y, nameOfWindow):
        regex_target_window = self.conf['window'].replace("*", ".*")
        ## Check the window
        if not re.match(regex_target_window, nameOfWindow):
            print('Window name <<{0}>> does not match with <<{1}>>. Nothing to do.'.format(nameOfWindow, self.conf['window']))
            return
        ## Get the possible actions from the current module
        module_conf = self._get_module(self.current_module['name'])
        if module_conf is None:
            print('Cannot find module <<{0}>>'.format(self.current_module['name']))
            return
        all_actions = module_conf['actions']
        ## Find the action
        action = self._get_action(all_actions, (win_x, win_y))
        if action is None:
            print('No action at this position, in the module {0}'.format(module_conf['name']))
            return
        print('Action found: {0}'.format(action['name']))
        next_module = self._get_module(action['target'])
        if next_module is None:
            print('Target module <<{0}>> not found for action {1}'.format(action['name'], action['target']))
            return
        else:
            ## Move to the target module 
            print('Moved to module <<{0}>>'.format(next_module))
            self.current_module = next_module
            self._open_help()

    def _open_help(self):
        help_file = self.current_module['help']
        exec_for_help = self.config_companion['CONFIG']['exec_for_help'].format(help_file)

        ## TODO : ouvrir une seule instance ???

        os.system(exec_for_help)
        print('Run {0}'.format(exec_for_help))

    
    def _get_module(self, module_name):
        for m in self.conf['modules']: 
            if m['name'] == module_name:
                return m
        return None
    
    def _get_action(self, actions, mouse_position):
        for a in actions:
            if a['corners'] and self._in_corner(mouse_position, a['corners']):
                return a
        return None

    def _in_corner(self, mouse_position, corners):
        if mouse_position[0] < corners[0] + corners[2] and mouse_position[0] > corners[0]:
            if mouse_position[1] < corners[1] + corners[3] and mouse_position[1] > corners[1]:
                return True
        return False

if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('companion.ini')
    comp = Companion(config)
    comp.start()