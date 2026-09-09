"""Thread-safe-in-the-event-loop state store and in-memory history."""
from __future__ import annotations
import asyncio
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, Optional, Set

from jk_bms_protocol_v3 import parse_jk_frame_v3


class BmsService:
    def __init__(self, demo: bool = False) -> None:
        self.demo = demo
        self.connected = False
        self.name = "512261K33000148"
        self.model: Optional[str] = None
        self.device_id: Optional[str] = None
        self.firmware: Optional[str] = None
        self.data = None
        self.history: Deque[Dict[str, Any]] = deque(maxlen=360)
        self.listeners: Set[asyncio.Queue] = set()

    def snapshot(self) -> Dict[str, Any]:
        base = self.data
        cells = [value / 1000.0 for value in base.cell_voltages_mv] if base else []
        return {
            "connected": self.connected,
            "demo": self.demo,
            "ble_name": self.name,
            "model": self.model,
            "device_id": self.device_id,
            "firmware": self.firmware,
            "cells_count": len(cells),
            "pack_voltage": base.total_voltage_v if base else None,
            "soc": base.soc_percent if base else None,
            "soh": base.soh_percent if base else None,
            "capacity_current": base.remaining_capacity_ah if base else None,
            "capacity_configured": base.nominal_capacity_ah if base else None,
            "cell_voltages": cells,
            "cell_min": min(cells) if cells else None,
            "cell_max": max(cells) if cells else None,
            "cell_delta": (max(cells) - min(cells)) if cells else None,
            "cell_sum": base.cell_sum_v if base else None,
            "temperature_1": base.temperatures_c[0] if base and base.temperatures_c else None,
            "temperature_2": base.temperatures_c[1] if base and len(base.temperatures_c) > 1 else None,
            "current": None, "alarms": None, "balance": None,
            "updated_at": self.history[-1]["timestamp"] if self.history else None,
        }

    async def publish(self) -> None:
        event = self.snapshot()
        for queue in list(self.listeners):
            if queue.full():
                try: queue.get_nowait()
                except asyncio.QueueEmpty: pass
            queue.put_nowait(event)

    async def apply_frame(self, frame: bytes) -> None:
        parsed = parse_jk_frame_v3(frame).base
        if parsed.frame_type == 0x03:
            self.model, self.device_id, self.firmware = parsed.model, parsed.device_id, parsed.version
        elif parsed.frame_type == 0x02:
            self.data = parsed
            self.history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "pack_voltage": parsed.total_voltage_v,
                "temperatures": parsed.temperatures_c,
                "cells": [value / 1000.0 for value in parsed.cell_voltages_mv],
            })
        await self.publish()

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=1)
        self.listeners.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None: self.listeners.discard(queue)
