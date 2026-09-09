import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from jk_bms_protocol import read_hex_frames
from jk_bms_protocol_v3 import parse_jk_frame_v3
FIXTURES=Path(__file__).parent/"fixtures"
class V3EvidenceTests(unittest.TestCase):
 def test_current_and_balance_candidates_are_not_promoted(self):
  parsed=parse_jk_frame_v3(read_hex_frames(FIXTURES/"frame_0x02.hex")[0])
  self.assertEqual(parsed.evidence["current_candidate"].raw,"00 00 00 00")
  self.assertEqual(parsed.evidence["current_candidate"].confidence,"FORTE EVIDÊNCIA")
  self.assertEqual(parsed.evidence["balance_current_candidate"].confidence,"INCERTO")
 def test_pack_agrees_with_cell_sum_across_real_frames(self):
  for frame in read_hex_frames(FIXTURES/"frame_0x02.hex"):
   data=parse_jk_frame_v3(frame).base
   self.assertLessEqual(abs(data.cell_sum_v-data.total_voltage_v),0.0251)
if __name__ == "__main__": unittest.main()
