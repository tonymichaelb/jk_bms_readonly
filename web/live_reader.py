"""Existing validated read flow adapted only to feed the web state service."""
from __future__ import annotations
import asyncio
from bleak import BleakClient
from ble_jk_readonly_v2 import FFE1, find_bms
from jk_bms_protocol import AT_LINE, FrameAssembler, REQUEST_96, REQUEST_97

async def run_live(service, address=None, name="512261K33000148"):
    """Reconnect safely; transmit only the two already-validated read requests."""
    while True:
        try:
            device = await find_bms(address, name)
            service.name = device.name or name
            async with BleakClient(device) as client:
                service.connected = True; await service.publish()
                assembler = FrameAssembler()
                def receive(_, payload):
                    raw = bytes(payload)
                    if raw != AT_LINE:
                        for frame in assembler.feed(raw): asyncio.create_task(service.apply_frame(frame))
                await client.start_notify(FFE1, receive)
                await client.write_gatt_char(FFE1, REQUEST_97, response=False)
                await asyncio.sleep(1)
                await client.write_gatt_char(FFE1, REQUEST_96, response=False)
                await asyncio.Future()
        except asyncio.CancelledError: raise
        except Exception as error: print("BLE desconectado: {}".format(error))
        finally:
            service.connected = False; await service.publish()
        await asyncio.sleep(5)
