"""Evidence-based reader for the captured 300-byte JK BMS frames."""
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

HEADER_RX = bytes.fromhex("55 AA EB 90")
HEADER_TX = bytes.fromhex("AA 55 90 EB")
FRAME_LENGTH = 300
AT_LINE = b"AT\r\n"
FFE1_REQUEST_COMMANDS = frozenset((0x96, 0x97))

def checksum8(data: bytes) -> int: return sum(data) & 0xFF
def checksum_ok(frame: bytes) -> bool: return len(frame) == FRAME_LENGTH and checksum8(frame[:-1]) == frame[-1]
def hex_bytes(data: bytes) -> str: return " ".join("{:02X}".format(b) for b in data)
def make_request(command: int) -> bytes:
    if command not in FFE1_REQUEST_COMMANDS: raise ValueError("only observed read commands 0x96 and 0x97 are permitted")
    body = HEADER_TX + bytes([command]) + bytes(14)
    return body + bytes([checksum8(body)])
REQUEST_96, REQUEST_97 = make_request(0x96), make_request(0x97)

def read_hex_frames(path: Path) -> List[bytes]:
    frames = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.strip():
            try: frames.append(bytes.fromhex(line))
            except ValueError as error: raise ValueError("invalid hex in {} line {}".format(path, number)) from error
    return frames

@dataclass
class FrameAssembler:
    buffer: bytearray = field(default_factory=bytearray)
    def feed(self, chunk: bytes) -> List[bytes]:
        if not chunk or chunk == AT_LINE: return []
        self.buffer.extend(chunk); result = []
        while True:
            start = self.buffer.find(HEADER_RX)
            if start < 0:
                self.buffer[:] = self.buffer[-3:]
                return result
            if start: del self.buffer[:start]
            if len(self.buffer) < FRAME_LENGTH: return result
            frame = bytes(self.buffer[:FRAME_LENGTH]); del self.buffer[:FRAME_LENGTH]
            if checksum_ok(frame): result.append(frame)

def _u16(f: bytes, o: int) -> int: return int.from_bytes(f[o:o + 2], "little")
def _u32(f: bytes, o: int) -> int: return int.from_bytes(f[o:o + 4], "little")
def _slot(f: bytes, o: int, n: int) -> str: return f[o:o+n].split(b"\0", 1)[0].decode("ascii", "replace").strip()

@dataclass
class BmsData:
    frame_type: int; raw: bytes
    cell_voltages_mv: List[int] = field(default_factory=list)
    total_voltage_v: Optional[float] = None
    temperatures_c: List[float] = field(default_factory=list)
    soc_percent: Optional[int] = None; soh_percent: Optional[int] = None
    remaining_capacity_ah: Optional[float] = None; nominal_capacity_ah: Optional[float] = None
    model: Optional[str] = None; device_id: Optional[str] = None; version: Optional[str] = None
    raw_candidates: Dict[str, object] = field(default_factory=dict)
    @property
    def cell_sum_v(self) -> Optional[float]: return sum(self.cell_voltages_mv) / 1000.0 if self.cell_voltages_mv else None
    @property
    def cell_delta_v(self) -> Optional[float]: return (max(self.cell_voltages_mv)-min(self.cell_voltages_mv))/1000.0 if self.cell_voltages_mv else None
    def approximate_power_w(self) -> Optional[float]: return None

def _active_cells(frame: bytes) -> List[int]:
    cells = []
    for offset in range(6, 70, 2):
        value = _u16(frame, offset)
        if value == 0: break
        cells.append(value)
    return cells

def parse_jk_frame(frame: bytes) -> BmsData:
    if len(frame) != FRAME_LENGTH: raise ValueError("JK frame must contain exactly 300 bytes")
    if not frame.startswith(HEADER_RX): raise ValueError("not a JK frame")
    if not checksum_ok(frame): raise ValueError("invalid JK frame checksum")
    data = BmsData(frame[4], frame)
    if data.frame_type == 0x02:
        data.cell_voltages_mv = _active_cells(frame)
        data.total_voltage_v = _u32(frame, 150) / 1000.0
        data.temperatures_c = [_u16(frame, 162) / 10.0, _u16(frame, 164) / 10.0]
        data.soc_percent, data.remaining_capacity_ah = frame[173], _u32(frame, 174) / 1000.0
        data.nominal_capacity_ah, data.soh_percent = _u32(frame, 178) / 1000.0, _u16(frame, 190)
        data.raw_candidates = {"mean_cell_mv_offset_74": _u16(frame, 74), "spread_like_value_offset_76": _u16(frame, 76), "unconfirmed_signed_16_offset_170": int.from_bytes(frame[170:172], "little", signed=True)}
    elif data.frame_type == 0x03:
        data.model, data.version, data.device_id = _slot(frame, 6, 24), _slot(frame, 30, 16), _slot(frame, 46, 16)
    return data
