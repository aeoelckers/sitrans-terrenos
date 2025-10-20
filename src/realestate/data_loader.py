"""Utilidades para cargar inventarios de terrenos desde archivos JSON."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


MACROZONE_BY_REGION = {
    "Arica y Parinacota": "Norte Grande",
    "Tarapacá": "Norte Grande",
    "Antofagasta": "Norte Grande",
    "Atacama": "Norte Chico",
    "Coquimbo": "Norte Chico",
    "Valparaíso": "Zona Centro",
    "Metropolitana de Santiago": "Zona Centro",
    "Libertador General Bernardo O'Higgins": "Zona Centro",
    "Libertador General Bernardo O’Higgins": "Zona Centro",
    "O'Higgins": "Zona Centro",
    "O’Higgins": "Zona Centro",
    "Maule": "Zona Centro-Sur",
    "Ñuble": "Zona Sur",
    "Nuble": "Zona Sur",
    "Biobío": "Zona Sur",
    "Biobio": "Zona Sur",
    "La Araucanía": "Zona Sur",
    "Los Ríos": "Zona Sur",
    "Los Lagos": "Zona Austral",
    "Aysén del General Carlos Ibáñez del Campo": "Zona Austral",
    "Aysen del General Carlos Ibanez del Campo": "Zona Austral",
    "Magallanes y de la Antártica Chilena": "Zona Austral",
}


@dataclass(frozen=True)
class Listing:
    """Representa un terreno disponible dentro de Chile."""

    id: str
    name: str
    region: str
    province: str
    commune: str
    locality: str
    property_type: str
    area_m2: float
    price_per_m2: float
    zoning: str
    services: Sequence[str]
    transport: dict
    topography: str
    notes: str = ""
    url: str = ""

    @property
    def total_price(self) -> float:
        """Calcula el precio total del terreno."""

        return self.area_m2 * self.price_per_m2

    @property
    def macrozone(self) -> str:
        """Obtiene la macrozona chilena asociada a la región del terreno."""

        return MACROZONE_BY_REGION.get(self.region, "Zona Desconocida")


def load_listings(path: Path | str) -> List[Listing]:
    """Carga un conjunto de terrenos desde un archivo JSON."""

    raw_path = Path(path)
    with raw_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    listings: List[Listing] = []
    for item in data:
        listings.append(Listing(**item))
    return listings


def listings_from_iterable(rows: Iterable[dict]) -> List[Listing]:
    """Construye listados a partir de una iteración de diccionarios."""

    return [Listing(**row) for row in rows]
