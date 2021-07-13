import time
import asyncio
from .recipe import *


async def main(system, ALL_NODES):
    stations = await gather_all_nodes(system, ALL_NODES)
    print('all nodes ready')

    # # test valves
    # await test_valve(stations, valve=0, delay=1, count=40)
    # await test_valve(stations, valve=1, delay=1, count=40)
    # await test_valve(stations, valve=2, delay=1.5, count=5)
    # await test_valve(stations, valve=3, delay=1, count=10)
    # await test_valve(stations, valve=4, delay=1, count=40)

    # Motors
    await move_rotary_motor(stations, axis='X', amount=360, feed=10000, count=15, delay=1)
    await move_rotary_motor(stations, axis='X', amount=720, feed=30000, count=15, delay=1)
    # await move_rotary_motor(stations, axis='Y', amount=360, feed=10000, count=15, delay=1)
    # await move_rotary_motor(stations, axis='Y', amount=720, feed=30000, count=15, delay=1)

    # Digital Inputs
    # Encoder
    # Home
    # Race
    return


async def gather_all_nodes(system, ALL_NODES):
    stations = [node for node in ALL_NODES if node.name.startswith('Station ')]

    # All Nodes Ready?
    for station in stations:
        while not station.ready_for_command():
            await asyncio.sleep(.01)

    return stations


async def test_valve(stations, valve, delay, count):
    valves = [0] * 5
    for i in range(count):
        valves[valve] = 1 - (i % 2)
        await run_many(stations, lambda x: x.set_valves(valves))
        await asyncio.sleep(delay)


async def move_rotary_motor(stations, axis, amount, feed, count, delay):
    for i in range(count):
        amount = -amount
        await run_many(stations, lambda x: x.send_command_raw('G10 L20 P1 %s0' % axis))
        await run_many(stations, lambda x: x.send_command_raw('G1 %s%d F%d' % (axis, amount, feed)))
        await asyncio.sleep(delay)


async def do_rail_n_robots(stations, robots, rail, all_nodes, STATUS):
    if stations_only:
        return

    t0 = time.time()
    await do_robots_cap(stations, robots, rail, all_nodes, STATUS)
    print('do_robots_cap:', time.time() - t0)

    t0 = time.time()
    await do_rail(stations, robots, rail, all_nodes, STATUS)
    print('do_rail:', time.time() - t0)

    t0 = time.time()
    await run_many(robots, lambda r: do_robot_pickup(stations, r, rail, all_nodes, STATUS))
    print('do_robot_pickup:', time.time() - t0)


async def do_exchange(stations, robot, rail, all_nodes, STATUS):
    if stations_only or rail_only:
        return
    print('deliver')

    X_INPUT = 375
    Y_INPUT_DOWN_1 = 35
    Y_INPUT_UP = 55
    Y_INPUT_DOWN_3 = 7
    Y_INPUT_DOWN_2 = Y_INPUT_DOWN_3 + 10
    Y_OUTPUT = 80
    X_OUTPUT_SAFE = X_CAPPING

    FEED_Y_PRESS = 3000

    Z_OUTPUT = 70
    Z_OUTPUT_SAFE = Z_OUTPUT - 20

    T_INPUT_RELEASE = 0.5
    T_HOLDER_JACK_CLOSE = 0.5
    T_PRE_PRESS = 0.2
    T_POST_PRESS = 0.2
    T_OUTPUT_GRIPP = 0.1
    T_OUTPUT_RELEASE = 0.2

    await robot.G1(x=X_INPUT, feed=FEED_X)
    await robot.G1(y=Y_INPUT_DOWN_1, feed=FEED_Y_DOWN)
    await robot.set_valves([0] * 10)
    await asyncio.sleep(T_INPUT_RELEASE)

    async def robot_press():
        await robot.G1(y=Y_INPUT_UP, feed=FEED_Y_UP)
        await robot.set_valves([0] * 5 + [1] * 5)
        await asyncio.sleep(T_HOLDER_JACK_CLOSE)
        await robot.G1(y=Y_INPUT_DOWN_2, feed=FEED_Y_DOWN)
        await asyncio.sleep(T_PRE_PRESS)
        await robot.G1(y=Y_INPUT_DOWN_3, feed=FEED_Y_PRESS)
        await asyncio.sleep(T_POST_PRESS)

    async def station_down(station):
        await station.G1(z=Z_OUTPUT, feed=FEED_Z_DOWN / 4.0)

    await asyncio.gather(
        robot_press(),
        run_many(stations, lambda x: station_down(x)),
    )

    await robot.G1(y=Y_OUTPUT, feed=FEED_Y_UP)
    await robot.set_valves([1] * 5)

    await asyncio.sleep(T_OUTPUT_GRIPP)

    async def station_release(station):
        await station.set_valves([0, 1])
        await asyncio.sleep(T_OUTPUT_RELEASE)
        await station.G1(z=Z_OUTPUT_SAFE, feed=FEED_Z_UP)

    await run_many(stations, lambda x: station_release(x))

    # Start Align Holder
    create_station_holder_align_task(
        stations, robot, rail, all_nodes, STATUS)

    await robot.G1(x=X_OUTPUT_SAFE, feed=FEED_X)

    STATUS['robots_full'] = True


ALIGN_HOLDER_TASK = {}


def create_station_holder_align_task(stations, robots, rail, all_nodes, STATUS):
    for station in stations:
        ALIGN_HOLDER_TASK[station.name] = asyncio.create_task(station.send_command(
            {'verb': 'align', 'component': 'holder', 'speed': ALIGN_SPEED_HOLDER, 'retries': 10}))


async def do_stations(stations, robots, rail, all_nodes, STATUS):
    if rail_only:
        return
    global ALIGN_HOLDER_TASK
    if not ALIGN_HOLDER_TASK:
        await run_many(stations, lambda x: x.set_valves([0, 1]))
        create_station_holder_align_task(
            stations, robots, rail, all_nodes, STATUS)

    tasks = []
    for station in stations:
        tasks.append(do_station(station, STATUS,
                                ALIGN_HOLDER_TASK[station.name]))

    res = await asyncio.gather(*tasks)
    for station_index in range(len(stations)):
        success, message = res[station_index]
        station = stations[station_index]
        if message:
            input(station.name + message)

    ALIGN_HOLDER_TASK = {}
    if stations_only:
        await asyncio.sleep(2)
        await run_many(stations, lambda x: x.set_valves([0]))


async def do_station(station, STATUS, align_holder_task):
    t0 = time.time()

    data = {}
    # go to aliging location
    data['H_ALIGNING'] = station.hw_config['H_ALIGNING']
    data['FEED_ALIGNING'] = FEED_Z_DOWN

    # Fall
    data['PAUSE_FALL_DOSING'] = 0.05

    # Ready to push
    data['H_READY_TO_PUSH'] = data['H_ALIGNING'] - 8
    data['FEED_READY_TO_PUSH'] = FEED_Z_UP
    data['PAUSE_READY_TO_PUSH'] = 0.05

    # Push
    data['H_PUSH'] = station.hw_config['H_PUSH']
    data['FEED_PUSH'] = FEED_Z_DOWN / 3.0
    data['PAUSE_PUSH'] = 0.1
    data['H_PUSH_BACK'] = data['H_PUSH'] - 5
    data['FEED_PUSH_BACK'] = FEED_Z_UP

    # Dance
    data['PAUSE_JACK_PRE_DANCE_1'] = 0.05
    data['PAUSE_JACK_PRE_DANCE_2'] = 0.05
    data['PAUSE_JACK_PRE_DANCE_3'] = 0.05
    data['H_PRE_DANCE'] = station.hw_config['H_PRE_DANCE']
    data['FEED_PRE_DANCE'] = FEED_Z_UP

    dance_rev = 1
    charge_h = 0.1
    data['H_DANCE'] = data['H_PRE_DANCE'] - ((11 + charge_h) * dance_rev)
    data['Y_DANCE'] = 360 * dance_rev
    data['FEED_DANCE'] = FEED_DANCE

    # Press
    data['PAUSE_PRESS0'] = 0.1
    data['PAUSE_PRESS1'] = 0.3
    data['PAUSE_PRESS2'] = 0.5

    # Dance Back
    data['PAUSE_JACK_PRE_DANCE_BACK'] = .2
    data['PAUSE_POST_DANCE_BACK'] = .3

    data['H_DANCE_BACK'] = data['H_DANCE'] + (charge_h * dance_rev)
    data['H_DANCE_BACK2'] = data['H_PRE_DANCE']
    data['Y_DANCE_BACK'] = 0
    data['Y_DANCE_BACK2'] = -40
    data['FEED_DANCE_BACK'] = data['FEED_DANCE']

    # Deliver
    data['H_DELIVER'] = .5
    data['FEED_DELIVER'] = FEED_Z_UP

    async def ignore(station, data):
        await station.G1(z=data['H_DELIVER'], feed=data['FEED_DELIVER'])
        await station.set_valves([0, 0, 0, 1, 0])

    async def come_down(station, data):
        await station.G1(z=data['H_ALIGNING'], feed=data['FEED_ALIGNING'])
        await station.set_valves([1])

    async def deliver(station, data):
        await station.G1(z=data['H_DELIVER'], feed=data['FEED_DELIVER'])
        await station.set_valves([None, None, None, 1])

    async def process(station, data):
        command = '''
            ; release dosing
            M100 ({out1: 0, out4: 0})
            G4 P%(PAUSE_FALL_DOSING).2f

            ; ready to push
            G1 Z%(H_READY_TO_PUSH).2f F%(FEED_READY_TO_PUSH)d
            M100 ({out1: 1})
            G4 P%(PAUSE_READY_TO_PUSH).2f

            ; push and come back
            G1 Z%(H_PUSH).2f F%(FEED_PUSH)d
            G4 P%(PAUSE_PUSH).2f
            G1 Z%(H_PUSH_BACK).2f F%(FEED_PUSH_BACK)d

            ; prepare for dance
            G10 L20 P1 Y0
            M100 ({out1: 0, out4: 1})
            G4 P%(PAUSE_JACK_PRE_DANCE_1).2f
            G1 Z%(H_PRE_DANCE).2f F%(FEED_PRE_DANCE)d
            G4 P%(PAUSE_JACK_PRE_DANCE_2).2f
            M100 ({out1: 1})
            G4 P%(PAUSE_JACK_PRE_DANCE_3).2f

            ; dance
            G1 Z%(H_DANCE).2f Y%(Y_DANCE).2f F%(FEED_DANCE)d

            ; press
            M100 ({out1: 0, out2: 0, out4: 0})
            G4 P%(PAUSE_PRESS0).2f
            M100 ({out5: 1})
            G4 P%(PAUSE_PRESS1).2f
            M100 ({out3: 1})
            G4 P%(PAUSE_PRESS2).2f
            M100 ({out3: 0})

            ; dance back
            M100 ({out1: 1, out4: 1, out5: 0})
            G4 P%(PAUSE_JACK_PRE_DANCE_BACK).2f

            G1 Z%(H_DANCE_BACK).2f F5000
            G1 Z%(H_DANCE_BACK2).2f Y%(Y_DANCE_BACK).2f F%(FEED_DANCE_BACK)d
            G1 Y%(Y_DANCE_BACK2).2f F%(FEED_DANCE_BACK)d
            M100 ({out4: 0})
            G4 P%(PAUSE_POST_DANCE_BACK).2f
        ''' % data
        await station.send_command_raw(command)

    _, holder_res = await align_holder_task

    if holder_res['exists'] and not holder_res['aligned']:
        await ignore(station, data)
        return False, 'couldnt align holder, remove objects'

    await come_down(station, data)
    print('aligning 1', station.ip, time.time() - t0)
    t0 = time.time()

    _, dosgin_res = await station.send_command({'verb': 'align', 'component': 'dosing', 'speed': ALIGN_SPEED_DOSING, 'retries': 10})

    if dosgin_res['exists'] and not dosgin_res['aligned']:
        await ignore(station, data)
        return False, 'couldnt align dosing, remove objects'

    if (not dosgin_res['exists']) and (not holder_res['exists']):
        await ignore(station, data)
        return False, ''

    if (not dosgin_res['exists']) or (not holder_res['exists']):
        await ignore(station, data)
        return False, 'a component is missing, remove objects'

    print('aligning 2', station.ip, time.time() - t0)
    t0 = time.time()

    await process(station, data)
    await deliver(station, data)
    print('aligning 3', station.ip, time.time() - t0)
    return True, ''


async def do_robots_cap(stations, robots, rail, all_nodes, STATUS):
    if rail_only:
        return
    if not STATUS['robots_full']:
        return

    print('Capping')

    async def swap_rail_jacks_1(rail):
        await rail.set_valves([1, 0])
        await asyncio.sleep(T_RAIL_MOVING_JACK)
        await rail.set_valves([1, 1])

    async def swap_rail_jacks_2(rail):
        await rail.set_valves([1, 0])
        await asyncio.sleep(T_RAIL_FIXED_JACK)
        await rail.set_valves([0, 0])

    await asyncio.gather(
        swap_rail_jacks_1(rail),
        run_many(robots, lambda r: r.G1(x=X_CAPPING, feed=FEED_X)),
    )

    await run_many(robots, lambda r: r.G1(y=Y_CAPPING_DOWN_1, feed=FEED_Y_DOWN))

    await asyncio.gather(
        swap_rail_jacks_2(rail),
        run_many(robots, lambda r: r.G1(
            y=Y_CAPPING_DOWN_2, feed=FEED_Y_CAPPING))
    )

    await run_many(robots, lambda r: r.set_valves([0] * 10))

    await run_many(robots, lambda r: r.G1(x=X_PARK, feed=FEED_X))


async def do_robot_pickup(stations, robot, rail, all_nodes, STATUS):
    if rail_only:
        return
    print('lets go grab input')

    data = {}
    Y_GRAB_IN_UP_1 = 65
    X_GRAB_IN = 284.5
    Y_GRAB_IN_DOWN = 0
    Y_GRAB_IN_UP_2 = Y_GRAB_IN_UP_1

    T_GRAB_IN = 0.5

    await robot.G1(y=Y_GRAB_IN_UP_1, feed=FEED_Y_UP)
    await robot.G1(x=X_GRAB_IN, feed=FEED_X)
    await robot.G1(y=Y_GRAB_IN_DOWN, feed=FEED_Y_DOWN)

    await robot.set_valves([1] * 10)
    await asyncio.sleep(T_GRAB_IN)

    await robot.G1(y=Y_GRAB_IN_UP_2, feed=FEED_Y_UP)


async def do_rail(stations, robots, rail, all_nodes, STATUS):
    task2 = run_many(robots, lambda r: r.G1(y=Y_PARK, feed=FEED_Y_UP / 5.0))

    D_MIN = D_STANDBY - 125
    D_MAX = D_MIN + 25 * 5  # 10

    T_RAIL_JACK1 = .4
    T_RAIL_JACK2 = .7

    # rail backward
    await rail.G1(z=D_MIN, feed=FEED_RAIL_FREE)

    # change jacks to moving
    await rail.set_valves([1, 0])
    await asyncio.sleep(T_RAIL_JACK1)
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

    await task2


def run_many(nodes, func):
    tasks = []
    for node in nodes:
        tasks.append(func(node))

    return asyncio.gather(*tasks)