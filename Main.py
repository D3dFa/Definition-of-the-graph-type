from __future__ import annotations
import argparse
import os
from collections import deque
from typing import List, Set, Tuple, Dict

class Graph:
    def __init__(self, n: int):
        self.n = n
        self.adj: List[Set[int]] = [set() for _ in range(n)]
        self.m = 0

    def add_edge(self, u: int, v: int):
        if u == v:
            raise ValueError("Петли недопустимы: u == v")
        if v in self.adj[u]:
            raise ValueError("Кратные рёбра недопустимы")
        self.adj[u].add(v)
        self.adj[v].add(u)
        self.m += 1

    @staticmethod
    def parse_from_file(path: str) -> "Graph":
        with open(path, 'r', encoding='utf-8') as f:
            raw = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
        if not raw:
            raise ValueError("Файл пуст")
        parts = raw[0].split()
        if len(parts) != 2:
            raise ValueError("Первая строка должна содержать n m")
        n, m = map(int, parts)
        if n < 1 or m < 0:
            raise ValueError("Ожидается n >= 1, m >= 0")
        edges: List[Tuple[int, int]] = []
        max_idx = -1
        for i in range(1, 1 + m):
            u, v = map(int, raw[i].split())
            edges.append((u, v))
            max_idx = max(max_idx, u, v)
        # авто-смещение индексации: 1-based -> 0-based, иначе считаем 0-based
        shift = 1 if max_idx == n else 0
        g = Graph(n)
        for (u, v) in edges:
            u0, v0 = u - shift, v - shift
            if not (0 <= u0 < n and 0 <= v0 < n):
                raise ValueError("Вершина вне диапазона после нормализации индексов")
            g.add_edge(u0, v0)
        return g

def bfs_connected_components(g: Graph) -> Tuple[bool, List[int]]:
    """Вернуть (connected, comp_id для каждой вершины)."""
    n = g.n
    comp = [-1] * n
    cid = 0
    for s in range(n):
        if comp[s] != -1:
            continue
        q = deque([s])
        comp[s] = cid
        while q:
            v = q.popleft()
            for u in g.adj[v]:
                if comp[u] == -1:
                    comp[u] = cid
                    q.append(u)
        cid += 1
    connected = (cid == 1)
    return connected, comp

def bipartite_coloring(g: Graph) -> Tuple[bool, List[int]]:
    """Двудольная раскраска BFS. Вернуть (ok, color), где color in {0,1} или -1."""
    n = g.n
    color = [-1] * n
    for s in range(n):
        if color[s] != -1:
            continue
        color[s] = 0
        q = deque([s])
        while q:
            v = q.popleft()
            for u in g.adj[v]:
                if color[u] == -1:
                    color[u] = 1 - color[v]
                    q.append(u)
                elif color[u] == color[v]:
                    return False, color
    return True, color

def is_empty(g: Graph) -> bool:
    return g.m == 0

def is_complete(g: Graph) -> bool:
    n = g.n
    exp_m = n * (n - 1) // 2
    if g.m != exp_m:
        return False
    for v in range(n):
        if len(g.adj[v]) != n - 1:
            return False
    return True

def is_cycle(g: Graph) -> bool:
    n = g.n
    if n < 3:
        return False
    if g.m != n:
        return False
    for v in range(n):
        if len(g.adj[v]) != 2:
            return False
    connected, _ = bfs_connected_components(g)
    return connected

def is_star(g: Graph) -> Tuple[bool, int]:
    # S_n == K_{1,n}: один центр степени n, остальные степени 1 (или S_0: одиночная вершина)
    n = g.n
    if n == 1:
        return True, 0
    centers = [v for v in range(n) if len(g.adj[v]) == n - 1]
    leaves = [v for v in range(n) if len(g.adj[v]) == 1]
    if len(centers) == 1 and len(leaves) == n - 1 and g.m == n - 1:
        return True, n - 1
    return False, -1

def is_bipartite(g: Graph) -> Tuple[bool, List[int], List[int]]:
    ok, color = bipartite_coloring(g)
    if not ok:
        return False, [], []
    part0 = [i for i, c in enumerate(color) if c == 0]
    part1 = [i for i, c in enumerate(color) if c == 1]
    return True, part0, part1

def is_complete_bipartite(g: Graph) -> Tuple[bool, int, int]:
    ok, A, B = is_bipartite(g)
    if not ok:
        return False, -1, -1
    a, b = len(A), len(B)
    if g.n == 1:
        return True, max(a, b), min(a, b)
    for v in A:
        if len(g.adj[v]) != b:
            return False, -1, -1
    for v in B:
        if len(g.adj[v]) != a:
            return False, -1, -1
    if g.m != a * b:
        return False, -1, -1
    m, n = sorted((a, b))
    return True, m, n

def classify(g: Graph) -> Dict:
    kinds: List[str] = []
    details: Dict = {}

    n, m = g.n, g.m
    degs = [len(g.adj[v]) for v in range(n)]

    if is_empty(g):
        kinds.append(f"пустой K{n}")
        details['empty_p'] = n

    if is_complete(g):
        kinds.append(f"полный K{n}")
        details['complete_p'] = n

    if is_cycle(g):
        kinds.append(f"цикл C{n}")
        details['cycle_k'] = n

    star_ok, star_n = is_star(g)
    if star_ok:
        kinds.append(f"звёздный S{star_n}")
        details['star_n'] = star_n

    bp_ok, A, B = is_bipartite(g)
    if bp_ok:
        kinds.append("двудольный")
        details['bipartition'] = {'A': A, 'B': B}

    kb_ok, m_part, n_part = is_complete_bipartite(g)
    if kb_ok:
        kinds.append(f"полный двудольный K{m_part},{n_part}")
        details['complete_bipartite'] = {'m': m_part, 'n': n_part}

    if not kinds:
        kinds = ["ни один из перечисленных"]

    return {
        'n': n,
        'm': m,
        'degrees': degs,
        'kinds': kinds,
        'details': details,
    }

def format_report(path: str, res: Dict) -> str:
    lines = []
    lines.append(f"Файл: {os.path.basename(path)}")
    lines.append(f"Вершины: n = {res['n']}")
    lines.append(f"Рёбра:   m = {res['m']}")
    lines.append(f"Степени: {res['degrees']}")
    lines.append("")
    lines.append("Виды графа (возможны несколько):")
    for k in res['kinds']:
        lines.append(f"  • {k}")
    if 'complete_bipartite' in res['details']:
        d = res['details']['complete_bipartite']
        lines.append(f"    (m = {d['m']}, n = {d['n']})")
    if 'bipartition' in res['details']:
        bp = res['details']['bipartition']
        lines.append(f"  Разбиение для двудольности: A={bp['A']}, B={bp['B']}")
    return "\n".join(lines) + "\n"

def iter_input_files(paths: List[str]) -> List[str]:
    files = []
    for p in paths:
        if os.path.isdir(p):
            for name in os.listdir(p):
                full = os.path.join(p, name)
                if os.path.isfile(full):
                    files.append(full)
        else:
            files.append(p)
    return files

def main():
    ap = argparse.ArgumentParser(description="Определение вида графа")
    ap.add_argument('paths', nargs='+', help='Файлы или папки с файлами графов')
    ap.add_argument('--out-dir', default=None, help='Каталог для выходных .out файлов')
    args = ap.parse_args()

    files = iter_input_files(args.paths)
    if not files:
        print("Нет входных файлов")
        return

    for path in files:
        try:
            g = Graph.parse_from_file(path)
            res = classify(g)
            text = format_report(path, res)
        except Exception as e:
            text = f"Файл: {os.path.basename(path)}\nОшибка: {e}\n"

        if args.out_dir:
            os.makedirs(args.out_dir, exist_ok=True)
            out_path = os.path.join(args.out_dir, os.path.basename(path) + '.out')
        else:
            out_path = path + '.out'
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"Готово: {out_path}")

if __name__ == '__main__':
    main()
