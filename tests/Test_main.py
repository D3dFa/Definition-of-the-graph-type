
import pytest
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "main.py"
spec = importlib.util.spec_from_file_location("main", str(MOD_PATH))
gk = importlib.util.module_from_spec(spec)
sys.modules["main"] = gk
spec.loader.exec_module(gk)  # type: ignore


# ------------------------- Хелперы -------------------------

def build_graph(n, edges):
    """Собрать граф из n и списка ребер (0-based)."""
    g = gk.Graph(n)
    for u, v in edges:
        g.add_edge(u, v)
    return g

def kinds_of(g):
    """Вернуть множество меток видов (строки) из classify()."""
    return set(gk.classify(g)["kinds"])

def details_of(g):
    """Вернуть details из classify()."""
    return gk.classify(g)["details"]


# ------------------------- Тесты корректной классификации -------------------------

def test_empty_K4_and_bipartite():
    g = build_graph(4, [])
    kinds = kinds_of(g)
    assert "пустой K4" in kinds
    # пустой граф двудолен
    assert "двудольный" in kinds
    # но не полный K4 (у полного m=6)
    assert not any(s.startswith("полный K4") for s in kinds)

def test_complete_K4():
    n = 4
    edges = [(i, j) for i in range(n) for j in range(i + 1, n)]
    g = build_graph(n, edges)
    kinds = kinds_of(g)
    assert "полный K4" in kinds
    assert "двудольный" not in kinds  # K4 недвудолен

def test_cycle_C6_even_is_bipartite():
    n = 6
    edges = [(i, (i + 1) % n) for i in range(n)]
    g = build_graph(n, edges)
    kinds = kinds_of(g)
    assert f"цикл C{n}" in kinds
    assert "двудольный" in kinds           # четный цикл двудолен
    assert not any("полный двудольный" in s for s in kinds)

def test_cycle_C5_odd_is_not_bipartite():
    n = 5
    edges = [(i, (i + 1) % n) for i in range(n)]
    g = build_graph(n, edges)
    kinds = kinds_of(g)
    assert f"цикл C{n}" in kinds
    assert "двудольный" not in kinds

def test_star_S4_is_K1_4_and_bipartite():
    # центр 0, листья 1..4
    n = 5
    edges = [(0, i) for i in range(1, n)]
    g = build_graph(n, edges)
    kinds = kinds_of(g)
    assert "звёздный S4" in kinds
    assert "двудольный" in kinds
    assert "полный двудольный K1,4" in kinds or "полный двудольный K4,1" in kinds

def test_complete_bipartite_K2_3():
    # A={0,1}, B={2,3,4}
    edges = [(0,2),(0,3),(0,4),(1,2),(1,3),(1,4)]
    g = build_graph(5, edges)
    kinds = kinds_of(g)
    assert "двудольный" in kinds
    assert "полный двудольный K2,3" in kinds or "полный двудольный K3,2" in kinds
    assert "звёздный" not in " ".join(kinds)

def test_single_vertex_all_that_apply():
    g = build_graph(1, [])
    kinds = kinds_of(g)
    # для n=1: одновременно пустой K1 и полный K1 (они совпадают)
    assert "пустой K1" in kinds
    assert "полный K1" in kinds
    # звезда S0
    assert "звёздный S0" in kinds
    # двудольный и даже полный двудольный K1,0 (или K0,1)
    assert "двудольный" in kinds
    assert any(s in kinds for s in ("полный двудольный K1,0", "полный двудольный K0,1"))

def test_none_of_the_above():
    # граф: квадрат 0-1-2-3-0 + одна диагональ 0-2
    # не пустой, не полный, не цикл, не звезда, не двудолен (есть треугольники 0-1-2 и 0-3-2)
    edges = [(0,1),(1,2),(2,3),(3,0),(0,2)]
    g = build_graph(4, edges)
    kinds = kinds_of(g)
    assert kinds == {"ни один из перечисленных"}


# ------------------------- Тесты парсера из файла -------------------------

def write_text(path: Path, text: str):
    path.write_text(text, encoding="utf-8")

@pytest.mark.parametrize("one_based", [False, True])
def test_parse_from_file_normalizes_indexing(tmp_path: Path, one_based: bool):
    # граф C4
    n = 4
    edges_0 = [(0,1),(1,2),(2,3),(3,0)]
    if one_based:
        # 1-based запись
        lines = ["4 4", "1 2", "2 3", "3 4", "4 1"]
    else:
        # 0-based запись (допустимая)
        lines = ["4 4", "0 1", "1 2", "2 3", "3 0"]
    text = "\n".join(lines) + "\n"
    p = tmp_path / ("c4_1b.txt" if one_based else "c4_0b.txt")
    write_text(p, text)

    g = gk.Graph.parse_from_file(str(p))
    kinds = kinds_of(g)
    assert "двудольный" in kinds
    assert f"цикл C{n}" in kinds

def test_parse_throws_on_out_of_range_index(tmp_path: Path):
    # n=3, но ребро 0-5 (или 1-based 1-6) — должно упасть
    p = tmp_path / "bad.txt"
    write_text(p, "3 1\n0 5\n")
    with pytest.raises(ValueError):
        gk.Graph.parse_from_file(str(p))


# ------------------------- Тесты ошибок в Graph.add_edge -------------------------

def test_add_edge_rejects_self_loop():
    g = gk.Graph(2)
    with pytest.raises(ValueError):
        g.add_edge(0, 0)

def test_add_edge_rejects_duplicate_edge():
    g = gk.Graph(3)
    g.add_edge(0, 1)
    with pytest.raises(ValueError):
        g.add_edge(0, 1)  # дубль
    with pytest.raises(ValueError):
        g.add_edge(1, 0)  # дубль в обратном порядке


# ------------------------- Тесты деталей (details) -------------------------

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
    # S4 == K1,4
    n = 5
    edges = [(0, i) for i in range(1, n)]
    g = build_graph(n, edges)
    details = details_of(g)
    assert "complete_bipartite" in details
    mn = details["complete_bipartite"]
    # параметры нормализованы так, что m <= n (в коде это гарантируется для общего случая),
    # для звезды ожидаем {m:1, n:4}
    assert set(mn.keys()) == {"m", "n"}
    assert sorted([mn["m"], mn["n"]]) == [1, 4]
