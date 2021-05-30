from .node import Node
from .node import MOTOR_STATUS_ENUM
from .trajectory import CURVE_ROBOT

# 1600 pulse  / rev


class Robot(Node):
    type = 'robot'
    arduino_reset_pin = 2
    valves = [15, 16]
    hw_config = {
        'valves': [36, 39, 38, 41, 40, 43, 42, 45, 44, 47],
        'motors': [
            {  # AXIS 1 - Up & Down
                'pin_pulse': 15,
                'pin_dir': 14,
                'pin_limit_n': 50,
                'pin_limit_p': 51,
                'microstep': 2500,
                'course': 9000,
                'homing_delay': 800,
                'home_retract': 200,
                'has_encoder': True,
                'encoder_no': 0,
                'encoder_ratio': 6,
            },
            {  # AXIS 2 - Front & Back
                'pin_pulse': 17,
                'pin_dir': 16,
                'pin_limit_n': 49,
                'pin_limit_p': 48,
                'microstep': 2500,
                'course': 30500,
                'homing_delay': 800,
                'home_retract': 200,
                'has_encoder': True,
                'encoder_no': 1,
                'encoder_ratio': 6,
            },
        ],
    }
    curves = [CURVE_ROBOT]

    def __init__(self, name, ip, arduino_id):
        self.arduino_id = arduino_id
        super(Robot, self).__init__(name, ip)

    async def send_command(self, command):
        if command['verb'] != 'get_status':
            print(command)
        command.update(arduino_index=self.arduino_id)
        return await super(Robot, self).send_command(command)

    def set_status(self, **kwargs):
        if 'data' in kwargs:
            data = kwargs['data']
            data = data[3:-2]
            data = dict(zip(['enc1', 'enc2', 'di1', 'di2', 'm1', 'm2'], data))

            data['m1'] = MOTOR_STATUS_ENUM[data['m1']]
            data['m2'] = MOTOR_STATUS_ENUM[data['m2']]

            kwargs['data'] = data
        super(Robot, self).set_status(**kwargs)

    async def goto(self, x=None, y=None):
        if x is not None:
            x = {'steps': x, 'absolute': 1}
        else:
            x = {}

        if y is not None:
            y = {'steps': y, 'absolute': 1}
        else:
            y = {}
        return await self.send_command({'verb': 'move_motors', 'moves': [y, x]})


ROBOT_1_IP = '192.168.44.100'
ROBOTS = [
    Robot('Robot 1', ROBOT_1_IP, 0),
    Robot('Robot 2', ROBOT_1_IP, 1),
]
