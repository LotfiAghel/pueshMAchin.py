import asyncio
import time


async def feeder_process(arduino, G1, command):
    N = command['N']

    arduino._send_command("{out2: 1}")
    await asyncio.sleep(.1)
    arduino._send_command("{out7: 1}")
    await asyncio.sleep(.3)
    # await cartridge_repeat_home(arduino)
    for i in range(N + 1):
        z = 16 + 25 * i
        await G1({'arduino_index': None, 'z': z, 'feed': 6000}, None)

        # if i > 0:
        #     await cartridge_feed(arduino, None)
        if i > (N - 2):
            arduino._send_command("{out7: 0}")
        # if i > 0:
        #     await cartridge_handover(arduino, None)

        await asyncio.sleep(.5)

    await G1({'arduino_index': None, 'z': 719, 'feed': 6000}, None)


async def cartridge_feed(arduino, cartridge_lock):
    # async with cartridge_lock:
    # rotate to upstream

    # Vacuum
    # bring jack down + Vacuum On
    arduino._send_command("{out9: 1, out13: 1, out8: 1}")
    arduino._send_command("G1 Y100 F60000")
    await asyncio.sleep(.24)

    # Cartridge Pusher
    arduino._send_command("{out4: 1}")  # push cartridge forward
    await asyncio.sleep(.02)

    # bring jack up
    arduino._send_command("{out9: 0}")  # bring jack up
    await asyncio.sleep(.1)

    # Cartridge Pusher back
    arduino._send_command("{out4: 0}")  # pull cartridge pusher back
    await asyncio.sleep(.02)

    # rotate to rail
    arduino._send_command("G1 Y10 F25000")
    # await asyncio.sleep(.5)


async def cartridge_handover(arduino, cartridge_lock):
    # async with cartridge_lock:

    # release vacuum
    # arduino._send_command("{out9: 0}")  # bring jack down at end
    # await asyncio.sleep(.1)
    # arduino._send_command("{out13: 0}")
    # await asyncio.sleep(.1)

    command_id = arduino.get_command_id()
    command_raw = '''
        G38.3 Y-100 F1000
        G10 L20 P1 Y0
        M100 ({out13: 0, out8: 0})
        N%d M0
        ''' % command_id
    arduino.send_command(command_raw)
    await arduino.wait_for_command_id(command_id)


async def cartridge_repeat_home(arduino):
    command_id = arduino.get_command_id()
    command_raw = '''
        G1 Y20 F60000
        G38.3 Y-100 F1000
        G10 L20 P1 Y0
        N%d M0
        ''' % command_id
    arduino.send_command(command_raw)
    await arduino.wait_for_command_id(command_id)

    # async def feeder_process(arduino, G1):
    #     t0 = time.time()
    #
    #     holder_lock = asyncio.Lock()
    #     holder_lock_rail = asyncio.Lock()
    #     cartridge_lock = asyncio.Lock()
    #     cartridge_lock_rail = asyncio.Lock()
    #
    #     for i in range(12):
    #         # rail must be stationary
    #         t1 = t2 = None
    #         if 10 >= i >= 1:
    #             t1 = asyncio.create_task(holder_handover(arduino, holder_lock))
    #         if 11 >= i >= 2:
    #             t2 = asyncio.create_task(
    #                 cartridge_handover(arduino, cartridge_lock))
    #         await asyncio.sleep(.05)
    #
    #         # rail can move
    #         if 9 >= i >= 0:
    #             asyncio.create_task(holder_feed(arduino, holder_lock))
    #         if 10 >= i >= 1:
    #             asyncio.create_task(cartridge_feed(arduino, cartridge_lock))
    #
    #         t1 is None or await t1
    #         t2 is None or await t2
    #         if 10 >= i >= 1:
    #             await move_rail(arduino, G1, i)
    #         else:
    #             await asyncio.sleep(.05)
    #
    #     print(time.time() - t0)
    #
    #     res = await G1({'arduino_index': None, 'z': 718, 'feed': 6000}, None)
    #     assert res['success']
    #     # input('handover?')
    #     res = await G1({'arduino_index': None, 'z': 16, 'feed': 6000}, None)
    #     assert res['success']
    #     print(time.time() - t0)
    #
    #
    # async def move_rail(arduino, G1, index):
    #     await asyncio.sleep(.05)
    #     z = index * 25 + 16
    #     print('going to Z:%d' % z)
    #     res = await G1({'arduino_index': None, 'z': z, 'feed': 6000}, None)
    #     assert res['success']
    #     # arduino._send_command("G1 Z%d F6000" % z)
    #     # await asyncio.sleep(0.6)
    #
    #
    # async def holder_feed(arduino, holder_lock):
    #     async with holder_lock:
    #         # H::6 - bring pusher back
    #         arduino._send_command("{out6: 0}")
    #         await asyncio.sleep(1.5)
    #
    #         # H::1 bring finger down (7) and open sub-gate(4)
    #         arduino._send_command("{out7: 1, out8: 1, out4: 0, out5: 0}")
    #         await asyncio.sleep(.2)
    #
    #         # H::2 - open main gate
    #         arduino._send_command("{out3: 1}")
    #         await asyncio.sleep(.2)
    #
    #         # H::3 - push forward
    #         arduino._send_command("{out6: 1}")
    #         await asyncio.sleep(.6)
    #
    #
    # async def holder_handover(arduino, holder_lock):
    #     async with holder_lock:
    #         # H::4 - close main gate again and close sub-gate
    #         arduino._send_command("{out3: 0, out4: 1, out5: 1}")
    #         await asyncio.sleep(.2)
    #
    #         # H::5 - bring up finger
    #         arduino._send_command("{out7: 0, out8: 0}")
    #         await asyncio.sleep(.2)
    #
    #
