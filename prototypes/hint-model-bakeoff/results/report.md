
### gpu-l4-qwen35-4b (m), prompt v1, leak check v4, 78 hints, extra body `{"chat_template_kwargs": {"enable_thinking": false}}`

#### per language x rung

| group | n | leak a1 (of valid a1) | a1 timeout / request error / invalid JSON | leak a2 (a1 leaked and a2 valid: leaked again) (a2 timeout / request error / invalid JSON) | residual (a1 leaked, template shown) | template fallback | fallback causes: timeout / request error / no time to retry / over budget / rejected twice (sum = template) | JSON valid a1 | JSON valid a1+a2 | possible gate misses | unparsed formulas | <think> left | attempts with reasoning (thinking not off?) | latency median / p95 (s); p95 is the max when n<30 | >20 s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ('en', 1) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 3.2 / 4.3 (max, n<30) | 0 |
| ('en', 2) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 2.8 / 4.2 (max, n<30) | 0 |
| ('en', 3) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 2.9 / 3.6 (max, n<30) | 0 |
| ('ro', 1) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 3.8 / 4.5 (max, n<30) | 0 |
| ('ro', 2) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 3.3 / 4.3 (max, n<30) | 0 |
| ('ro', 3) | 13 | 8% (1/13) | 0 / 0 / 0 | 0% (0/1) (0 / 0 / 0) | 0% (0/1) | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (14/14) | 0 | 0 | 0 | 0 | 3.5 / 7.1 (max, n<30) | 0 |

#### per language and overall

| group | n | leak a1 (of valid a1) | a1 timeout / request error / invalid JSON | leak a2 (a1 leaked and a2 valid: leaked again) (a2 timeout / request error / invalid JSON) | residual (a1 leaked, template shown) | template fallback | fallback causes: timeout / request error / no time to retry / over budget / rejected twice (sum = template) | JSON valid a1 | JSON valid a1+a2 | possible gate misses | unparsed formulas | <think> left | attempts with reasoning (thinking not off?) | latency median / p95 (s); p95 is the max when n<30 | >20 s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 78 | 1% (1/78) | 0 / 0 / 0 | 0% (0/1) (0 / 0 / 0) | 0% (0/1) | 0% (0/78) | 0 / 0 / 0 / 0 / 0 | 100% (78/78) | 100% (79/79) | 0 | 0 | 0 | 0 | 3.2 / 4.3 | 0 |
| en | 39 | 0% (0/39) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/39) | 0 / 0 / 0 / 0 / 0 | 100% (39/39) | 100% (39/39) | 0 | 0 | 0 | 0 | 3.0 / 4.2 | 0 |
| ro | 39 | 3% (1/39) | 0 / 0 / 0 | 0% (0/1) (0 / 0 / 0) | 0% (0/1) | 0% (0/39) | 0 / 0 / 0 / 0 / 0 | 100% (39/39) | 100% (40/40) | 0 | 0 | 0 | 0 | 3.6 / 4.5 | 0 |

#### per step (both languages, all rungs)

| group | n | leak a1 (of valid a1) | a1 timeout / request error / invalid JSON | leak a2 (a1 leaked and a2 valid: leaked again) (a2 timeout / request error / invalid JSON) | residual (a1 leaked, template shown) | template fallback | fallback causes: timeout / request error / no time to retry / over budget / rejected twice (sum = template) | JSON valid a1 | JSON valid a1+a2 | possible gate misses | unparsed formulas | <think> left | attempts with reasoning (thinking not off?) | latency median / p95 (s); p95 is the max when n<30 | >20 s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| both | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.4 / 4.3 (max, n<30) | 0 |
| brack | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 2.9 / 3.3 (max, n<30) | 0 |
| dec | 6 | 17% (1/6) | 0 / 0 / 0 | 0% (0/1) (0 / 0 / 0) | 0% (0/1) | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (7/7) | 0 | 0 | 0 | 0 | 3.1 / 7.1 (max, n<30) | 0 |
| dom | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 2.8 / 3.8 (max, n<30) | 0 |
| frac | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 2.8 / 3.9 (max, n<30) | 0 |
| ineq | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.1 / 3.9 (max, n<30) | 0 |
| lin2 | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.1 / 3.5 (max, n<30) | 0 |
| log | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.9 / 4.3 (max, n<30) | 0 |
| quad | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.2 / 3.9 (max, n<30) | 0 |
| rearr | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.0 / 3.7 (max, n<30) | 0 |
| sqrt | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.8 / 4.1 (max, n<30) | 0 |
| sys | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.5 / 4.5 (max, n<30) | 0 |
| wrong | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.9 / 4.4 (max, n<30) | 0 |

### gpu-l4-qwen35-9b (m), prompt v1, leak check v4, 78 hints, extra body `{"chat_template_kwargs": {"enable_thinking": false}}`

#### per language x rung

| group | n | leak a1 (of valid a1) | a1 timeout / request error / invalid JSON | leak a2 (a1 leaked and a2 valid: leaked again) (a2 timeout / request error / invalid JSON) | residual (a1 leaked, template shown) | template fallback | fallback causes: timeout / request error / no time to retry / over budget / rejected twice (sum = template) | JSON valid a1 | JSON valid a1+a2 | possible gate misses | unparsed formulas | <think> left | attempts with reasoning (thinking not off?) | latency median / p95 (s); p95 is the max when n<30 | >20 s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ('en', 1) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 4.2 / 5.3 (max, n<30) | 0 |
| ('en', 2) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 3.6 / 4.4 (max, n<30) | 0 |
| ('en', 3) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 3.2 / 4.0 (max, n<30) | 0 |
| ('ro', 1) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 4.5 / 6.4 (max, n<30) | 0 |
| ('ro', 2) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 4.1 / 5.1 (max, n<30) | 0 |
| ('ro', 3) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 4.2 / 5.4 (max, n<30) | 0 |

#### per language and overall

| group | n | leak a1 (of valid a1) | a1 timeout / request error / invalid JSON | leak a2 (a1 leaked and a2 valid: leaked again) (a2 timeout / request error / invalid JSON) | residual (a1 leaked, template shown) | template fallback | fallback causes: timeout / request error / no time to retry / over budget / rejected twice (sum = template) | JSON valid a1 | JSON valid a1+a2 | possible gate misses | unparsed formulas | <think> left | attempts with reasoning (thinking not off?) | latency median / p95 (s); p95 is the max when n<30 | >20 s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 78 | 0% (0/78) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/78) | 0 / 0 / 0 / 0 / 0 | 100% (78/78) | 100% (78/78) | 0 | 0 | 0 | 0 | 4.0 / 5.3 | 0 |
| en | 39 | 0% (0/39) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/39) | 0 / 0 / 0 / 0 / 0 | 100% (39/39) | 100% (39/39) | 0 | 0 | 0 | 0 | 3.5 / 5.3 | 0 |
| ro | 39 | 0% (0/39) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/39) | 0 / 0 / 0 / 0 / 0 | 100% (39/39) | 100% (39/39) | 0 | 0 | 0 | 0 | 4.2 / 5.6 | 0 |

#### per step (both languages, all rungs)

| group | n | leak a1 (of valid a1) | a1 timeout / request error / invalid JSON | leak a2 (a1 leaked and a2 valid: leaked again) (a2 timeout / request error / invalid JSON) | residual (a1 leaked, template shown) | template fallback | fallback causes: timeout / request error / no time to retry / over budget / rejected twice (sum = template) | JSON valid a1 | JSON valid a1+a2 | possible gate misses | unparsed formulas | <think> left | attempts with reasoning (thinking not off?) | latency median / p95 (s); p95 is the max when n<30 | >20 s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| both | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 4.3 / 5.3 (max, n<30) | 0 |
| brack | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.7 / 5.0 (max, n<30) | 0 |
| dec | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.9 / 4.3 (max, n<30) | 0 |
| dom | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.6 / 5.2 (max, n<30) | 0 |
| frac | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.8 / 5.0 (max, n<30) | 0 |
| ineq | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.9 / 5.6 (max, n<30) | 0 |
| lin2 | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.8 / 4.4 (max, n<30) | 0 |
| log | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 4.8 / 6.4 (max, n<30) | 0 |
| quad | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.8 / 4.3 (max, n<30) | 0 |
| rearr | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.7 / 4.8 (max, n<30) | 0 |
| sqrt | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 4.3 / 5.3 (max, n<30) | 0 |
| sys | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 4.1 / 5.1 (max, n<30) | 0 |
| wrong | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 4.3 / 5.4 (max, n<30) | 0 |

### gpu-l4-gemma4-e4b (m), prompt v1, leak check v4, 78 hints, extra body `{}`

#### per language x rung

| group | n | leak a1 (of valid a1) | a1 timeout / request error / invalid JSON | leak a2 (a1 leaked and a2 valid: leaked again) (a2 timeout / request error / invalid JSON) | residual (a1 leaked, template shown) | template fallback | fallback causes: timeout / request error / no time to retry / over budget / rejected twice (sum = template) | JSON valid a1 | JSON valid a1+a2 | possible gate misses | unparsed formulas | <think> left | attempts with reasoning (thinking not off?) | latency median / p95 (s); p95 is the max when n<30 | >20 s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ('en', 1) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 3.6 / 6.6 (max, n<30) | 0 |
| ('en', 2) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 4.0 / 5.4 (max, n<30) | 0 |
| ('en', 3) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 4.0 / 6.0 (max, n<30) | 0 |
| ('ro', 1) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 4.0 / 5.3 (max, n<30) | 0 |
| ('ro', 2) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 4.9 / 6.6 (max, n<30) | 0 |
| ('ro', 3) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 4.3 / 6.0 (max, n<30) | 0 |

#### per language and overall

| group | n | leak a1 (of valid a1) | a1 timeout / request error / invalid JSON | leak a2 (a1 leaked and a2 valid: leaked again) (a2 timeout / request error / invalid JSON) | residual (a1 leaked, template shown) | template fallback | fallback causes: timeout / request error / no time to retry / over budget / rejected twice (sum = template) | JSON valid a1 | JSON valid a1+a2 | possible gate misses | unparsed formulas | <think> left | attempts with reasoning (thinking not off?) | latency median / p95 (s); p95 is the max when n<30 | >20 s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 78 | 0% (0/78) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/78) | 0 / 0 / 0 / 0 / 0 | 100% (78/78) | 100% (78/78) | 0 | 0 | 0 | 0 | 4.1 / 6.0 | 0 |
| en | 39 | 0% (0/39) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/39) | 0 / 0 / 0 / 0 / 0 | 100% (39/39) | 100% (39/39) | 0 | 0 | 0 | 0 | 3.9 / 6.0 | 0 |
| ro | 39 | 0% (0/39) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/39) | 0 / 0 / 0 / 0 / 0 | 100% (39/39) | 100% (39/39) | 0 | 0 | 0 | 0 | 4.5 / 6.0 | 0 |

#### per step (both languages, all rungs)

| group | n | leak a1 (of valid a1) | a1 timeout / request error / invalid JSON | leak a2 (a1 leaked and a2 valid: leaked again) (a2 timeout / request error / invalid JSON) | residual (a1 leaked, template shown) | template fallback | fallback causes: timeout / request error / no time to retry / over budget / rejected twice (sum = template) | JSON valid a1 | JSON valid a1+a2 | possible gate misses | unparsed formulas | <think> left | attempts with reasoning (thinking not off?) | latency median / p95 (s); p95 is the max when n<30 | >20 s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| both | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 4.1 / 4.9 (max, n<30) | 0 |
| brack | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.8 / 4.2 (max, n<30) | 0 |
| dec | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.7 / 4.9 (max, n<30) | 0 |
| dom | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.9 / 4.8 (max, n<30) | 0 |
| frac | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 4.5 / 6.0 (max, n<30) | 0 |
| ineq | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.5 / 4.7 (max, n<30) | 0 |
| lin2 | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 4.7 / 5.7 (max, n<30) | 0 |
| log | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 5.5 / 6.6 (max, n<30) | 0 |
| quad | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.9 / 5.1 (max, n<30) | 0 |
| rearr | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.3 / 4.1 (max, n<30) | 0 |
| sqrt | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 4.7 / 6.0 (max, n<30) | 0 |
| sys | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 4.4 / 5.0 (max, n<30) | 0 |
| wrong | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 4.2 / 4.7 (max, n<30) | 0 |

### gpu-l4-ministral3-8b (m), prompt v1, leak check v4, 78 hints, extra body `{}`

#### per language x rung

| group | n | leak a1 (of valid a1) | a1 timeout / request error / invalid JSON | leak a2 (a1 leaked and a2 valid: leaked again) (a2 timeout / request error / invalid JSON) | residual (a1 leaked, template shown) | template fallback | fallback causes: timeout / request error / no time to retry / over budget / rejected twice (sum = template) | JSON valid a1 | JSON valid a1+a2 | possible gate misses | unparsed formulas | <think> left | attempts with reasoning (thinking not off?) | latency median / p95 (s); p95 is the max when n<30 | >20 s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ('en', 1) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 1 | 0 | 0 | 3.6 / 5.3 (max, n<30) | 0 |
| ('en', 2) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 1 | 0 | 0 | 0 | 3.4 / 5.4 (max, n<30) | 0 |
| ('en', 3) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 3.3 / 5.3 (max, n<30) | 0 |
| ('ro', 1) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 3.8 / 6.4 (max, n<30) | 0 |
| ('ro', 2) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 1 | 0 | 0 | 0 | 5.1 / 6.5 (max, n<30) | 0 |
| ('ro', 3) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 1 | 0 | 0 | 4.1 / 6.7 (max, n<30) | 0 |

#### per language and overall

| group | n | leak a1 (of valid a1) | a1 timeout / request error / invalid JSON | leak a2 (a1 leaked and a2 valid: leaked again) (a2 timeout / request error / invalid JSON) | residual (a1 leaked, template shown) | template fallback | fallback causes: timeout / request error / no time to retry / over budget / rejected twice (sum = template) | JSON valid a1 | JSON valid a1+a2 | possible gate misses | unparsed formulas | <think> left | attempts with reasoning (thinking not off?) | latency median / p95 (s); p95 is the max when n<30 | >20 s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 78 | 0% (0/78) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/78) | 0 / 0 / 0 / 0 / 0 | 100% (78/78) | 100% (78/78) | 2 | 2 | 0 | 0 | 3.8 / 5.9 | 0 |
| en | 39 | 0% (0/39) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/39) | 0 / 0 / 0 / 0 / 0 | 100% (39/39) | 100% (39/39) | 1 | 1 | 0 | 0 | 3.5 / 5.3 | 0 |
| ro | 39 | 0% (0/39) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/39) | 0 / 0 / 0 / 0 / 0 | 100% (39/39) | 100% (39/39) | 1 | 1 | 0 | 0 | 4.0 / 6.5 | 0 |

#### per step (both languages, all rungs)

| group | n | leak a1 (of valid a1) | a1 timeout / request error / invalid JSON | leak a2 (a1 leaked and a2 valid: leaked again) (a2 timeout / request error / invalid JSON) | residual (a1 leaked, template shown) | template fallback | fallback causes: timeout / request error / no time to retry / over budget / rejected twice (sum = template) | JSON valid a1 | JSON valid a1+a2 | possible gate misses | unparsed formulas | <think> left | attempts with reasoning (thinking not off?) | latency median / p95 (s); p95 is the max when n<30 | >20 s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| both | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.7 / 4.1 (max, n<30) | 0 |
| brack | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.0 / 3.8 (max, n<30) | 0 |
| dec | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.5 / 3.8 (max, n<30) | 0 |
| dom | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.4 / 5.3 (max, n<30) | 0 |
| frac | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.8 / 5.1 (max, n<30) | 0 |
| ineq | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.5 / 5.6 (max, n<30) | 0 |
| lin2 | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.5 / 4.1 (max, n<30) | 0 |
| log | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 5.3 / 6.4 (max, n<30) | 0 |
| quad | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 2 | 0 | 0 | 0 | 3.8 / 5.9 (max, n<30) | 0 |
| rearr | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.4 / 3.9 (max, n<30) | 0 |
| sqrt | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 1 | 0 | 0 | 5.6 / 6.7 (max, n<30) | 0 |
| sys | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 4.2 / 5.2 (max, n<30) | 0 |
| wrong | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 1 | 0 | 0 | 5.1 / 5.5 (max, n<30) | 0 |

### gpu-l4-eurollm9b (m), prompt v1, leak check v4, 78 hints, extra body `{}`

#### per language x rung

| group | n | leak a1 (of valid a1) | a1 timeout / request error / invalid JSON | leak a2 (a1 leaked and a2 valid: leaked again) (a2 timeout / request error / invalid JSON) | residual (a1 leaked, template shown) | template fallback | fallback causes: timeout / request error / no time to retry / over budget / rejected twice (sum = template) | JSON valid a1 | JSON valid a1+a2 | possible gate misses | unparsed formulas | <think> left | attempts with reasoning (thinking not off?) | latency median / p95 (s); p95 is the max when n<30 | >20 s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ('en', 1) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 3 | 0 | 0 | 3.9 / 5.4 (max, n<30) | 0 |
| ('en', 2) | 13 | 0% (0/12) | 1 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 8% (1/13) | 1 / 0 / 0 / 0 / 0 | 100% (12/12) | 100% (12/12) | 0 | 1 | 0 | 0 | 4.2 / 20.0 (max, n<30) | 1 |
| ('en', 3) | 13 | 8% (1/13) | 0 / 0 / 0 | 100% (1/1) (0 / 0 / 0) | 100% (1/1) | 8% (1/13) | 0 / 0 / 0 / 0 / 1 | 100% (13/13) | 100% (14/14) | 0 | 0 | 0 | 0 | 3.7 / 8.1 (max, n<30) | 0 |
| ('ro', 1) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 1 | 0 | 0 | 3.8 / 7.8 (max, n<30) | 0 |
| ('ro', 2) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 4.5 / 13.1 (max, n<30) | 0 |
| ('ro', 3) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 3.6 / 5.2 (max, n<30) | 0 |

#### per language and overall

| group | n | leak a1 (of valid a1) | a1 timeout / request error / invalid JSON | leak a2 (a1 leaked and a2 valid: leaked again) (a2 timeout / request error / invalid JSON) | residual (a1 leaked, template shown) | template fallback | fallback causes: timeout / request error / no time to retry / over budget / rejected twice (sum = template) | JSON valid a1 | JSON valid a1+a2 | possible gate misses | unparsed formulas | <think> left | attempts with reasoning (thinking not off?) | latency median / p95 (s); p95 is the max when n<30 | >20 s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 78 | 1% (1/77) | 1 / 0 / 0 | 100% (1/1) (0 / 0 / 0) | 100% (1/1) | 3% (2/78) | 1 / 0 / 0 / 0 / 1 | 100% (77/77) | 100% (78/78) | 0 | 5 | 0 | 0 | 3.9 / 7.8 | 1 |
| en | 39 | 3% (1/38) | 1 / 0 / 0 | 100% (1/1) (0 / 0 / 0) | 100% (1/1) | 5% (2/39) | 1 / 0 / 0 / 0 / 1 | 100% (38/38) | 100% (39/39) | 0 | 4 | 0 | 0 | 3.9 / 8.1 | 1 |
| ro | 39 | 0% (0/39) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/39) | 0 / 0 / 0 / 0 / 0 | 100% (39/39) | 100% (39/39) | 0 | 1 | 0 | 0 | 4.0 / 7.8 | 0 |

#### per step (both languages, all rungs)

| group | n | leak a1 (of valid a1) | a1 timeout / request error / invalid JSON | leak a2 (a1 leaked and a2 valid: leaked again) (a2 timeout / request error / invalid JSON) | residual (a1 leaked, template shown) | template fallback | fallback causes: timeout / request error / no time to retry / over budget / rejected twice (sum = template) | JSON valid a1 | JSON valid a1+a2 | possible gate misses | unparsed formulas | <think> left | attempts with reasoning (thinking not off?) | latency median / p95 (s); p95 is the max when n<30 | >20 s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| both | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.6 / 4.8 (max, n<30) | 0 |
| brack | 6 | 17% (1/6) | 0 / 0 / 0 | 100% (1/1) (0 / 0 / 0) | 100% (1/1) | 17% (1/6) | 0 / 0 / 0 / 0 / 1 | 100% (6/6) | 100% (7/7) | 0 | 0 | 0 | 0 | 3.7 / 8.1 (max, n<30) | 0 |
| dec | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.8 / 4.1 (max, n<30) | 0 |
| dom | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.7 / 5.0 (max, n<30) | 0 |
| frac | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.8 / 4.1 (max, n<30) | 0 |
| ineq | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 2 | 0 | 0 | 3.9 / 6.4 (max, n<30) | 0 |
| lin2 | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.2 / 4.6 (max, n<30) | 0 |
| log | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 3 | 0 | 0 | 5.6 / 6.5 (max, n<30) | 0 |
| quad | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.6 / 4.5 (max, n<30) | 0 |
| rearr | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 3.7 / 4.8 (max, n<30) | 0 |
| sqrt | 6 | 0% (0/5) | 1 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 17% (1/6) | 1 / 0 / 0 / 0 / 0 | 100% (5/5) | 100% (5/5) | 0 | 0 | 0 | 0 | 6.5 / 20.0 (max, n<30) | 1 |
| sys | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 4.7 / 5.4 (max, n<30) | 0 |
| wrong | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 4.3 / 5.4 (max, n<30) | 0 |

### cpu-q35-4b-q4km (qwen3.5-4b), prompt v1, leak check v4, 78 hints, extra body `{"chat_template_kwargs": {"enable_thinking": false}}`

#### per language x rung

| group | n | leak a1 (of valid a1) | a1 timeout / request error / invalid JSON | leak a2 (a1 leaked and a2 valid: leaked again) (a2 timeout / request error / invalid JSON) | residual (a1 leaked, template shown) | template fallback | fallback causes: timeout / request error / no time to retry / over budget / rejected twice (sum = template) | JSON valid a1 | JSON valid a1+a2 | possible gate misses | unparsed formulas | <think> left | attempts with reasoning (thinking not off?) | latency median / p95 (s); p95 is the max when n<30 | >20 s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ('en', 1) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 7.3 / 8.6 (max, n<30) | 0 |
| ('en', 2) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 6.5 / 8.2 (max, n<30) | 0 |
| ('en', 3) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 6.6 / 8.2 (max, n<30) | 0 |
| ('ro', 1) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 8.9 / 10.5 (max, n<30) | 0 |
| ('ro', 2) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 7.9 / 10.1 (max, n<30) | 0 |
| ('ro', 3) | 13 | 0% (0/13) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/13) | 0 / 0 / 0 / 0 / 0 | 100% (13/13) | 100% (13/13) | 0 | 0 | 0 | 0 | 7.2 / 9.2 (max, n<30) | 0 |

#### per language and overall

| group | n | leak a1 (of valid a1) | a1 timeout / request error / invalid JSON | leak a2 (a1 leaked and a2 valid: leaked again) (a2 timeout / request error / invalid JSON) | residual (a1 leaked, template shown) | template fallback | fallback causes: timeout / request error / no time to retry / over budget / rejected twice (sum = template) | JSON valid a1 | JSON valid a1+a2 | possible gate misses | unparsed formulas | <think> left | attempts with reasoning (thinking not off?) | latency median / p95 (s); p95 is the max when n<30 | >20 s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| all | 78 | 0% (0/78) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/78) | 0 / 0 / 0 / 0 / 0 | 100% (78/78) | 100% (78/78) | 0 | 0 | 0 | 0 | 7.5 / 9.4 | 0 |
| en | 39 | 0% (0/39) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/39) | 0 / 0 / 0 / 0 / 0 | 100% (39/39) | 100% (39/39) | 0 | 0 | 0 | 0 | 6.7 / 8.5 | 0 |
| ro | 39 | 0% (0/39) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/39) | 0 / 0 / 0 / 0 / 0 | 100% (39/39) | 100% (39/39) | 0 | 0 | 0 | 0 | 7.9 / 10.4 | 0 |

#### per step (both languages, all rungs)

| group | n | leak a1 (of valid a1) | a1 timeout / request error / invalid JSON | leak a2 (a1 leaked and a2 valid: leaked again) (a2 timeout / request error / invalid JSON) | residual (a1 leaked, template shown) | template fallback | fallback causes: timeout / request error / no time to retry / over budget / rejected twice (sum = template) | JSON valid a1 | JSON valid a1+a2 | possible gate misses | unparsed formulas | <think> left | attempts with reasoning (thinking not off?) | latency median / p95 (s); p95 is the max when n<30 | >20 s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| both | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 7.5 / 10.4 (max, n<30) | 0 |
| brack | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 6.5 / 7.5 (max, n<30) | 0 |
| dec | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 7.7 / 8.0 (max, n<30) | 0 |
| dom | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 6.8 / 9.1 (max, n<30) | 0 |
| frac | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 7.0 / 9.1 (max, n<30) | 0 |
| ineq | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 5.9 / 8.9 (max, n<30) | 0 |
| lin2 | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 7.5 / 9.4 (max, n<30) | 0 |
| log | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 8.3 / 9.0 (max, n<30) | 0 |
| quad | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 7.9 / 9.1 (max, n<30) | 0 |
| rearr | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 6.4 / 8.8 (max, n<30) | 0 |
| sqrt | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 8.2 / 9.2 (max, n<30) | 0 |
| sys | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 8.1 / 10.5 (max, n<30) | 0 |
| wrong | 6 | 0% (0/6) | 0 / 0 / 0 | no valid retry (0 / 0 / 0) | - | 0% (0/6) | 0 / 0 / 0 / 0 / 0 | 100% (6/6) | 100% (6/6) | 0 | 0 | 0 | 0 | 8.2 / 10.1 (max, n<30) | 0 |
