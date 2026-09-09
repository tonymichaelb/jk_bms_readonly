"""Safe configuration facade: blocked until official protocol evidence exists."""
BLOCK_REASON="Leitura e escrita de configurações estão bloqueadas: protocolo oficial não disponível para validação."
FIELDS=["Cell UVP","Cell UVPR","Cell OVP","Cell OVPR","Balance Trigger","SOC 100%","SOC 0%","Power Off","Maximum Charge Current","Maximum Discharge Current","Maximum Balance Current","Balance Start Voltage","Capacity Ah","Cell Count","Charge MOS temperature","Discharge MOS temperature","Balance temperature","Charge enabled","Discharge enabled","Balance enabled"]
class ConfigService:
 def status(self): return {"available":False,"read_available":False,"write_available":False,"authentication_available":False,"reason":BLOCK_REASON}
 def settings(self): return {"settings":[{"name":x,"value":None,"status":"Indisponível"} for x in FIELDS],"reason":BLOCK_REASON}
 def blocked(self): return {"ok":False,"reason":BLOCK_REASON}
