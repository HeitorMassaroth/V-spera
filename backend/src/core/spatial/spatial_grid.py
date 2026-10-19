"""Estrutura de dados Spatial Hash Grid 2D para consultas espaciais em O(1) médio."""

from __future__ import annotations
import math
from typing import TypeVar, Generic, Dict, List, Tuple, Optional

T = TypeVar("T")


class SpatialHashGrid(Generic[T]):
    """Grid espacial para particionamento 2D e busca acelerada de proximidade."""

    def __init__(self, cell_size: float = 60.0) -> None:
        if cell_size <= 0:
            raise ValueError("cell_size deve ser estritamente positivo.")
        self.cell_size = float(cell_size)
        self._grid: Dict[Tuple[int, int], List[Tuple[T, float, float]]] = {}
        self._item_count = 0

    @property
    def item_count(self) -> int:
        return self._item_count

    def _hash_coords(self, x: float, y: float) -> Tuple[int, int]:
        return int(math.floor(x / self.cell_size)), int(math.floor(y / self.cell_size))

    def clear(self) -> None:
        """Limpa todas as células do grid para reinserção no novo tick."""
        self._grid.clear()
        self._item_count = 0

    def insert(self, item: T, x: float, y: float) -> None:
        """Insere um item com coordenadas contínuas no grid."""
        cell = self._hash_coords(x, y)
        if cell not in self._grid:
            self._grid[cell] = []
        self._grid[cell].append((item, x, y))
        self._item_count += 1

    def query_radius(self, x: float, y: float, radius: float) -> List[Tuple[T, float]]:
        """Retorna todos os itens dentro do raio esférico e a respectiva distância euclidiana."""
        if radius <= 0:
            return []

        min_cell_x = int(math.floor((x - radius) / self.cell_size))
        max_cell_x = int(math.floor((x + radius) / self.cell_size))
        min_cell_y = int(math.floor((y - radius) / self.cell_size))
        max_cell_y = int(math.floor((y + radius) / self.cell_size))

        results: List[Tuple[T, float]] = []
        r2 = radius * radius

        for cx in range(min_cell_x, max_cell_x + 1):
            for cy in range(min_cell_y, max_cell_y + 1):
                cell_items = self._grid.get((cx, cy))
                if not cell_items:
                    continue
                for item, ix, iy in cell_items:
                    dx = ix - x
                    dy = iy - y
                    d2 = dx * dx + dy * dy
                    if d2 <= r2:
                        results.append((item, math.sqrt(d2)))

        return results

    def query_nearest(self, x: float, y: float, max_radius: float) -> Tuple[Optional[T], float]:
        """Encontra o item mais próximo dentro de max_radius. Retorna (item, dist) ou (None, inf)."""
        candidates = self.query_radius(x, y, max_radius)
        if not candidates:
            return None, float("inf")

        best_item: Optional[T] = None
        best_dist = float("inf")
        for item, dist in candidates:
            if dist < best_dist:
                best_dist = dist
                best_item = item

        return best_item, best_dist
