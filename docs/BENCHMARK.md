# Benchmark desde el USB — 2026-09-19

Condiciones: `D:\CodeSolver`, modelo Qwen3.5-4B-UD-Q4_K_XL (perfil MEDIUM), Vulkan sobre Iris Xe, laptop i9-13900H **en batería**, 6.4 tok/s, presupuesto de pensamiento 804 tokens, límite 600 s por problema, 2 reparaciones + rethink. Lenguaje: Python. Interrumpido en el problema 19 de 27 por apagado de la laptop.

## Resultado: 16 de 18 resueltos (89 %)

| Problema | Categoría | Resultado | Tiempo |
|---|---|---|---|
| p001 sum_pairs | hash map | PASS 1er intento | 2.6 min |
| p002 shortest_path_grid | BFS grid, T casos | TIMEOUT (2 intentos) | 10 min |
| p003 big_factorial_digits | big ints | PASS 1er intento | 3.2 min |
| p004 hills | arrays | PASS 1er intento | 2.3 min |
| p005 palindrome_shuffle | strings, T casos | PASS 1er intento | 3.3 min |
| p006 divisor_stats | teoría de números | PASS 1er intento | 3.6 min |
| p007 contest_ranking | sorting | TIMEOUT (1 intento largo) | 10.7 min |
| p008 first_not_less | binary search | PASS 1er intento | 3.6 min |
| p009 favorite_digit | counting | PASS 1er intento | 3.9 min |
| p010 pair_target | two pointers | PASS 1er intento | 3.7 min |
| p011 k_distinct_window | sliding window | PASS 1er intento | 3.7 min |
| p012 range_sums | prefix sums | PASS 1er intento | 4.6 min |
| p013 brackets | stack, T casos | PASS tras 2 reparaciones | 9.9 min |
| p014 fire_spread | BFS multi-fuente | PASS 1er intento | 5.8 min |
| p015 components | DSU/DFS | PASS 1er intento | 4.3 min |
| p016 boats | greedy | PASS 1er intento | 3.6 min |
| p017 broken_stairs | DP 1D | PASS 1er intento | 3.6 min |
| p018 common_subsequence | DP 2D (LCS), T casos | PASS 1er intento | 4.1 min |

- Al primer intento: 15 de 18 (83 %). Tras reparar: +1. Fallos: 2 (ambos por límite de tiempo, no por respuesta incorrecta final).
- Tiempo medio de los resueltos al primer intento: 3.6 min. Rango 2.3-5.8 min.
- p002 había pasado al primer intento en una corrida anterior desde C: → variabilidad del muestreo (temperature 0.6).
- p007 agotó 600 s en una sola generación: el modelo escribió hasta el máximo de tokens. Ajuste pendiente: bajar `max_answer_tokens` (2500 → 1800) o subir `solve_timeout_seconds` a 900.

## Conclusiones para la competencia

1. En problemas fáciles y medios de los tipos habituales (arrays, strings, math, búsqueda binaria, hashing, two pointers, ventana, prefijos, grafos básicos, greedy, DP básica) la tasa de acierto está entre 80 y 90 % con el 4B a 6 tok/s.
2. Cuenta 3-4 minutos por problema resuelto y 10 minutos cuando falla. Con corriente conectada los tiempos bajan.
3. Los fallos observados son por tiempo, no por código incorrecto entregado como bueno: el sistema nunca marcó PASS un código erróneo.
4. Pendiente (M4): completar los problemas 19-27, probar JavaScript, y ajustar `max_answer_tokens` / `solve_timeout_seconds`.
