"""V3 display using exactly the V2 macOS discovery and JK read requests."""
from __future__ import annotations
import argparse
import asyncio
from bleak import BleakClient
from ble_jk_readonly_v2 import FFE1, find_bms, render
from jk_bms_protocol import AT_LINE, FrameAssembler, REQUEST_96, REQUEST_97
from jk_bms_protocol_v3 import parse_jk_frame_v3

def render_v3(parsed) -> str:
    output = render(parsed.base)
    if parsed.base.frame_type == 0x02:
        current = parsed.evidence["current_candidate"]
        output += "\n\nV3 análise (não confirmada):\nCorrente candidata bytes {}: {} ({})".format(current.raw, current.value, current.confidence)
        output += "\nEstados, alarmes e balanceamento: INCERTOS; nenhum bit é interpretado."
    return output

async def main(address, name):
    device = await find_bms(address, name)
    print("Encontrado: {} / {}".format(device.name or "(sem nome)", device.address))
    assembler = FrameAssembler()
    try:
        async with BleakClient(device) as client:
            def receive(_, payload):
                raw = bytes(payload)
                if raw == AT_LINE: return
                for frame in assembler.feed(raw): print("\n" + render_v3(parse_jk_frame_v3(frame)))
            await client.start_notify(FFE1, receive)
            await client.write_gatt_char(FFE1, REQUEST_97, response=False)
            await asyncio.sleep(1)
            await client.write_gatt_char(FFE1, REQUEST_96, response=False)
            try: await asyncio.Future()
            finally: await client.stop_notify(FFE1)
    except Exception as error:
        print("Conexão perdida ou não iniciada: {}".format(error)); raise

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--address"); parser.add_argument("--name", default="512261K33000148")
    args = parser.parse_args(); asyncio.run(main(args.address, args.name))
