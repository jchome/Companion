#!/usr/bin/env python3

from pynput import mouse
import json
import subprocess
import re
import configparser
import os

class Companion:

    def __init__(self, config_ini):
        self.config_companion = config_ini
        with open(self.config_companion['CONFIG']['app_config_file'], 'r') as f:
            self.conf = json.load(f)

        self.current_module = self._get_module(self.conf["start"])

        # Collect events until released
        with mouse.Listener(
                on_move=self.on_move,
                on_click=self.on_click,
                on_scroll=self.on_scroll) as listener:
            listener.join()
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
            self.open_help()

    def open_help(self):
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
    Companion(config)
