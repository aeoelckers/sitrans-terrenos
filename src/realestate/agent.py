"""Lógica del agente de búsqueda de terrenos."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, MutableMapping, Sequence

from .data_loader import Listing


@dataclass
class SearchCriteria:
    """Criterios configurables para evaluar terrenos."""

    preferred_regions: Sequence[str] = ()
    preferred_macrozones: Sequence[str] = ()
    target_zonings: Sequence[str] = ()
    min_area_m2: float = 0.0
    min_area_hectares: float = 0.0
    max_total_price: float | None = None
    max_price_per_m2: float | None = None
    required_services: Sequence[str] = ()
    preferred_services: Sequence[str] = ()
    transport_importance: Mapping[str, float] = field(default_factory=dict)
    desired_property_types: Sequence[str] = ()

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "SearchCriteria":
        """Crea criterios a partir de un diccionario (ej. JSON)."""

        kwargs = dict(data)
        return cls(**kwargs)

    @property
    def _area_threshold_m2(self) -> float:
        """Calcula el mínimo de superficie en m² a considerar."""

        min_m2 = max(self.min_area_m2, 0.0)
        if self.min_area_hectares:
            min_m2 = max(min_m2, self.min_area_hectares * 10_000)
        return min_m2

    def matches(self, listing: Listing) -> bool:
        """Valida si un terreno cumple los filtros mínimos."""

        if self.preferred_macrozones:
            macrozones = {zone.lower() for zone in self.preferred_macrozones}
            if listing.macrozone.lower() not in macrozones:
                return False
        if self.preferred_regions:
            regions = {region.lower() for region in self.preferred_regions}
            if listing.region.lower() not in regions:
                return False
        if self.desired_property_types:
            types = {ptype.lower() for ptype in self.desired_property_types}
            if listing.property_type.lower() not in types:
                return False
        if self.target_zonings:
            zonings = {zoning.lower() for zoning in self.target_zonings}
            if listing.zoning.lower() not in zonings:
                return False
        min_area = self._area_threshold_m2
        if listing.area_m2 < min_area:
            return False
        if self.max_total_price is not None and listing.total_price > self.max_total_price:
            return False
        if self.max_price_per_m2 is not None and listing.price_per_m2 > self.max_price_per_m2:
            return False
        services = set(service.lower() for service in listing.services)
        for service in self.required_services:
            if service.lower() not in services:
                return False
        return True


@dataclass
class SearchResult:
    """Resultado de evaluación de un terreno."""

    listing: Listing
    score: float
    breakdown: Mapping[str, float]
    highlights: Mapping[str, object]


class RealEstateSearchAgent:
    """Agente que filtra y prioriza terrenos según criterios."""

    def __init__(self, listings: Iterable[Listing]):
        self._listings = list(listings)

    def search(self, criteria: SearchCriteria, top_n: int = 5) -> List[SearchResult]:
        """Retorna los mejores terrenos ordenados por calificación."""

        results: List[SearchResult] = []
        for listing in self._listings:
            if not criteria.matches(listing):
                continue
            score, breakdown, highlights = self._score_listing(listing, criteria)
            results.append(SearchResult(listing, score, breakdown, highlights))

        results.sort(key=lambda result: result.score, reverse=True)
        return results[:top_n]

    def _score_listing(
        self, listing: Listing, criteria: SearchCriteria
    ) -> tuple[float, MutableMapping[str, float], MutableMapping[str, object]]:
        breakdown: MutableMapping[str, float] = {}
        highlights: MutableMapping[str, object] = {}
        score = 0.0

        # Ubicación
        highlights["region"] = listing.region
        highlights["macrozona"] = listing.macrozone

        if criteria.preferred_regions:
            if listing.region in criteria.preferred_regions:
                value = 1.0
                highlights["ubicacion"] = "Región preferida"
            else:
                value = 0.4
                highlights["ubicacion"] = "Región alternativa"
        elif criteria.preferred_macrozones:
            if listing.macrozone in criteria.preferred_macrozones:
                value = 0.9
                highlights["ubicacion"] = "Macrozona preferida"
            else:
                value = 0.5
                highlights["ubicacion"] = "Macrozona alternativa"
        else:
            value = 0.7
            highlights["ubicacion"] = "Sin preferencia"
        breakdown["ubicación"] = value * 0.25
        score += breakdown["ubicación"]

        # Servicios
        services = {service.lower() for service in listing.services}
        required = {service.lower() for service in criteria.required_services}
        preferred = {service.lower() for service in criteria.preferred_services}
        if required:
            coverage = len(required & services) / len(required)
        else:
            coverage = 1.0
        preferred_score = (len(preferred & services) / len(preferred)) if preferred else 0.5
        services_score = 0.4 * (0.6 * coverage + 0.4 * preferred_score)
        breakdown["servicios"] = services_score
        score += services_score
        highlights["servicios_cubiertos"] = sorted(required & services)
        highlights["servicios_preferidos"] = sorted(preferred & services)

        # Precio
        price_weight = 0.2
        if criteria.max_total_price:
            ratio = listing.total_price / criteria.max_total_price
            price_component = max(0.0, 1.0 - min(ratio, 1.5))
        else:
            price_component = 0.6
        if criteria.max_price_per_m2:
            ratio_m2 = listing.price_per_m2 / criteria.max_price_per_m2
            price_component = (price_component + max(0.0, 1.0 - min(ratio_m2, 1.5))) / 2
        breakdown["precio"] = price_component * price_weight
        score += breakdown["precio"]
        highlights["precio_total_clp"] = round(listing.total_price, 2)
        highlights["precio_m2_clp"] = listing.price_per_m2

        # Transporte y conectividad
        transport_score = self._transport_score(listing, criteria.transport_importance)
        breakdown["conectividad"] = transport_score * 0.15
        score += breakdown["conectividad"]
        highlights["transporte"] = listing.transport

        # Superficie
        area_ratio = listing.area_m2 / max(criteria._area_threshold_m2, 1)
        area_score = min(area_ratio / 4, 1.0)  # saturación si supera 4x el mínimo
        breakdown["superficie"] = area_score * 0.2
        score += breakdown["superficie"]
        highlights["area_m2"] = listing.area_m2
        highlights["area_ha"] = listing.area_m2 / 10_000

        return score, breakdown, highlights

    @staticmethod
    def _transport_score(
        listing: Listing, importance: Mapping[str, float]
    ) -> float:
        if not importance:
            return 0.6

        normalized: Dict[str, float] = {}
        total = float(sum(importance.values())) or 1.0
        for key, value in importance.items():
            normalized[key] = value / total

        score = 0.0
        data = listing.transport
        for mode, weight in normalized.items():
            availability = RealEstateSearchAgent._mode_availability(mode, data)
            score += weight * availability
        return score

    @staticmethod
    def _mode_availability(mode: str, data: Mapping[str, object]) -> float:
        mode = mode.lower()
        if mode == "carretera":
            distance = data.get("distancia_km")
            if isinstance(distance, (int, float)):
                return max(0.0, 1.0 - min(distance / 10.0, 1.0))
            return 0.7 if "carretera" in data else 0.0
        if mode == "ferrocarril":
            value = data.get("ferrocarril")
            if isinstance(value, bool):
                return 1.0 if value else 0.0
            return 0.5 if value else 0.0
        if mode == "aeropuerto":
            distance = data.get("aeropuerto_km")
            if isinstance(distance, (int, float)):
                return max(0.0, 1.0 - min(distance / 50.0, 1.0))
            return 0.0
        return 0.5 if data.get(mode) else 0.0
