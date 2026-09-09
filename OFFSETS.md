# Offsets V2 — frames reais

Fonte primária: 45 frames em `tests/fixtures/`; todos têm 300 bytes, header `55 AA EB 90` e checksum válido (`sum(frame[:-1]) & 0xFF == frame[299]`).

|Campo|Frame|Offset|Tam.|Conversão|Valor 1º 0x02|Confiança|
|-|-:|-:|-:|-|-:|-|
|Header|todos|0–3|4|literal|`55 AA EB 90`|CONFIRMADO|
|Tipo|todos|4|1|u8|01/02/03|CONFIRMADO|
|Célula N|02|`6+2*(N-1)`|2|LE u16 mV|C1=4051; C17=4038|CONFIRMADO|
|Células ativas|02|6–39|34|slots LE não nulos|17|CONFIRMADO|
|Pack|02|150–153|4|LE u32 /1000|68.736 V|CONFIRMADO|
|Temperatura 1|02|162–163|2|LE u16 /10|37.7 °C|CONFIRMADO|
|Temperatura 2|02|164–165|2|LE u16 /10|34.2 °C|CONFIRMADO|
|SOC|02|173|1|u8 %|100|FORTE EVIDÊNCIA|
|Capacidade restante|02|174–177|4|LE u32 /1000|39.954 Ah|CONFIRMADO|
|Capacidade nominal|02|178–181|4|LE u32 /1000|40.000 Ah|CONFIRMADO|
|SOH|02|190–191|2|LE u16 %|100|FORTE EVIDÊNCIA|
|Modelo|03|6–29|24|ASCII NUL-slot|JK-BD4A20S4P|CONFIRMADO|
|Versão|03|30–45|16|ASCII NUL-slot|19.27|CONFIRMADO|
|ID|03|46–61|16|ASCII NUL-slot|512261K33000148|CONFIRMADO|

Soma das células no primeiro 0x02: **68.737 V**; pack: **68.736 V** (1 mV). Nos 42 frames a diferença soma–pack é -25 a +15 mV. Máxima, mínima, delta e potência são calculados das células confirmadas; potência fica indisponível até a corrente ser confirmada.

**INCERTOS:** corrente, ciclos, carga, descarga, balanceamento, corrente de balanceamento, alarmes e máximos/mínimos reportados. Bytes dinâmicos em 170–171, 194–195, 230, 234, 246–247 e 262–263 não são nomeados pela V2.

|Campo solicitado|Offset / valor|Confiança|
|-|-|-|
|Corrente|170–171 é um candidato dinâmico (LE signed: -413 a -385); unidade e semântica não comprovadas|INCERTO|
|Ciclos|nenhuma correspondência verificável nesta amostra|INCERTO|
|Carga / descarga|nenhuma correspondência verificável nesta amostra|INCERTO|
|Balanceamento / corrente de balanceamento|nenhuma correspondência verificável nesta amostra|INCERTO|
|Alarmes|nenhuma correspondência verificável nesta amostra|INCERTO|
|Maior célula / menor célula / delta reportados|não mapeados; calculados dos slots confirmados|CONFIRMADO como cálculo, INCERTO como campo bruto|
|Potência|não calculada enquanto a corrente bruta for incerta|INCERTO|
