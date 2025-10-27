"""CLI para ejecutar el agente de búsqueda inmobiliaria."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .realestate import RealEstateSearchAgent, SearchCriteria, load_listings


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evalúa terrenos con base en criterios configurables"
    )
    parser.add_argument(
        "--listings",
        type=Path,
        default=Path("data/sample_listings.json"),
        help="Ruta al inventario de terrenos en formato JSON",
    )
    parser.add_argument(
        "--criteria",
        type=Path,
        default=Path("config/industrial_criteria.json"),
        help="Archivo JSON con los criterios de búsqueda",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Número de terrenos a mostrar ordenados por score",
    )
    return parser.parse_args()


def load_criteria(path: Path) -> SearchCriteria:
    with path.open("r", encoding="utf-8") as file:
        data: dict[str, Any] = json.load(file)
    return SearchCriteria.from_dict(data)


def format_result(result) -> str:
    listing = result.listing
    lines = [
        f"{listing.id} - {listing.name} ({listing.region}, {listing.commune})",
        f"  Score: {result.score:.3f}",
        f"  Localidad: {listing.locality}, {listing.province}",
        f"  Superficie: {result.highlights['area_m2']:.0f} m² ({result.highlights['area_ha']:.2f} ha)",
        f"  Precio total: ${result.highlights['precio_total_clp']:,.0f} CLP",
        f"  Precio/m²: ${result.highlights['precio_m2_clp']:,.0f} CLP",
        f"  Servicios clave: {', '.join(result.highlights['servicios_cubiertos']) or 'N/A'}",
        f"  Servicios preferidos: {', '.join(result.highlights['servicios_preferidos']) or 'N/A'}",
        f"  Transporte: {result.highlights['transporte']}",
        f"  Observaciones: {listing.notes}",
        f"  Publicación: {listing.url or 'N/D'}",
    ]
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    listings = load_listings(args.listings)
    criteria = load_criteria(args.criteria)

    agent = RealEstateSearchAgent(listings)
    results = agent.search(criteria, top_n=args.top)

    if not results:
        print("No se encontraron terrenos que cumplan con los criterios.")
        return

    print("Terrenos sugeridos:\n")
    for result in results:
        print(format_result(result))
        print("-" * 60)


if __name__ == "__main__":
    main()
