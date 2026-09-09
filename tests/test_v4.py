import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from jk_bms_analysis_v4 import analyze
from jk_bms_protocol import read_hex_frames
class V4Tests(unittest.TestCase):
 def setUp(self): self.result=analyze(read_hex_frames(ROOT/"tests/fixtures/frame_0x02.hex"))
 def test_analyzes_all_frames_and_bytes(self): self.assertEqual((self.result["frame_count"],len(self.result["bytes"])),(42,300))
 def test_current_candidate_is_constant_raw_zero(self):
  item=self.result["representations"]["i32le"][154]; self.assertEqual((item["stats"]["min"],item["stats"]["max"],item["stats"]["changes"]),(0,0,0))
 def test_confirmed_pack_changes(self):
  item=self.result["representations"]["u32le"][150]; self.assertEqual((item["stats"]["min"],item["stats"]["max"]),(68706,68745)); self.assertGreater(item["stats"]["changes"],0)
if __name__ == "__main__": unittest.main()
