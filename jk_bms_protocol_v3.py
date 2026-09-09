"""V3 analytical layer over V2; no BLE transport or commands live here."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from jk_bms_protocol import BmsData, parse_jk_frame


@dataclass(frozen=True)
class Evidence:
    offset_start: int
    offset_end: int
    endian: str
    raw: str
    factor: str
    unit: str
    value: object
    confidence: str


@dataclass
class V3Data:
    base: BmsData
    evidence: Dict[str, Evidence] = field(default_factory=dict)
    unknown_dynamic_offsets: List[int] = field(default_factory=list)


def parse_jk_frame_v3(frame: bytes) -> V3Data:
    """Decode only evidence-backed V2 fields and expose V3 candidates safely."""
    base = parse_jk_frame(frame)
    result = V3Data(base=base)
    if base.frame_type != 0x02:
        return result

    # The sample's known near-zero current coincides with this signed 32-bit
    # candidate, immediately after confirmed pack voltage. It never changes in
    # the 42 frames, so the factor is deliberately not asserted as confirmed.
    raw_current = int.from_bytes(frame[154:158], "little", signed=True)
    raw_balance_current = int.from_bytes(frame[158:162], "little", signed=True)
    result.evidence = {
        "current_candidate": Evidence(154, 157, "LE signed i32", frame[154:158].hex(" ").upper(), "unconfirmed", "A", raw_current, "FORTE EVIDÊNCIA"),
        "balance_current_candidate": Evidence(158, 161, "LE signed i32", frame[158:162].hex(" ").upper(), "unconfirmed", "A", raw_balance_current, "INCERTO"),
        "state_flag_block": Evidence(196, 199, "raw bytes", frame[196:200].hex(" ").upper(), "none", "flags", list(frame[196:200]), "INCERTO"),
        "alarm_candidate_block": Evidence(200, 215, "raw bytes", frame[200:216].hex(" ").upper(), "none", "unknown", list(frame[200:216]), "INCERTO"),
    }
    # These varied in the real 0x02 fixture set, but no independent BMS-state
    # observation identifies their meaning. Keep their offsets visible only.
    result.unknown_dynamic_offsets = [170, 171, 194, 195, 230, 234, 246, 247, 262, 263]
    return result
