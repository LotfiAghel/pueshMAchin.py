import time
import asyncio
import aioconsole
from .recipe import *


async def main(system, ALL_NODES):
    all_nodes, feeder, rail, robots, stations = await gather_all_nodes(system, ALL_NODES)
    robot = robots[0]

    a = await aioconsole.ainput('type anything to home. or enter to dismiss')
    if a:
        print('homing')
        await home_all_nodes(all_nodes, feeder, rail, robots, stations)
    for station in stations:
        await station.set_valves([None, None, None, 1])

    # await rail.home()

    # for i in range(20):
    #     await rail.set_valves([(i + 1) % 2, 0])
    #     await asyncio.sleep(.5)
    # return

    # for i in range(20):
    #     await robot.set_valves([(i + 1) % 2] * 10)
    #     await asyncio.sleep(.5)
    # return

    while True:
        # '''PICK UP'''
        # await get_input(system, 'pick up')
        # Y_GRAB_IN_UP_1 = 75
        # X_GRAB_IN = 284.5
        # Y_GRAB_IN_DOWN = 0
        # Y_GRAB_IN_UP_2 = 65
        # T_GRAB_IN = 0.5
        # await robot.G1(y=Y_GRAB_IN_UP_1, feed=FEED_Y_UP)
        # await robot.G1(x=X_GRAB_IN, feed=FEED_X)
        # await robot.G1(y=Y_GRAB_IN_DOWN, feed=FEED_Y_DOWN)
        # await robot.set_valves_grab_infeed()
        # await asyncio.sleep(T_GRAB_IN)
        # await robot.G1(y=Y_GRAB_IN_UP_2, feed=FEED_Y_UP)
        #
        # '''EXCHANGE'''
        # # await get_input(system, 'exchange')
        # X_INPUT = 375
        # Y_INPUT_DOWN_1 = 35
        # Y_INPUT_UP = 55
        # Y_INPUT_DOWN_3 = 7
        # Y_INPUT_DOWN_2 = Y_INPUT_DOWN_3 + 10
        # Y_OUTPUT = 80
        # X_OUTPUT_SAFE = X_CAPPING
        #
        # FEED_Y_PRESS = 3000
        #
        # Z_OUTPUT = 70
        # Z_OUTPUT_SAFE = Z_OUTPUT - 20
        #
        # T_INPUT_RELEASE = 0.5
        # T_HOLDER_JACK_CLOSE = 0.5
        # T_PRE_PRESS = 0.2
        # T_POST_PRESS = 0.2
        # T_OUTPUT_GRIPP = 0.1
        # T_OUTPUT_RELEASE = 0.2
        #
        # await robot.G1(x=X_INPUT, feed=FEED_X)
        # await robot.G1(y=Y_INPUT_DOWN_1, feed=FEED_Y_DOWN)
        # await robot.set_valves([0] * 10)
        # await asyncio.sleep(T_INPUT_RELEASE)
        #
        # await robot.G1(y=Y_INPUT_UP, feed=FEED_Y_UP)
        # await robot.set_valves([0] * 5 + [1] * 5)
        # await asyncio.sleep(T_HOLDER_JACK_CLOSE)
        # await robot.G1(y=Y_INPUT_DOWN_2, feed=FEED_Y_DOWN)
        # await asyncio.sleep(T_PRE_PRESS)
        # await robot.G1(y=Y_INPUT_DOWN_3, feed=FEED_Y_PRESS)
        # await asyncio.sleep(T_POST_PRESS)
        #
        # await do_stations(stations, lambda s: s.G1(z=Z_OUTPUT, feed=FEED_Z_DOWN / 4.0))
        # await robot.G1(y=Y_OUTPUT, feed=FEED_Y_UP)
        # await robot.set_valves([1] * 5)
        # await do_stations(stations, lambda s: s.set_valves([0, 0, 0, 1]))
        #
        # await asyncio.sleep(T_OUTPUT_GRIPP)
        #
        # await do_stations(stations, lambda s: s.set_valves([0, 1]))
        # await asyncio.sleep(T_OUTPUT_RELEASE)
        # await do_stations(stations, lambda s: s.G1(z=Z_OUTPUT_SAFE, feed=FEED_Z_UP))
        #
        # await robot.G1(x=X_OUTPUT_SAFE, feed=FEED_X)
        #
        # '''CAP'''
        # # await get_input(system, 'cap')
        # await rail.set_valves([1, 0])
        # await asyncio.sleep(T_RAIL_MOVING_JACK)
        # await rail.set_valves([1, 1])
        # await robot.G1(x=X_CAPPING, feed=FEED_X)
        # await robot.G1(y=Y_CAPPING_DOWN_1, feed=FEED_Y_DOWN)
        # await rail.set_valves([1, 0])
        # await asyncio.sleep(T_RAIL_FIXED_JACK)
        # await rail.set_valves([0, 0])
        # await robot.G1(y=Y_CAPPING_DOWN_2, feed=FEED_Y_CAPPING)
        # await robot.set_valves([0] * 10)
        # await robot.G1(x=X_PARK, feed=FEED_X)
        # await robot.G1(y=Y_PARK, feed=FEED_Y_UP)

        ''' FEEDER '''
        await get_input(system, 'feeder')
        await feeder.G1(z=16, feed=5000)
        await feeder.send_command({'verb': 'feeder_process', 'N': N})

        ''' RAIL '''
        # await get_input(system, 'rail')
        D_MIN = D_STANDBY - 25 * N
        D_MAX = D_STANDBY
        T_RAIL_JACK1 = 1.5
        T_RAIL_JACK2 = 1.5

        # rail backward
        await rail.G1(z=D_MIN, feed=FEED_RAIL_FREE)

        # change jacks to moving
        await rail.set_valves([1, 0])
        await asyncio.sleep(T_RAIL_JACK1)
        await feeder.set_valves([None, 0])
        await rail.set_valves([1, 1])
        await asyncio.sleep(T_RAIL_JACK2)

        # rail forward
        await rail.G1(z=D_MAX, feed=FEED_RAIL_INTACT)

        # change jacks to moving
        await rail.set_valves([1, 0])
        await asyncio.sleep(T_RAIL_JACK1)
        await rail.set_valves([0, 0])
        await asyncio.sleep(T_RAIL_JACK1)

        # rail park
        await rail.G1(z=D_STANDBY, feed=FEED_RAIL_FREE)

        # ''' STATION::Align Holder '''
        # async def align_holder(station):
        #     await get_input(system, 'STATION::Align Holder')
        #     await station.set_valves([0, 1])
        #     z1, z2 = await station.send_command({'verb': 'align', 'component': 'holder', 'speed': ALIGN_SPEED_HOLDER, 'retries': 10}, assert_success=False)
        #     print(z1, z2)
        #     if (not z1) or (not z2['aligned']):
        #         await aioconsole.ainput('aligining failed. align to continue')
        # await do_stations(stations, lambda s: align_holder(s))
        #
        # ''' STATION::Align Dosing '''
        # async def align_dosing(station):
        #     await get_input(system, 'STATION::Align Dosing')
        #     data = {}
        #     data['H_ALIGNING'] = station.hw_config['H_ALIGNING']
        #     data['FEED_ALIGNING'] = FEED_Z_DOWN
        #     await station.G1(z=data['H_ALIGNING'], feed=data['FEED_ALIGNING'])
        #     await station.set_valves([1])
        #     z1, z2 = await station.send_command({'verb': 'align', 'component': 'dosing', 'speed': ALIGN_SPEED_DOSING, 'retries': 10}, assert_success=False)
        #     print(z1, z2)
        #     if (not z1) or (not z2['aligned']):
        #         await aioconsole.ainput('aligining failed. align to continue')
        # await do_stations(stations, lambda s: align_dosing(s))
        #
        # ''' STATION::Rest '''
        # async def station_rest(station):
        #     await get_input(system, 'STATION::Rest')
        #     data = {}
        #     # go to aliging location
        #     data['H_ALIGNING'] = station.hw_config['H_ALIGNING']
        #     data['FEED_ALIGNING'] = FEED_Z_DOWN
        #
        #     # Fall
        #     data['PAUSE_FALL_DOSING'] = 0.05
        #
        #     # Ready to push
        #     data['H_READY_TO_PUSH'] = data['H_ALIGNING'] - 8
        #     data['FEED_READY_TO_PUSH'] = FEED_Z_UP
        #     data['PAUSE_READY_TO_PUSH'] = 0.05
        #
        #     # Push
        #     data['H_PUSH'] = station.hw_config['H_PUSH']
        #     data['FEED_PUSH'] = FEED_Z_DOWN / 3.0
        #     data['PAUSE_PUSH'] = 0.1
        #     data['H_PUSH_BACK'] = data['H_PUSH'] - 5
        #     data['FEED_PUSH_BACK'] = FEED_Z_UP
        #
        #     # Dance
        #     data['PAUSE_JACK_PRE_DANCE_1'] = 0.05
        #     data['PAUSE_JACK_PRE_DANCE_2'] = 0.05
        #     data['PAUSE_JACK_PRE_DANCE_3'] = 0.05
        #     data['H_PRE_DANCE'] = station.hw_config['H_PRE_DANCE']
        #     data['FEED_PRE_DANCE'] = FEED_Z_UP
        #
        #     dance_rev = 1
        #     charge_h = 0.1
        #     data['H_DANCE'] = data['H_PRE_DANCE'] - \
        #         ((11 + charge_h) * dance_rev)
        #     data['Y_DANCE'] = 360 * dance_rev
        #     data['FEED_DANCE'] = FEED_DANCE
        #
        #     # Press
        #     data['PAUSE_PRESS0'] = 0.1
        #     data['PAUSE_PRESS1'] = 0.3
        #     data['PAUSE_PRESS2'] = 0.5
        #
        #     # Dance Back
        #     data['PAUSE_JACK_PRE_DANCE_BACK'] = .2
        #     data['PAUSE_POST_DANCE_BACK'] = .3
        #
        #     data['H_DANCE_BACK'] = data['H_DANCE'] + (charge_h * dance_rev)
        #     data['H_DANCE_BACK2'] = data['H_PRE_DANCE']
        #     data['Y_DANCE_BACK'] = 0
        #     data['Y_DANCE_BACK2'] = -40
        #     data['FEED_DANCE_BACK'] = data['FEED_DANCE']
        #
        #     # Deliver
        #     data['H_DELIVER'] = .5
        #     data['FEED_DELIVER'] = FEED_Z_UP
        #
        #     command = '''
        #         ; release dosing
        #         M100 ({out1: 0, out4: 0})
        #         G4 P%(PAUSE_FALL_DOSING).2f
        #
        #         ; ready to push
        #         G1 Z%(H_READY_TO_PUSH).2f F%(FEED_READY_TO_PUSH)d
        #         M100 ({out1: 1})
        #         G4 P%(PAUSE_READY_TO_PUSH).2f
        #
        #         ; push and come back
        #         G1 Z%(H_PUSH).2f F%(FEED_PUSH)d
        #         G4 P%(PAUSE_PUSH).2f
        #         G1 Z%(H_PUSH_BACK).2f F%(FEED_PUSH_BACK)d
        #
        #         ; prepare for dance
        #         G10 L20 P1 Y0
        #         M100 ({out1: 0, out4: 1})
        #         G4 P%(PAUSE_JACK_PRE_DANCE_1).2f
        #         G1 Z%(H_PRE_DANCE).2f F%(FEED_PRE_DANCE)d
        #         G4 P%(PAUSE_JACK_PRE_DANCE_2).2f
        #         M100 ({out1: 1})
        #         G4 P%(PAUSE_JACK_PRE_DANCE_3).2f
        #
        #         ; dance
        #         G1 Z%(H_DANCE).2f Y%(Y_DANCE).2f F%(FEED_DANCE)d
        #
        #         ; press
        #         M100 ({out1: 0, out2: 0, out4: 0})
        #         G4 P%(PAUSE_PRESS0).2f
        #         M100 ({out5: 1})
        #         G4 P%(PAUSE_PRESS1).2f
        #         M100 ({out3: 1})
        #         G4 P%(PAUSE_PRESS2).2f
        #         M100 ({out3: 0})
        #
        #         ; dance back
        #         M100 ({out1: 1, out4: 1, out5: 0})
        #         G4 P%(PAUSE_JACK_PRE_DANCE_BACK).2f
        #
        #         G1 Z%(H_DANCE_BACK).2f F5000
        #         G1 Z%(H_DANCE_BACK2).2f Y%(Y_DANCE_BACK).2f F%(FEED_DANCE_BACK)d
        #         G1 Y%(Y_DANCE_BACK2).2f F%(FEED_DANCE_BACK)d
        #         M100 ({out4: 0})
        #         G4 P%(PAUSE_POST_DANCE_BACK).2f
        #     ''' % data
        #     await station.send_command_raw(command)
        #
        #     await station.G1(z=data['H_DELIVER'], feed=data['FEED_DELIVER'])
        #     await station.set_valves([None, None, None, 1])
        # await do_stations(stations, lambda s: station_rest(s))


async def home_all_nodes(all_nodes, feeder, rail, robots, stations):
    await do_stations(stations, lambda s: s.home(), simultanously=True)
    await robots[0].home()
    await rail.home()
    await rail.G1(z=D_STANDBY, feed=FEED_RAIL_FREE * .6)
    await feeder.home()

    await feeder.set_motors(
        (2, 4), (3, 3),  # Holder Downstream
        (1, 26), (4, 8), (7, 46),  # Holder Upstream - Lift and long conveyor
        (6, 32), (8, 200)  # Cartridge Conveyor + OralB
    )


async def get_input(system, text):
    # await system.system_running.wait()
    print(text)
    try:
        a = await aioconsole.ainput('? - Type anything to stop... - Just enter to continue')
    except:
        a = '-'
    if a:
        raise


async def do_stations(stations, func, simultanously=False):
    if simultanously:
        res = await async.gather(*[func(station) for station in stations], return_exceptions=True)
        for i in range(len(stations)):
            if res[i]:
                print('error while running for %dth station' % (i + 1))
                print(res[i])
                await aioconsole.ainput('enter to continue')
    else:
        for station in stations:
            try:
                await func(station)
            except:
                print(traceback.format_exc())
                await aioconsole.ainput('enter to continue')