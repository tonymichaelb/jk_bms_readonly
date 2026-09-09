# V3 — análise restrita aos 42 frames 0x02 reais

Os frames comprovam novamente 17 células em `6–39` (LE, mV), pack em `150–153`, T1 em `162–163` e T2 em `164–165`. A soma das células e o pack diferem de -25 a +15 mV nas 42 capturas; portanto os campos já confirmados permanecem válidos.

|Campo|Offset|Bytes no primeiro frame|Endian|Fator/unidade|Valor|Confiança|
|-|-|-|-|-|-|-|
|Corrente candidata|154–157|`00 00 00 00`|LE signed i32|fator não comprovado / A|0 bruto|FORTE EVIDÊNCIA|
|Corrente de balanceamento candidata|158–161|`00 00 00 00`|LE signed i32|fator não comprovado / A|0 bruto|INCERTO|
|Temperatura 1|162–163|`79 01`|LE u16|/10 °C|37.7 °C|CONFIRMADO|
|Temperatura 2|164–165|`56 01`|LE u16|/10 °C|34.2 °C|CONFIRMADO|
|Bloco de flags de estado|196–199|`08 00 01 01`|raw|sem fator|não decodificado|INCERTO|
|Bloco candidato de alarmes|200–215|`00` × 16|raw|sem fator|não decodificado|INCERTO|
|Charge enable/state|não identificado|—|—|—|—|INCERTO|
|Discharge enable/state|não identificado|—|—|—|—|INCERTO|
|Balance enable/state|não identificado|—|—|—|—|INCERTO|

Os offsets que mudaram entre frames foram: células, pack `150`, bytes `170–171`, `194–195`, `230`, `234`, `246–247` e `262–263`. Sem uma captura em que corrente, alarme ou estado conhecido mude de forma independente, associar qualquer um deles a uma função seria especulação. A V3 expõe tais bytes como candidatos, mas não os converte em telemetria.
