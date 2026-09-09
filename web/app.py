"""FastAPI application for the read-only JK BMS monitor."""
from __future__ import annotations
import argparse, asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from jk_bms_protocol import read_hex_frames
from web.bms_service import BmsService
from web.live_reader import run_live
from web.ble_manager import BleManager
from web.config_service import ConfigService

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent

async def run_demo(service):
    frames = read_hex_frames(PROJECT / "tests/fixtures/frame_0x02.hex")
    identity = read_hex_frames(PROJECT / "tests/fixtures/frame_0x03.hex")[0]
    await service.apply_frame(identity); service.connected = True; await service.publish()
    index = 0
    while True:
        await service.apply_frame(frames[index % len(frames)]); index += 1
        await asyncio.sleep(2)

def create_app(demo: bool = False, enable_ble: bool = True) -> FastAPI:
    service = BmsService(demo=demo)
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        task = asyncio.create_task(run_demo(service)) if demo and enable_ble else None
        yield
        if task is not None:
            task.cancel()
            try: await task
            except asyncio.CancelledError: pass
        if hasattr(app.state, "ble_manager"): await app.state.ble_manager.disconnect()
    app = FastAPI(title="JK BMS Monitor", lifespan=lifespan)
    app.state.service = service
    app.state.ble_manager = BleManager(service)
    app.state.config_service = ConfigService()
    app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
    @app.get("/")
    async def index(): return FileResponse(ROOT / "templates/index.html")
    @app.get("/api/status")
    async def status(): return service.snapshot()
    @app.get("/api/cells")
    async def cells():
        s=service.snapshot(); return {key:s[key] for key in ("cells_count","cell_voltages","cell_min","cell_max","cell_delta","cell_sum")}
    @app.get("/api/temperatures")
    async def temperatures():
        s=service.snapshot(); return {"temperature_1":s["temperature_1"],"temperature_2":s["temperature_2"]}
    @app.get("/api/connection")
    async def connection():
        s=service.snapshot(); return {key:s[key] for key in ("connected","demo","ble_name","updated_at")}
    @app.get("/api/history")
    async def history(): return list(service.history)
    @app.get("/api/ble/scan")
    async def ble_scan(): return {"devices": [] if demo else await app.state.ble_manager.scan(), "error":app.state.ble_manager.error}
    @app.post("/api/ble/connect")
    async def ble_connect(payload: dict):
        if demo: return {"ok":False,"error":"BLE indisponível no modo demonstração"}
        address=payload.get("address")
        if not address: return {"ok":False,"error":"address é obrigatório"}
        await app.state.ble_manager.connect(address,payload.get("name")); return {"ok":True}
    @app.post("/api/ble/disconnect")
    async def ble_disconnect(): await app.state.ble_manager.disconnect(); return {"ok":True}
    @app.get("/api/ble/status")
    async def ble_status(): return app.state.ble_manager.status()
    @app.get("/api/config/status")
    async def config_status(): return app.state.config_service.status()
    @app.get("/api/config/settings")
    async def config_settings(): return app.state.config_service.settings()
    @app.post("/api/config/read")
    async def config_read(): return app.state.config_service.blocked()
    @app.post("/api/config/validate")
    async def config_validate(): return app.state.config_service.blocked()
    @app.post("/api/config/write")
    async def config_write(): return app.state.config_service.blocked()
    @app.websocket("/ws")
    async def websocket(socket: WebSocket):
        await socket.accept(); queue=service.subscribe()
        try:
            await socket.send_json(service.snapshot())
            while True: await socket.send_json(await queue.get())
        except WebSocketDisconnect: pass
        finally: service.unsubscribe(queue)
    return app

app = create_app()
if __name__ == "__main__":
    parser=argparse.ArgumentParser(); parser.add_argument("--demo",action="store_true"); parser.add_argument("--host",default="0.0.0.0"); parser.add_argument("--port",type=int,default=8000)
    args=parser.parse_args(); import uvicorn
    uvicorn.run(create_app(demo=args.demo), host=args.host, port=args.port)
