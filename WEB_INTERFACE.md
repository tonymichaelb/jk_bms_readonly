# Interface Web V1 — somente leitura

## Arquitetura

`BLE → leitor validado (FFE1, 0x97/0x96) → parser V3 → BmsService → FastAPI/WebSocket → navegador`.

Nenhum endpoint web envia comandos à BMS. O leitor vivo reutiliza somente `REQUEST_97` e `REQUEST_96`, já validados, uma vez por conexão. Em quedas, ele informa desconexão e tenta reconectar após cinco segundos.

## Instalação e execução

```bash
cd "/Users/tonymichaelbatistadelima/Desktop/apk bms/raspberry batera/jk_bms_readonly"
../.venv/bin/pip install -r requirements-web.txt
../.venv/bin/python -m web.app --demo
```

Abra [http://localhost:8000](http://localhost:8000). O modo `--demo` usa frames reais capturados e mostra **MODO DEMONSTRAÇÃO**.

Para o BMS real, sem `--demo`:

```bash
../.venv/bin/python -m web.app
```

No Raspberry Pi, instale as mesmas dependências e abra `http://IP_DO_RASPBERRY:8000`. A interface é responsiva e usa HTML/CSS/JavaScript puro.

## API

- `GET /api/status`
- `GET /api/cells`
- `GET /api/temperatures`
- `GET /api/connection`
- `GET /api/history`
- `GET /ws` (WebSocket)

## Bluetooth manual (modo REAL)

Abra a seção **Bluetooth**, escolha **Procurar dispositivos BLE** e clique em
**Conectar** somente no dispositivo desejado. O scanner mostra nome, endereço,
RSSI quando disponível e uma indicação de possível JK BMS pelo serviço FFE0 ou
nome. Não há conexão automática com todos os dispositivos.

No Raspberry Pi, confirme o adaptador antes da execução:

```bash
bluetoothctl show
bluetoothctl scan on
```

O leitor usa FFE0/FFE1 e somente os requests de leitura 0x97 e 0x96. Nenhum
endpoint aceita bytes arbitrários, configurações ou comandos de controle.

Campos sem confirmação — corrente, alarmes e balanceamento — são sempre `null`/“Não disponível”. O histórico fica apenas em memória (últimas 360 amostras).

## Testes

```bash
../.venv/bin/python -m pytest -q
```
