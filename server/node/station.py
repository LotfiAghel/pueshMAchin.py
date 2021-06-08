from .node import Node
import os
import json

PATH = os.path.dirname(os.path.abspath(__file__))
SERVER_PATH = os.path.dirname(PATH)
BASE_PATH = os.path.dirname(SERVER_PATH)
VISION_ANNOTATION_FILE = os.path.join(BASE_PATH, 'models/annotaion.json')

with open(VISION_ANNOTATION_FILE) as f:
    VISION_ANNOTATION = json.loads(f.read())


class Station(Node):
    type = 'station'
    arduino_reset_pin = 21

    g2core_config_base = [
        # X - Holder Motor
        (1, {
            'ma': 0,  # map to X
            'sa': 1.8,  # step angle 1.8
            'tr': 360,  # travel per rev = 360 degree
            'mi': 32,  # microstep = 32
            'po': 1,  # direction
        }),
        ('x', {
            'am': 1,  # standard axis mode
            'vm': 360000,  # max speed
            'fr': 360000,  # max feed rate
            'jm': 360000,  # max jerk
        }),
        ('out', {7: 1, 8: 1, 9: 1}),  # Microstepping enabled

        # Y - Dosing Motor
        (2, {
            'ma': 1,  # map to Y
            'sa': 1.8,  # step angle 1.8
            'tr': 360,  # travel per rev = 360 degree
            'mi': 32,  # microstep = 32
            'po': 1,  # direction
        }),
        ('y', {
            'am': 1,  # standard axis mode
            'vm': 360000,  # max speed
            'fr': 360000,  # max feed rate
            'jm': 360000,  # max jerk
        }),
        ('out', {10: 1, 11: 1, 12: 1}),  # Microstepping enabled

        # Z - Main Motor
        (3, {
            'ma': 2,  # map to Z
            'sa': 1.8,  # step angle 1.8
            'tr': 8,  # travel per rev = 8mm
            'mi': 2,  # microstep = 2
            'po': 1,  # direction
        }),
        ('z', {
            'am': 1,  # standard axis mode
            'vm': 35000,  # max speed
            'fr': 800000,  # max feed rate
            'tn': 0,  # min travel
            'tm': 230,  # max travel
            'jm': 20000,  # max jerk
            'jh': 3000,  # homing jerk
            'hi': 1,  # home switch
            'hd': 0,  # homing direction
            'sv': 1000,  # home search speed
            'lv': 200,  # latch speed
            'zb': 1,  # zero backoff
        }),
        ('di1mo', 1),  # Homing Switch - Mode = Active High - NC
    ]

    hw_config_base = {
        'valves': {
            'holder': 1,
            'dosing': 2,
            'main': 3,
            'dosing_base': 4,
            'gate': 5,
            'reserve': 6,
        },
        'di': {
            'jack': 1,  # jack verification
            'gate': 2,  # gate verification
        },
        'points': {
            'H_ALIGNING': 21500,
            'H_PUSH': 23000,
        }

    }

    async def home(self):
        return await self.send_command_raw('G28.2 Z0')

    async def send_command_create_camera(self):
        annotation_data = VISION_ANNOTATION[str(self.ip_short)]
        roi = VISION_ANNOTATION
        command = {
            'verb': 'create_camera',
            'dosing_roi': [annotation_data['dosing_roi']],
            'holder_roi': [annotation_data['holder_roi']],
        }
        return await self.send_command(command)

    def set_status(self, **kwargs):
        # if 'data' in kwargs:
        #     data = kwargs['data']
        #     kwargs['data'] = data
        super(Station, self).set_status(**kwargs)

    #
    # def set_home_retract(self, motor_index, value):
    #     self.hw_config['motors'][motor_index]['home_retract'] = value
    #
    # def goto(self, location, offset=0, **kwargs):
    #     if isinstance(location, str):
    #         h = self.hw_config['points'][location] + offset
    #     else:
    #         h = location
    #     move = {'steps': h, 'absolute': True}
    #     move.update(kwargs)
    #     moves = [{}, {}, {}, move]
    #     return self.send_command({'verb': 'move_motors', 'moves': moves}, assert_success=True)
