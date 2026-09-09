import sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from jk_bms_protocol import FRAME_LENGTH, FrameAssembler, checksum_ok, parse_jk_frame, read_hex_frames
FIXTURES=Path(__file__).parent/"fixtures"
class RealFrames(unittest.TestCase):
 def test_all_complete_and_valid(self):
  for filename,count,kind in (("frame_0x01.hex",1,1),("frame_0x02.hex",42,2),("frame_0x03.hex",2,3)):
   frames=read_hex_frames(FIXTURES/filename); self.assertEqual(len(frames),count); self.assertTrue(all(len(x)==FRAME_LENGTH and x[4]==kind and checksum_ok(x) for x in frames))
 def test_first_data_frame(self):
  d=parse_jk_frame(read_hex_frames(FIXTURES/"frame_0x02.hex")[0]); self.assertEqual(d.cell_voltages_mv,[4051,4038,4040,4038,4042,4043,4043,4045,4045,4046,4046,4046,4046,4046,4042,4042,4038]); self.assertEqual(len(d.cell_voltages_mv),17); self.assertEqual(d.total_voltage_v,68.736); self.assertEqual(d.cell_sum_v,68.737); self.assertEqual(d.temperatures_c,[37.7,34.2]); self.assertEqual(d.remaining_capacity_ah,39.954); self.assertEqual(d.nominal_capacity_ah,40.0)
 def test_fragments_and_at(self):
  frame=read_hex_frames(FIXTURES/"frame_0x02.hex")[0]; a=FrameAssembler(); self.assertEqual(a.feed(b"AT\r\n"),[]); self.assertEqual(a.feed(frame[:73]),[]); self.assertEqual(a.feed(frame[73:]),[frame])
 def test_identity(self):
  d=parse_jk_frame(read_hex_frames(FIXTURES/"frame_0x03.hex")[0]); self.assertEqual((d.model,d.device_id,d.version),("JK-BD4A20S4P","512261K33000148","19.27"))
if __name__ == "__main__": unittest.main()
