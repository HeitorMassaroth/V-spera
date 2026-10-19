"""Gerador pseudoaleatório determinístico encapsulado para experimentos do VÉSPERA."""

from __future__ import annotations
import random
from typing import Any, Tuple


class PRNG:
    """Instância isolada de gerador pseudoaleatório baseada no algoritmo Mersenne Twister.
    
    Garante que cada experimento mantenha sua própria sequência estocástica isolada,
    evitando efeitos colaterais de bibliotecas que utilizam o estado global de random.
    """

    def __init__(self, seed: int | None = None) -> None:
        self._seed = seed if seed is not None else random.randint(0, 2**32 - 1)
        self._rng = random.Random(self._seed)

    @property
    def seed_value(self) -> int:
        return self._seed

    def reseed(self, seed: int) -> None:
        """Reinicia a sequência pseudoaleatória com uma nova semente."""
        self._seed = seed
        self._rng.seed(seed)

    def random(self) -> float:
        """Retorna um float no intervalo [0.0, 1.0)."""
        return self._rng.random()

    def uniform(self, a: float, b: float) -> float:
        """Retorna um float distribuído uniformemente em [a, b]."""
        return self._rng.uniform(a, b)

    def randint(self, a: int, b: int) -> int:
        """Retorna um inteiro aleatório no intervalo [a, b] inclusive."""
        return self._rng.randint(a, b)

    def gauss(self, mu: float = 0.0, sigma: float = 1.0) -> float:
        """Retorna uma amostra de distribuição normal Gaussiana."""
        return self._rng.gauss(mu, sigma)

    def get_state(self) -> Tuple[Any, ...]:
        """Obtém o estado interno completo da RNG para serialização/snapshots."""
        return self._rng.getstate()

    def set_state(self, state: Any) -> None:
        """Restaura o estado interno completo da RNG, convertendo listas JSON em tuplas se necessário."""
        if isinstance(state, (list, tuple)):
            if len(state) >= 3 and isinstance(state[1], list):
                state = (state[0], tuple(state[1]), state[2])
            elif isinstance(state, list):
                state = tuple(state)
        self._rng.setstate(state)
