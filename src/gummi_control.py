#!/bin/sh
"exec" "`dirname $0`/env/bin/python" "$0" "$@"
# shebang for virtualenv execution from any location
# credit: stackoverflow.com/questions/20095351

import textwrap
from time import time, sleep

from Xlib.display import Display
from pyfiglet import figlet_format
from scipy.interpolate import interp1d

from src.control.position_controller import PositionController
from src.control.raw_controller import OutOfRangeError
from src.constants import DEFAULT_ARM_CONFIG
from src.configurator import Configurator

banner_string = 'GummiControl'
print(figlet_format(banner_string, font='rectangles'))


class MouseHandler:
    def __init__(self, min_angle=50, max_angle=180):
        self.root = Display().screen().root
        screen_width = self.root.get_geometry().width
        screen_height = self.root.get_geometry().height

        self.stiffness_mapper = interp1d([0, screen_height],
                                         [50, -30])
        self.angle_mapper = interp1d([0, screen_width],
                                     [min_angle, max_angle])

        self.last_command = None
        self.last_update_time = None

    def get_cmd_from_mouse_position(self):
        qp = self.root.query_pointer()
        angle = self.angle_mapper(qp.root_x)
        stiffness = self.stiffness_mapper(qp.root_y)

        if [angle, stiffness] != self.last_command:
            position_changed = True
            self.last_command = [angle, stiffness]
            self.last_update_time = time()
        else:
            position_changed = False
        return angle, stiffness, position_changed

    def continuous_control(self, controller, timeout=float('inf')):
        self.last_update_time = time()
        while time() - self.last_update_time < timeout:
            sleep(0.001)
            angle, stiffness, position_changed = self.get_cmd_from_mouse_position()
            if not position_changed:
                continue
            try:
                controller.send(angle, stiffness)
                print(f'angle: {angle:3.0f}   stiffness: {stiffness:3.0f}')
            except OutOfRangeError:
                print('servo out of range')


help_string = f"""
    Type commands that will be sent to the arm:
        command:     "<angle> <stiffness>"
        for example: "120 10"

    To send raw angles to servos:
        command:     "r<angle> <stiffness>"
        for example: "r35 10"

    Print arm angle measured by camera:
        'c'

    Mouse control:
        press 'm' to turn on
        CTRL+C to turn off
        move mouse left-right to control arm position
        move mouse up-down to control arm stiffness

    Quit:
        press 'q'
    """

if __name__ == '__main__':
    filename = input(
        f'Type name of the config file you\'d like to use.\n'
        f'For default config ({DEFAULT_ARM_CONFIG}) press ENTER.\n')
    if filename == '':
        filename = DEFAULT_ARM_CONFIG
    while not Configurator.config_exists(filename):
        filename = input('This file doesn\'t exist. Try again.\n')
        if filename == '':
            filename = DEFAULT_ARM_CONFIG

    controller = PositionController()
    controller.load_config(filename)
    mouse_handler = MouseHandler()

    while True:
        line = input()

        if line == 'q':
            controller.kill()
            exit()
        if line == 'm':
            try:
                mouse_handler.continuous_control(controller)
            except KeyboardInterrupt:
                pass
            print('\nQuited mouse mode')
            continue
        if line == 'c':
            angle = controller.position_detector.get_angle()
            print(angle)
            continue

        # parse
        raw = False
        try:
            angle_str, stiffness_str = line.split()
            if angle_str[0] == 'r':
                raw = True
                angle_str = angle_str[1:]
            angle, stiffness = float(angle_str), float(stiffness_str)
        except ValueError:
            print(textwrap.dedent(help_string))
            continue

        # send
        try:
            if raw:
                controller.raw_controller.send(angle, stiffness)
            else:
                controller.send(angle, stiffness)
        except OutOfRangeError:
            print('servo out of range')
