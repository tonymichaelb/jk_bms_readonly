import asyncio
from bleak import BleakScanner

async def main():
    print("Procurando dispositivos BLE por 20 segundos...")
    devices = await BleakScanner.discover(timeout=20)

    print("\nDispositivos encontrados:")
    for d in devices:
        print(f"Nome: {d.name!r} | Endereço: {d.address}")

asyncio.run(main())

