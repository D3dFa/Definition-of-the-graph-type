# Определение вида графа (Python, без рекурсии)

Программа читает из файлов **невзвешенные неориентированные простые** графы и определяет, к каким видам они относятся:

- цикл `C_k`
- полный `K_p`
- пустой `K_p`
- двудольный
- полный двудольный `K_{m,n}`
- звёздный `S_n`
- или «ни один из перечисленных»

Если граф подходит под несколько видов — выводятся **все** типы сразу (с параметрами `k, p, m, n`). Реализация **без рекурсии** — используется итеративный BFS (поиск в ширину).

---

## Быстрый старт

```bash
python --version             # Python 3.10+ (подойдёт и 3.8+)
python Main.py path/to/graph.txt
python Main.py graphs_dir --out-dir out
```

> Скрипт создаёт для каждого входного файла одноимённый файл отчёта с суффиксом `.out` (или складывает в `--out-dir`).

---

## Формат входа/выхода

**Вход** — текстовый файл со списком рёбер:

```
n m
u1 v1
u2 v2
...
```

- `n ≥ 1` — число вершин, `m ≥ 0` — число рёбер.
- Индексация вершин может быть **0-based** или **1-based**; определяется автоматически:
  - если максимальный номер вершины равен `n` → считаем 1-based и нормализуем к 0-based;
  - если `≤ n-1` → считаем 0-based.
- Ожидается **простой** граф: без петель (`u != v`) и без кратных рёбер.

**Выход** — текстовый отчёт (`.out`) c полями:
- `n`, `m`, вектор степеней;
- список всех подходящих видов (строки типа `цикл C5`, `полный K4`, `полный двудольный K2,3` и т.п.);
- для двудольных графов — разбиение на доли `A` и `B`.

---

## Примеры

**Цикл C5**
```
5 5
1 2
2 3
3 4
4 5
5 1
```

**Полный двудольный K2,3**
```
5 6
1 3
1 4
1 5
2 3
2 4
2 5
```

---

## Алгоритм (кратко)

- **Пустой `K_p`**: `m == 0`.
- **Полный `K_p`**: `m == n(n−1)/2` и `deg(v) == n−1` для всех `v`.
- **Цикл `C_k`**: `n ≥ 3`, `m == n`, все `deg == 2`, граф связен (BFS).
- **Двудольный**: 2‑раскраска BFS (конфликт одинаковых цветов на ребре ⇒ недвудолен).
- **Полный двудольный `K_{m,n}`**: граф двудолен с долями `A,B`; для `v ∈ A` `deg(v) == |B|`, для `u ∈ B` `deg(u) == |A|`, всего рёбер `|A||B|`.
- **Звезда `S_n`**: один центр степени `n`, остальные степени `1`; всего рёбер `n` (или `S_0` при `n=1`).

**Сложность**: время `O(n + m)`, память `O(n + m)` — линейно от размера графа.

---

## Обработка ошибок

Программа формирует понятное сообщение об ошибке, если:
- нарушен формат первой строки (`n m`);
- вершины вне диапазона (после нормализации индексов);
- найдено ребро‑петля (`u == v`) или дубль ребра;
- число строк с рёбрами меньше, чем `m`.

---

## Структура проекта

```
Main.py           # основной скрипт (класс Graph, проверки, CLI)
tests/
  test_main.py    # автотесты pytest
```

---

## Тесты (pytest)

Установка и запуск:

```bash
pip install pytest
pytest -q
```

Содержание `tests/main.py`:

```python
# -*- coding: utf-8 -*-
import importlib.util
import sys
from pathlib import Path
import pytest

# Импортируем модуль Main.py из корня репозитория
ROOT = Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "Main.py"
spec = importlib.util.spec_from_file_location("Main", str(MOD_PATH))
gk = importlib.util.module_from_spec(spec)
sys.modules["Main"] = gk
spec.loader.exec_module(gk)  # type: ignore

def build_graph(n, edges):
    g = gk.Graph(n)
    for u, v in edges:
        g.add_edge(u, v)
    return g

def kinds_of(g):
    return set(gk.classify(g)["kinds"])

def details_of(g):
    return gk.classify(g)["details"]

def test_empty_K4_and_bipartite():
    g = build_graph(4, [])
    kinds = kinds_of(g)
    assert "пустой K4" in kinds
    assert "двудольный" in kinds
    assert not any(s.startswith("полный K4") for s in kinds)

def test_complete_K4():
    n = 4
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    g = build_graph(n, edges)
    kinds = kinds_of(g)
    assert "полный K4" in kinds
    assert "двудольный" not in kinds

def test_cycle_C6_even_is_bipartite():
    n = 6
    edges = [(i, (i + 1) % n) for i in range(n)]
    g = build_graph(n, edges)
    kinds = kinds_of(g)
    assert f"цикл C{n}" in kinds
    assert "двудольный" in kinds
    assert not any("полный двудольный" in s for s in kinds)

def test_cycle_C5_odd_is_not_bipartite():
    n = 5
    edges = [(i, (i + 1) % n) for i in range(n)]
    g = build_graph(n, edges)
    kinds = kinds_of(g)
    assert f"цикл C{n}" in kinds
    assert "двудольный" not in kinds

def test_star_S4_is_K1_4_and_bipartite():
    n = 5
    edges = [(0, i) for i in range(1, n)]
    g = build_graph(n, edges)
    kinds = kinds_of(g)
    assert "звёздный S4" in kinds
    assert "двудольный" in kinds
    assert "полный двудольный K1,4" in kinds or "полный двудольный K4,1" in kinds

def test_complete_bipartite_K2_3():
    edges = [(0,2),(0,3),(0,4),(1,2),(1,3),(1,4)]
    g = build_graph(5, edges)
    kinds = kinds_of(g)
    assert "двудольный" in kinds
    assert "полный двудольный K2,3" in kinds or "полный двудольный K3,2" in kinds
    assert "звёздный" not in " ".join(kinds)

def test_single_vertex_all_that_apply():
    g = build_graph(1, [])
    kinds = kinds_of(g)
    assert "пустой K1" in kinds
    assert "полный K1" in kinds
    assert "звёздный S0" in kinds
    assert "двудольный" in kinds
    assert any(s in kinds for s in ("полный двудольный K1,0", "полный двудольный K0,1"))

def test_none_of_the_above():
    edges = [(0,1),(1,2),(2,3),(3,0),(0,2)]
    g = build_graph(4, edges)
    kinds = kinds_of(g)
    assert kinds == {"ни один из перечисленных"}

def test_parse_from_file_normalizes_indexing(tmp_path: Path):
    lines = ["4 4", "1 2", "2 3", "3 4", "4 1"]
    p = tmp_path / "c4_1b.txt"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    g = gk.Graph.parse_from_file(str(p))
    kinds = kinds_of(g)
    assert "двудольный" in kinds and "цикл C4" in kinds

def test_parse_throws_on_out_of_range_index(tmp_path: Path):
    p = tmp_path / "bad.txt"
    p.write_text("3 1\n0 5\n", encoding="utf-8")
    with pytest.raises(ValueError):
        gk.Graph.parse_from_file(str(p))

def test_add_edge_rejects_self_loop():
    g = gk.Graph(2)
    with pytest.raises(ValueError):
        g.add_edge(0, 0)

def test_add_edge_rejects_duplicate_edge():
    g = gk.Graph(3)
    g.add_edge(0, 1)
    with pytest.raises(ValueError):
        g.add_edge(0, 1)
    with pytest.raises(ValueError):
        g.add_edge(1, 0)

def test_bipartition_details_on_K2_3():
    edges = [(0,2),(0,3),(0,4),(1,2),(1,3),(1,4)]
    g = build_graph(5, edges)
    details = details_of(g)
    assert "bipartition" in details
    A = details["bipartition"]["A"]
    B = details["bipartition"]["B"]
    assert set(A) == {0, 1}
    assert set(B) == {2, 3, 4}

def test_complete_bipartite_details_on_star():
    n = 5
    edges = [(0, i) for i in range(1, n)]
    g = build_graph(n, edges)
    details = details_of(g)
    assert "complete_bipartite" in details
    mn = details["complete_bipartite"]
    assert set(mn.keys()) == {"m", "n"}
    assert sorted([mn["m"], mn["n"]]) == [1, 4]

