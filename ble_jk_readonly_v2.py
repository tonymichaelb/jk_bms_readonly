"""JK BMS V2 reader for macOS and BLE platforms supported by Bleak.

The only BLE writes in this module are the two observed information requests
0x97 and 0x96.  No configuration or control command is present.
"""
from __future__ import annotations

import argparse
import asyncio
from typing import Optional

from bleak import BleakClient, BleakScanner
from bleak.backends.device import BLEDevice

from jk_bms_protocol import AT_LINE, FrameAssembler, REQUEST_96, REQUEST_97, parse_jk_frame


FFE1 = "0000ffe1-0000-1000-8000-00805f9b34fb"


def render(data) -> str:
    if data.frame_type == 0x03:
        return "JK BMS\nModelo: {}\nID: {}\nVersão: {}".format(data.model, data.device_id, data.version)
    if data.frame_type != 0x02:
        return "Frame 0x{:02X} validado; sem campos confirmados na V2.".format(data.frame_type)
    rows = [
        "JK BMS", "Células: {}".format(len(data.cell_voltages_mv)),
        "Pack: {:.3f} V".format(data.total_voltage_v),
        "SOC: {} % (forte evidência)".format(data.soc_percent),
        "SOH: {} % (forte evidência)".format(data.soh_percent),
        "Capacidade: {:.3f} / {:.3f} Ah".format(data.remaining_capacity_ah, data.nominal_capacity_ah),
    ]
    rows += ["{:02d} {:.3f} V".format(index, voltage / 1000.0) for index, voltage in enumerate(data.cell_voltages_mv, 1)]
    rows += [
        "Soma das células: {:.3f} V".format(data.cell_sum_v),
        "Delta calculado: {:.3f} V".format(data.cell_delta_v),
        "Temperatura 1: {:.1f} °C".format(data.temperatures_c[0]),
        "Temperatura 2: {:.1f} °C".format(data.temperatures_c[1]),
        "Corrente/alarmes/estados: INCERTOS nos frames disponíveis.",
    ]
    return "\n".join(rows)


async def find_bms(address: Optional[str], name: Optional[str]) -> BLEDevice:
    """Resolve a macOS CoreBluetooth UUID to a discovered BLEDevice object."""
    print("Procurando dispositivos BLE por 20 segundos...")
    devices = await BleakScanner.discover(timeout=20.0)
    if not devices:
        raise RuntimeError("Nenhum dispositivo BLE encontrado na varredura.")

    for item in devices:
        print("  Nome: {!r} | Endereço: {}".format(item.name, item.address))

    normalized_name = name.strip() if name else None
    normalized_address = address.casefold() if address else None
    name_match = None
    address_match = None
    for item in devices:
        item_name = item.name.strip() if item.name else None
        # A exact name match is preferred over a potentially stale macOS UUID.
        if normalized_name and item_name == normalized_name and name_match is None:
            name_match = item
        if normalized_address and item.address.casefold() == normalized_address and address_match is None:
            address_match = item

    if name_match is not None:
        if address_match is not None and address_match.address != name_match.address:
            print("Aviso: nome e UUID apontam para dispositivos diferentes; usando a correspondência exata do nome.")
        elif normalized_address and name_match.address.casefold() != normalized_address:
            print("Aviso: nome encontrado, mas o UUID informado não apareceu nesta varredura; usando o dispositivo pelo nome.")
        return name_match

    if address_match is not None:
        if address_match.name is None:
            print("UUID CoreBluetooth encontrado, mas o dispositivo não anunciou nome.")
        elif normalized_name:
            print("UUID encontrado, mas o nome anunciado é diferente: {!r}.".format(address_match.name))
        return address_match

    raise RuntimeError("BMS não encontrada. Nenhum dispositivo correspondeu ao nome ou UUID CoreBluetooth informado.")


async def main(address: Optional[str], name: Optional[str]) -> None:
    device = await find_bms(address, name)
    print("Encontrado: {} / {}".format(device.name or "(sem nome)", device.address))
    print("Conectando...")

    assembler = FrameAssembler()
    try:
        async with BleakClient(device) as client:
            print("Conectado: {}".format(client.is_connected))

            def receive(_: int, payload: bytearray) -> None:
                raw = bytes(payload)
                if raw == AT_LINE:
                    return
                for frame in assembler.feed(raw):
                    print("\n" + render(parse_jk_frame(frame)))

            await client.start_notify(FFE1, receive)
            # Exact requests captured from the official application's read flow.
            await client.write_gatt_char(FFE1, REQUEST_97, response=False)
            await asyncio.sleep(1)
            await client.write_gatt_char(FFE1, REQUEST_96, response=False)
            try:
                await asyncio.Future()
            finally:
                await client.stop_notify(FFE1)
    except Exception as error:
        print("Conexão perdida ou não iniciada: {}".format(error))
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--address", help="UUID CoreBluetooth/macOS, resolvido pelo scanner")
    parser.add_argument("--name", default="512261K33000148", help="nome BLE usado como fallback")
    arguments = parser.parse_args()
    asyncio.run(main(arguments.address, arguments.name))
