import argparse
import asyncio
from datetime import datetime

from bleak import BleakClient, BleakScanner

from jk_bms_protocol import (
    REQUEST_96,
    REQUEST_97,
    HEADER_RX,
    hex_bytes,
    checksum_ok,
    FrameAssembler,
)


FFE0 = "0000ffe0-0000-1000-8000-00805f9b34fb"
FFE1 = "0000ffe1-0000-1000-8000-00805f9b34fb"


async def find_device(name: str):
    print(f"Procurando por: {name}")

    devices = await BleakScanner.discover(timeout=8.0)

    for d in devices:
        print(f"  {d.name!r}  {d.address}")

        if d.name == name:
            return d

    return None


async def main(name: str, seconds: int):
    device = await find_device(name)

    if device is None:
        print("\nBMS não encontrado.")
        return

    print(f"\nEncontrado: {device.name} / {device.address}")
    print("Conectando...")

    assembler = FrameAssembler()

    def notification_handler(sender, data: bytearray):
        raw = bytes(data)

        now = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        print(
            f"\n[{now}] RX {sender}"
            f"\nHEX:   {hex_bytes(raw)}"
            f"\nASCII: {raw!r}"
        )

        frames = assembler.feed(raw)

        for frame in frames:
            print("\n==============================")
            print("FRAME JK COMPLETO")
            print(f"Tamanho: {len(frame)} bytes")
            print(f"HEX: {hex_bytes(frame)}")
            print(f"Checksum: {checksum_ok(frame)}")
            print(f"Frame type: 0x{frame[4]:02X}")
            print("==============================")

    async with BleakClient(device) as client:
        print("Conectado:", client.is_connected)

        print("\nServiços encontrados:")
        for service in client.services:
            print(service.uuid)
            for char in service.characteristics:
                print(
                    f"  {char.uuid} "
                    f"properties={','.join(char.properties)}"
                )

        # Procurar FFE1
        ffe1 = None

        for service in client.services:
            if service.uuid.lower() == FFE0:
                for char in service.characteristics:
                    if char.uuid.lower() == FFE1:
                        ffe1 = char

        if ffe1 is None:
            print("\nFFE1 não encontrado.")
            return

        print("\nAtivando NOTIFY em FFE1...")
        await client.start_notify(ffe1, notification_handler)

        print("NOTIFY FFE1 ativado.")

        # Solicitação 0x97
        print("\nTX 0x97:")
        print(hex_bytes(REQUEST_97))
        await client.write_gatt_char(
            ffe1,
            REQUEST_97,
            response=False,
        )

        await asyncio.sleep(2)

        # Solicitação 0x96
        print("\nTX 0x96:")
        print(hex_bytes(REQUEST_96))
        await client.write_gatt_char(
            ffe1,
            REQUEST_96,
            response=False,
        )

        print(f"\nCapturando por {seconds} segundos...")

        await asyncio.sleep(seconds)

        await client.stop_notify(ffe1)

        print("\nFim do teste.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--name",
        required=True,
    )

    parser.add_argument(
        "--seconds",
        type=int,
        default=20,
    )

    args = parser.parse_args()

    asyncio.run(
        main(
            args.name,
            args.seconds,
        )
    )
