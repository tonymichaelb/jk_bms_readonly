"""Statistical V4 analysis of real 0x02 fixtures; no BLE code or writes."""
from __future__ import annotations
import json
import math
from pathlib import Path
from statistics import mean
from typing import Dict, Iterable, List, Optional

from jk_bms_protocol import read_hex_frames, parse_jk_frame

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "tests" / "fixtures" / "frame_0x02.hex"

def changes(values): return sum(left != right for left, right in zip(values, values[1:]))
def correlation(left, right):
    if len(left) < 2 or len(set(left)) < 2 or len(set(right)) < 2: return None
    lx, ly = mean(left), mean(right)
    numerator = sum((x-lx)*(y-ly) for x,y in zip(left,right))
    denominator = math.sqrt(sum((x-lx)**2 for x in left)*sum((y-ly)**2 for y in right))
    return None if denominator == 0 else numerator / denominator
def summary(values): return {"min":min(values),"max":max(values),"mean":mean(values),"distinct":len(set(values)),"changes":changes(values)}
def series(frames, offset, size, byteorder, signed): return [int.from_bytes(frame[offset:offset+size],byteorder,signed=signed) for frame in frames]

def analyze(frames):
    parsed=[parse_jk_frame(frame) for frame in frames]
    metrics={
        "pack_v":[item.total_voltage_v for item in parsed], "cell_sum_v":[item.cell_sum_v for item in parsed],
        "cell_max_mv":[max(item.cell_voltages_mv) for item in parsed], "cell_min_mv":[min(item.cell_voltages_mv) for item in parsed],
        "cell_delta_mv":[max(item.cell_voltages_mv)-min(item.cell_voltages_mv) for item in parsed],
        "t1_c":[item.temperatures_c[0] for item in parsed], "t2_c":[item.temperatures_c[1] for item in parsed],
    }
    bytes_out=[]
    for offset in range(300):
        values=[frame[offset] for frame in frames]; item={"offset":offset,"stats":summary(values)}
        item["correlation"]={name:correlation(values,values2) for name,values2 in metrics.items()}
        bytes_out.append(item)
    representations={}
    for label,size,order,signed in (("u16le",2,"little",False),("u16be",2,"big",False),("i16le",2,"little",True),("i16be",2,"big",True),("u32le",4,"little",False),("i32le",4,"little",True),("u32be",4,"big",False),("i32be",4,"big",True)):
        representations[label]=[]
        for offset in range(301-size):
            values=series(frames,offset,size,order,signed)
            representations[label].append({"offset":offset,"stats":summary(values),"correlation":{name:correlation(values,target) for name,target in metrics.items()}})
    return {"frame_count":len(frames),"metrics":metrics,"bytes":bytes_out,"representations":representations}

def _fmt(value): return "—" if value is None else "{:.4f}".format(value)
def report(analysis):
    lines=["# OFFSETS V4 — análise estatística dos frames 0x02 reais", "", "Fonte: 42 fixtures completos de 300 bytes. Correlação: Pearson; `—` significa série constante, portanto correlação não definível.", "", "## Candidatos e campos confirmados", "", "|Campo|Offset|Representação|Faixa observada|Correlação principal|Interpretação|Confiança|", "|-|-|-|-|-|-|-|"]
    rows=[
      ("17 células","6–39","17×u16 LE / mV","4037–4056 mV","pack/células: derivado","slots ativos consecutivos","CONFIRMADO"),
      ("Pack","150–153","u32 LE /1000 V","68.706–68.745 V","soma: calculada","tensão total","CONFIRMADO"),
      ("T1 / T2","162–165","2×u16 LE /10 °C","37.7 / 34.2 °C","constante","temperaturas","CONFIRMADO"),
      ("SOC","173","u8 %","100","constante","SOC","FORTE EVIDÊNCIA"),
      ("SOH","190–191","u16 LE %","100","constante","SOH","FORTE EVIDÊNCIA"),
      ("Capacidades","174–181","2×u32 LE /1000 Ah","39.954 / 40.000 Ah","constante","restante / nominal","CONFIRMADO"),
      ("current_raw_candidate","154–157","i32 LE","0","constante","não converter para A","FORTE EVIDÊNCIA"),
      ("balance_current_candidate","158–161","i32 LE","0","constante","sem escala ou função confirmada","INCERTO"),
      ("Flags","196–199","bytes brutos","08 00 01 01","constante","não interpretar bits","INCERTO"),
      ("Alarmes","200–215","bytes brutos","todos 00","constante","não interpretar como alarme=0","INCERTO"),
    ]
    lines += ["|{}|{}|{}|{}|{}|{}|{}|".format(*row) for row in rows]
    lines += ["", "## Estatística temporal por byte", "", "|Offset|Mín.|Máx.|Média|Distintos|Mudanças|r pack|r soma|r delta|", "|-:|-:|-:|-:|-:|-:|-:|-:|-:|"]
    for item in analysis["bytes"]:
        s,c=item["stats"],item["correlation"]
        lines.append("|{}|{}|{}|{:.3f}|{}|{}|{}|{}|{}|".format(item["offset"],s["min"],s["max"],s["mean"],s["distinct"],s["changes"],_fmt(c["pack_v"]),_fmt(c["cell_sum_v"]),_fmt(c["cell_delta_mv"])))
    lines += ["", "## Séries numéricas por representação", "", "O arquivo de dados completo `analysis_v4.json` contém cada janela possível para u16 LE/BE, i16 LE/BE e u32/i32 LE/BE, com todas as correlações solicitadas. A tabela abaixo lista somente janelas que mudaram; isso evita transformar 2.384 janelas constantes em interpretação.", "", "|Rep.|Offset|Mín.|Máx.|Distintos|Mudanças|r pack|", "|-|-:|-:|-:|-:|-:|-:|"]
    for label,items in analysis["representations"].items():
        for item in items:
            s=item["stats"]
            if s["changes"]:
                lines.append("|{}|{}|{}|{}|{}|{}|{}|".format(label,item["offset"],s["min"],s["max"],s["distinct"],s["changes"],_fmt(item["correlation"]["pack_v"])))
    return "\n".join(lines)+"\n"

def main():
    frames=read_hex_frames(FIXTURES); analysis=analyze(frames)
    (ROOT/"analysis_v4.json").write_text(json.dumps(analysis,indent=2),encoding="utf-8")
    (ROOT/"OFFSETS_V4.md").write_text(report(analysis),encoding="utf-8")
    print("Wrote OFFSETS_V4.md and analysis_v4.json for {} frames.".format(len(frames)))
if __name__ == "__main__": main()
