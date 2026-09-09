import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from fastapi.testclient import TestClient
from web.app import create_app

def test_demo_api_has_confirmed_fields():
    with TestClient(create_app(demo=True)) as client:
        status=client.get('/api/status'); assert status.status_code==200
        data=status.json(); assert data['demo'] is True and data['connected'] is True
        assert data['cells_count']==17 and len(data['cell_voltages'])==17
        assert data['cell_min'] <= data['cell_max']
        assert data['cell_delta'] == data['cell_max']-data['cell_min']
        assert data['current'] is None and data['alarms'] is None and data['balance'] is None

def test_api_routes_and_disconnected_state():
    app=create_app(demo=False, enable_ble=False); service=app.state.service
    assert service.snapshot()['connected'] is False
    with TestClient(app) as client:
        for route in ('/','/api/status','/api/cells','/api/temperatures','/api/connection','/api/history'):
            assert client.get(route).status_code==200
