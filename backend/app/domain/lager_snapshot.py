"""Bibliotheksunabhängige Beobachtung der SPS-Lagerstände."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class GehaeuseBestand:
    """Füllstand des Gehäuselagers nach Farbe."""

    gesamt: int
    rot: int
    silber: int
    schwarz: int


@dataclass(frozen=True)
class ProduktBestand:
    """Füllstand des Hochregallagers nach Produkt und Farbe."""

    gesamt: int
    salz_rot: int
    salz_silber: int
    salz_schwarz: int
    pfeffer_rot: int
    pfeffer_silber: int
    pfeffer_schwarz: int


@dataclass(frozen=True)
class LagerSnapshot:
    """Konsistent gelesener Füllstand aller vier SPS-Lagerknoten."""

    gehaeuse: GehaeuseBestand
    deckel_blau: int
    deckel_gruen: int
    produkte: ProduktBestand
    observed_at: datetime
