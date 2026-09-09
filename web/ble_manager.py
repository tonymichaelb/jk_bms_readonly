"""Manual BLE discovery/connection coordinator; never accepts arbitrary bytes."""
import asyncio
from bleak import BleakScanner
from web.live_reader import run_live

FFE0 = "0000ffe0-0000-1000-8000-00805f9b34fb"

class BleManager:
    def __init__(self, service): self.service=service; self.task=None; self.selected=None; self.error=None
    async def scan(self):
        self.error=None
        try: devices=await BleakScanner.discover(timeout=8.0, return_adv=True)
        except Exception as error: self.error=str(error); return []
        result=[]
        rows=devices.items() if isinstance(devices,dict) else ((item.address,(item,None)) for item in devices)
        for address,(device,advertisement) in rows:
            name=device.name or getattr(advertisement,"local_name",None)
            uuids=[str(x).lower() for x in getattr(advertisement,"service_uuids",[]) or []]
            candidate=FFE0 in uuids or "jk" in (name or "").lower() or (name or "")=="512261K33000148"
            result.append({"name":name,"address":address,"rssi":getattr(advertisement,"rssi",None),"is_jk_bms":candidate,"services":uuids})
        return sorted(result,key=lambda x:(not x["is_jk_bms"],x["name"] or ""))
    async def connect(self,address,name=None):
        await self.disconnect()
        self.selected={"address":address,"name":name}; self.error=None
        self.task=asyncio.create_task(run_live(self.service,address=address,name=name or "512261K33000148"))
    async def disconnect(self):
        if self.task:
            self.task.cancel()
            try: await self.task
            except asyncio.CancelledError: pass
        self.task=None; self.service.connected=False; await self.service.publish()
    def status(self): return {"selected":self.selected,"connected":self.service.connected,"error":self.error}
