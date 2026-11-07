"""Gemeinsame Fixtures: die Handinstanz aus den Stücken 1 bis 4, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rsk_scenario import Instance  # noqa: E402

(S2, S18, S20, S29, S37, S53, S72, S74) = (math.sqrt(v) for v in (2, 18, 20, 29, 37, 53, 72, 74))


@pytest.fixture
def hand():
    """Planinstanz aus den Stücken 1 bis 4: Depot (0,0); Kunden 1 (6,-6), 2 (-2,5), 3 (-4,-4), 4 (0,-7), 5 (-1,-1), 6 (-6,3); Nachfragen 3, 2, 2, 4, 2, 1; Kapazität 7.

    Von Hand (Wurzeln): Optimum = Route (1 4) + Route (2 6 3 5) = (sqrt72 + sqrt37 + 7) + (sqrt29 + sqrt20 + sqrt53 + sqrt18 + sqrt2) = 44,3623."""
    return Instance(((0.0, 0.0), (6.0, -6.0), (-2.0, 5.0), (-4.0, -4.0), (0.0, -7.0), (-1.0, -1.0), (-6.0, 3.0)), (3, 2, 2, 4, 2, 1), 7)


@pytest.fixture
def square():
    """Vier Kunden auf den Ecken eines Quadrats um das Depot: 1 (1,1), 2 (1,-1), 3 (-1,-1), 4 (-1,1); Nachfrage je 1, Kapazität 10. Die Route (1 3 2 4) kreuzt sich: Länge 6 sqrt2 + 2 = 10,4853;
    die Umkehr des Stücks (3 2) ergibt (1 2 3 4), das Quadrat: 6 + 2 sqrt2 = 8,8284."""
    return Instance(((0.0, 0.0), (1.0, 1.0), (1.0, -1.0), (-1.0, -1.0), (-1.0, 1.0)), (1, 1, 1, 1), 10)


OPTIMUM = (S72 + S37 + 7) + (S29 + S20 + S53 + S18 + S2)
