from .node import Node
import asyncio
import time


class Robot(Node):
    type = 'robot'
    arduino_reset_pin = 2
    HOMMED_AXES = ['x', 'y']
    AUTO_CLEAR_HOLD = True
    g2core_config_base = [
        # X - Holder Motor
        (1, {
            'ma': 0,  # map to X
            'sa': 1.8,  # step angle 1.8
            'tr': 20,  # travel per rev = 20mm
            'mi': 2,  # microstep = 2
            'po': 1,  # direction
        }),
        ('x', {
            'am': 1,  # standard axis mode
            'vm': 50000,  # max speed
            'fr': 50000,  # max feed rate
            'jm': 10000,  # max jerk
            'jh': 6000,  # hominzg jerk
            'tn': 0,  # min travel
            'tm': 400,  # max travel
            'hi': 1,  # home switch
            'hd': 0,  # homing direction
            'sv': 1000,  # home search speed
            'lv': 200,  # latch speed
            'lb': 10,  # latch backoff; if home switch is active at start
            'zb': 1,  # zero backoff
        }),
        ('di1mo', 1),  # Homing Switch - Mode = Active High - NC
        ('di1ac', 0),
        ('di1fn', 0),
        ('di2mo', 1),  # Limit Switch + - Mode = Active High - NC
        ('di2ac', 0),  # Limit Switch + - Action = Fast Stop
        ('di2fn', 0),  # Limit Switch + - Function = Limit

        # Y - Dosing Motor
        (2, {
            'ma': 1,  # map to Y
            'sa': 1.8,  # step angle 1.8
            'tr': 20,  # travel per rev = 20mm
            'mi': 4,  # microstep = 2
            'po': 1,  # direction
        }),
        ('y', {
            'am': 1,  # standard axis mode
            'vm': 50000,  # max speed
            'fr': 50000,  # max feed rate
            'jm': 9000,  # max jerk
            'jh': 8000,  # homing jerk
            'tn': 0,  # min travel
            'tm': 100,  # max travel
            'hi': 3,  # home switch
            'hd': 0,  # homing direction
            'sv': 1000,  # home search speed
            'lv': 200,  # latch speed
            'lb': 10,  # latch backoff; if home switch is active at start
            'zb': 1,  # zero backoff
        }),
        ('di3mo', 1),  # Homing Switch - Mode = Active High - NC
        ('di3ac', 0),
        ('di3fn', 0),
        ('di4mo', 1),  # Limit Switch + - Mode = Active High - NC
        ('di4ac', 0),  # Limit Switch + - Action = Fast Stop
        ('di4fn', 0),  # Limit Switch + - Function = Limit
        ('jt', 1.00),
        ('gpa', 2),  # equivalent of G64
        ('sv', 2),  # Status report enabled
        ('sr', {'uda0': True, 'posx': True, 'posy': True, 'stat': True}),
        ('si', 250),  # also every 250ms

        ('jt', 1.2),
        ('ct', 2),
    ]

    hw_config_base = {
        'valves': {
            'dosing1': 1,
            'dosing2': 2,
            'dosing3': 3,
            'dosing4': 4,
            'dosing5': 5,
            'holder1': 6,
            'holder2': 7,
            'holder3': 8,
            'holder4': 9,
            'holder5': 10,
        },
        'di': {
            'x-': 1,
            'x+': 2,
            'y-': 3,
            'y-': 4,
        },
        'encoders': {
            # encoder key, ratio, telorance_soft, telorance_hard
            'posx': ['enc2', 120.0, 1.0, 5.0],
            'posy': ['enc1', 120.0, 1.0, 5.0],
        },
        'eac': [600, 600],
        'X_GRAB_IN': 284.5,
        'X_INPUT': 373,
        'Y_GRAB_IN_UP_2': 64,
        'X_CAPPING': 60,
    }

    def __init__(self, *args, **kwargs):
        self._stations = set()
        self._stations_slot = [None] * 5
        super().__init__(*args, **kwargs)

    async def home_core(self):
        await self.send_command_raw('G28.2 X0')
        await self.send_command_raw('G28.2 Y0')

        # reset encoder
        await self.send_command_raw('G28.5')
        await self.send_command_raw('G1 X1 Y1 F1000')
        await self.send_command_raw('G1 X0 Y0 F1000')

    def add_station(self, station, index):
        self._stations.add(station)
        self._stations_slot[index] = station

    async def set_valves_grab_infeed(self):
        mask = [0] * 5
        for i in range(5):
            if self._stations_slot[i]:
                mask[5 - i - 1] = 1
        mask = mask * 2
        await self.set_valves(mask)

    async def do_robot(self):
        self.update_recipe()
        # ensure about stations
        stations_task1 = asyncio.gather(
            *[station.clearance() for station in self._stations])

        '''PICK UP'''
        Y_GRAB_IN_UP_1 = 75
        X_GRAB_IN = self.hw_config['X_GRAB_IN']
        Y_GRAB_IN_DOWN = 0
        Y_GRAB_IN_UP_2 = self.hw_config['Y_GRAB_IN_UP_2']
        T_GRAB_IN = 0.75

        await self.system.system_running.wait()

        await self.send_command_raw(f'''
            G1 Y{Y_GRAB_IN_UP_1} F{self.recipe.FEED_Y_UP}
            G1 X{X_GRAB_IN} F{self.recipe.FEED_X_FORWARD}
            G1 Y{Y_GRAB_IN_DOWN} F{self.recipe.FEED_Y_DOWN}
        ''')

        await self.set_valves_grab_infeed()

        await self.send_command_raw(f'''
            G4 P{T_GRAB_IN:.2f}
            G1 Y{Y_GRAB_IN_UP_2} F{self.recipe.FEED_Y_UP}
        ''')

        '''EXCHANGE'''
        X_CAPPING = self.hw_config['X_CAPPING']

        X_INPUT = self.hw_config['X_INPUT']
        X_PRESS = X_INPUT - 3
        Y_INPUT_DOWN_RELEASE_HOLDER = 36
        Y_INPUT_DOWN_RELEASE_DOSING = 32
        Y_INPUT_UP = 55 + 10
        Y_INPUT_DOWN_PRESS_HOLDER = 6
        Y_INPUT_DOWN_PRE_PRESS_HOLDER = Y_INPUT_DOWN_PRESS_HOLDER + 10
        Y_OUTPUT = 80

        T_INPUT_RELEASE = 1.0
        T_HOLDER_JACK_CLOSE = 0.1
        T_PRE_PRESS = 0.05
        T_POST_PRESS = 0.1
        T_OUTPUT_GRIPP = 0.1
        T_OUTPUT_RELEASE = 0.2

        # ensure about stations
        await stations_task1
        await self.system.system_running.wait()

        await self.send_command_raw(f'''
            G1 X{X_INPUT} F{self.recipe.FEED_X_SHORT}
            G1 Y{Y_INPUT_DOWN_RELEASE_HOLDER} F{self.recipe.FEED_Y_DOWN_PRESS}
            M100 ({{out: {{6:0,7:0,8:0,9:0,10:0}}}})
            G1 Y{Y_INPUT_DOWN_RELEASE_DOSING} F{self.recipe.FEED_Y_DOWN_PRESS}
            M100 ({{out: {{1:0,2:0,3:0,4:0,5:0}}}})
        ''')

        async def stations_verify_and_deliver():
            await asyncio.sleep(T_INPUT_RELEASE)
            await asyncio.gather(*[station.verify_dosing_sit_right_and_come_down() for station in self._stations])

        stations_task = asyncio.create_task(stations_verify_and_deliver())

        await self.send_command_raw(f'''
            G1 Y{Y_INPUT_UP} X{X_PRESS} F{self.recipe.FEED_Y_UP}
            M100 ({{out: {{1:0,2:0,3:0,4:0,5:0}}}})
            M100 ({{out: {{6:1,7:1,8:1,9:1,10:1}}}})
            G4 P{T_HOLDER_JACK_CLOSE:.2f}
            G1 Y{Y_INPUT_DOWN_PRE_PRESS_HOLDER} F{self.recipe.FEED_Y_DOWN}
            G4 P{T_PRE_PRESS:.2f}
            G1 Y{Y_INPUT_DOWN_PRESS_HOLDER} F{self.recipe.FEED_Y_DOWN_PRESS}
            G4 P{T_POST_PRESS:.2f}
            G1 Y{Y_INPUT_DOWN_PRE_PRESS_HOLDER} X{X_INPUT} F{self.recipe.FEED_Y_DOWN}

        ''')

        await stations_task

        await self.send_command_raw(f'''
            G1 Y{Y_OUTPUT} F{self.recipe.FEED_Y_UP}
            M100 ({{out: {{1:1,2:1,3:1,4:1,5:1}}}})
            M100 ({{out: {{6:0,7:0,8:0,9:0,10:0}}}})
        ''')

        await asyncio.sleep(T_OUTPUT_GRIPP)

        await asyncio.gather(*[station.set_valves([0, 0, 0, 1]) for station in self._stations])
        await asyncio.sleep(T_OUTPUT_RELEASE)
        await asyncio.gather(*[station.G1(z=self.recipe.STATION_Z_OUTPUT_SAFE, feed=self.recipe.FEED_Z_UP) for station in self._stations])
        for station in self._stations:
            station.station_is_full_event.set()

        ''' Move out / CAP'''
        STATION_SAFE_LIMIT = 310

        t1 = asyncio.create_task(self.send_command_raw(f'''
            G1 X{X_CAPPING} F{self.recipe.FEED_X_BACKWARD}
        '''))

        while self.get_enc_loc('x') > STATION_SAFE_LIMIT:
            await asyncio.sleep(0.002)

        for station in self._stations:
            station.station_is_safe_event.set()

        await self.send_command_raw(f'''
            G1 Y{self.recipe.Y_CAPPING_DOWN} F{self.recipe.FEED_Y_DOWN_CAP}
            M100 ({{out: {{1:0,2:0,3:0,4:0,5:0}}}})
            G4 P.35
            G1 X{self.recipe.X_PARK} F{self.recipe.FEED_X_BACKWARD}
        ''')

    async def do_robot_park(self):
        await self.system.system_running.wait()

        # await self.send_command_raw(f'''
        #     G1 Y{self.recipe.Y_PARK} F{self.recipe.FEED_Y_UP/10}
        # ''')
        await self.G1(y=self.recipe.Y_PARK, feed=self.recipe.FEED_Y_UP / 10, correct_initial=True)
        await self.G1(x=self.recipe.X_PARK - 1, feed=self.recipe.FEED_X_BACKWARD / 40, correct_initial=True)
