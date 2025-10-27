"""Servidor web mínimo para ejecutar el agente inmobiliario."""

from __future__ import annotations

import argparse
import html
import socket
from pathlib import Path
from typing import Iterable, Tuple
from urllib.parse import parse_qs
from wsgiref.simple_server import make_server

from .realestate import RealEstateSearchAgent, SearchCriteria, load_listings

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_LISTINGS_PATH = BASE_DIR / "data" / "sample_listings.json"


def _initialize_agent(listings_path: Path | None = None) -> Tuple[
    RealEstateSearchAgent, list[str], list[str], list[str]
]:
    """Crea el agente y catálogos auxiliares."""

    target_path = (listings_path or DEFAULT_LISTINGS_PATH).expanduser().resolve()
    listings = load_listings(target_path)
    agent = RealEstateSearchAgent(listings)
    macrozones = sorted({listing.macrozone for listing in listings})
    regions = sorted({listing.region for listing in listings})
    property_types = sorted({listing.property_type for listing in listings})
    return agent, macrozones, regions, property_types


AGENT, MACROZONES, REGIONS, PROPERTY_TYPES = _initialize_agent()


def _parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    value = value.strip()
    if not value:
        return None
    normalized = (
        value.replace("\u00a0", "")
        .replace(" ", "")
        .replace(".", "")
        .replace(",", ".")
    )
    if normalized.count(".") > 1:
        # si todavía hay múltiples separadores, preferimos el original para evitar ValueError
        normalized = normalized.replace(".", "", normalized.count(".") - 1)
    try:
        return float(normalized)
    except ValueError:
        return None


def _split_csv(raw: str | None) -> list[str]:
    if not raw:
        return []
    parts = raw.replace(";", ",").split(",")
    return [segment.strip() for segment in parts if segment.strip()]


def _build_criteria(params: dict[str, list[str]]) -> SearchCriteria:
    kwargs: dict[str, object] = {}

    macrozona = params.get("macrozona", [""])[0].strip()
    if macrozona:
        kwargs["preferred_macrozones"] = [macrozona]

    region = params.get("region", [""])[0].strip()
    if region:
        kwargs["preferred_regions"] = [region]

    property_type = params.get("property_type", [""])[0].strip()
    if property_type:
        kwargs["desired_property_types"] = [property_type]

    min_area = _parse_float(params.get("min_area", [""])[0])
    area_unit = params.get("area_unit", ["m2"])[0]
    if min_area is not None and min_area > 0:
        if area_unit == "ha":
            kwargs["min_area_hectares"] = min_area
        else:
            kwargs["min_area_m2"] = min_area

    required_services = _split_csv(params.get("required_services", [""])[0])
    if required_services:
        kwargs["required_services"] = required_services

    preferred_services = _split_csv(params.get("preferred_services", [""])[0])
    if preferred_services:
        kwargs["preferred_services"] = preferred_services

    max_price = _parse_float(params.get("max_price", [""])[0])
    if max_price is not None and max_price > 0:
        kwargs["max_total_price"] = max_price

    max_price_m2 = _parse_float(params.get("max_price_m2", [""])[0])
    if max_price_m2 is not None and max_price_m2 > 0:
        kwargs["max_price_per_m2"] = max_price_m2

    return SearchCriteria(**kwargs)


def _format_currency(value: float) -> str:
    return f"$ {value:,.0f}".replace(",", ".")


def _render_options(values: Iterable[str], selected: str) -> str:
    options = ["<option value=''>Todas</option>"]
    for value in values:
        safe_value = html.escape(value)
        if value == selected:
            options.append(f"<option value=\"{safe_value}\" selected>{safe_value}</option>")
        else:
            options.append(f"<option value=\"{safe_value}\">{safe_value}</option>")
    return "\n".join(options)


def _render_results(results) -> str:
    if not results:
        return "<p>No se encontraron terrenos que cumplan los criterios.</p>"

    rows: list[str] = []
    for result in results:
        listing = result.listing
        highlights = result.highlights
        url = listing.url.strip()
        if url:
            link = f'<a href="{html.escape(url)}" target="_blank" rel="noopener">Ver publicación</a>'
        else:
            link = "<span>Sin enlace</span>"
        rows.append(
            """
            <tr>
                <td><strong>{name}</strong><br><small>{commune}, {region}</small></td>
                <td>{area_m2:.0f} m²<br>{area_ha:.2f} ha</td>
                <td>{total} CLP<br><small>{per_m2} CLP/m²</small></td>
                <td>{score:.3f}</td>
                <td>{link}</td>
            </tr>
            """.format(
                name=html.escape(listing.name),
                commune=html.escape(listing.commune),
                region=html.escape(listing.region),
                area_m2=highlights.get("area_m2", listing.area_m2),
                area_ha=highlights.get("area_ha", listing.area_m2 / 10_000),
                total=html.escape(_format_currency(highlights.get("precio_total_clp", listing.total_price))),
                per_m2=html.escape(_format_currency(highlights.get("precio_m2_clp", listing.price_per_m2))),
                score=result.score,
                link=link,
            )
        )

    return (
        "<table class=\"results\">"
        "<thead><tr><th>Terreno</th><th>Superficie</th><th>Precio</th><th>Score</th><th>Publicación</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
    )


def _render_page(params: dict[str, list[str]], results_html: str, top: int) -> str:
    selected_macrozona = params.get("macrozona", [""])[0]
    selected_region = params.get("region", [""])[0]
    selected_property = params.get("property_type", [""])[0]
    min_area_value = params.get("min_area", [""])[0]
    area_unit = params.get("area_unit", ["m2"])[0]
    required_services = params.get("required_services", [""])[0]
    preferred_services = params.get("preferred_services", [""])[0]
    max_price = params.get("max_price", [""])[0]
    max_price_m2 = params.get("max_price_m2", [""])[0]
    top_value = params.get("top", [str(top)])[0]

    return f"""
    <!DOCTYPE html>
    <html lang=\"es\">
    <head>
        <meta charset=\"utf-8\">
        <title>Buscador de Terrenos</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 2rem; background: #f5f6f8; }}
            h1 {{ color: #243447; }}
            form {{ background: #fff; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 6px rgba(0,0,0,0.08); margin-bottom: 2rem; }}
            fieldset {{ border: none; padding: 0; margin: 0 0 1rem 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; }}
            label {{ display: flex; flex-direction: column; font-weight: 600; color: #33475b; font-size: 0.9rem; }}
            input, select {{ margin-top: 0.4rem; padding: 0.5rem; border: 1px solid #cbd6e2; border-radius: 4px; font-size: 0.95rem; }}
            button {{ background: #2b7cff; color: #fff; border: none; padding: 0.75rem 1.5rem; border-radius: 4px; font-size: 1rem; cursor: pointer; }}
            button:hover {{ background: #1f5fd6; }}
            table.results {{ width: 100%; border-collapse: collapse; background: #fff; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-radius: 8px; overflow: hidden; }}
            table.results th, table.results td {{ padding: 0.9rem; border-bottom: 1px solid #e6ecf1; text-align: left; }}
            table.results th {{ background: #f0f4f8; color: #243447; }}
            table.results tr:last-child td {{ border-bottom: none; }}
            @media (max-width: 768px) {{ fieldset {{ grid-template-columns: 1fr; }} }}
        </style>
    </head>
    <body>
        <h1>Buscador de terrenos en Chile</h1>
        <form method=\"get\">
            <fieldset>
                <label>Macrozona
                    <select name=\"macrozona\">
                        {_render_options(MACROZONES, selected_macrozona)}
                    </select>
                </label>
                <label>Región
                    <select name=\"region\">
                        {_render_options(REGIONS, selected_region)}
                    </select>
                </label>
                <label>Tipo de propiedad
                    <select name=\"property_type\">
                        {_render_options(PROPERTY_TYPES, selected_property)}
                    </select>
                </label>
                <label>Superficie mínima
                    <div style=\"display:flex; gap:0.5rem;\">
                        <input type=\"number\" step=\"any\" min=\"0\" name=\"min_area\" value=\"{html.escape(min_area_value)}\" placeholder=\"Ej: 3\">
                        <select name=\"area_unit\">
                            <option value=\"m2\" {'selected' if area_unit == 'm2' else ''}>m²</option>
                            <option value=\"ha\" {'selected' if area_unit == 'ha' else ''}>hectáreas</option>
                        </select>
                    </div>
                </label>
                <label>Servicios requeridos
                    <input type=\"text\" name=\"required_services\" value=\"{html.escape(required_services)}\" placeholder=\"Ej: electricidad, agua potable\">
                </label>
                <label>Servicios preferidos
                    <input type=\"text\" name=\"preferred_services\" value=\"{html.escape(preferred_services)}\" placeholder=\"Ej: gas natural\">
                </label>
                <label>Precio total máximo (CLP)
                    <input type=\"number\" step=\"any\" min=\"0\" name=\"max_price\" value=\"{html.escape(max_price)}\">
                </label>
                <label>Precio máximo por m² (CLP)
                    <input type=\"number\" step=\"any\" min=\"0\" name=\"max_price_m2\" value=\"{html.escape(max_price_m2)}\">
                </label>
                <label>Cantidad de resultados
                    <input type=\"number\" step=\"1\" min=\"1\" name=\"top\" value=\"{html.escape(top_value)}\">
                </label>
            </fieldset>
            <button type=\"submit\">Buscar terrenos</button>
        </form>
        {results_html}
    </body>
    </html>
    """


def application(environ, start_response):
    params = parse_qs(environ.get("QUERY_STRING", ""))
    top_param = params.get("top", ["5"])[0]
    try:
        top = max(1, int(top_param))
    except ValueError:
        top = 5

    criteria = _build_criteria(params) if params else SearchCriteria()
    results = AGENT.search(criteria, top_n=top)

    results_html = _render_results(results)
    page = _render_page(params, results_html, top)
    body = page.encode("utf-8")

    start_response(
        "200 OK",
        [
            ("Content-Type", "text/html; charset=utf-8"),
            ("Content-Length", str(len(body))),
        ],
    )
    return [body]


def _discover_local_urls(host: str, port: int) -> list[str]:
    urls = set()

    if host not in {"0.0.0.0", "::"}:
        urls.add(f"http://{host}:{port}")
    else:
        urls.add(f"http://127.0.0.1:{port}")

    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, family=socket.AF_INET):
            ip = info[4][0]
            if not ip.startswith("127."):
                urls.add(f"http://{ip}:{port}")
    except OSError:
        pass

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
            if not ip.startswith("127."):
                urls.add(f"http://{ip}:{port}")
    except OSError:
        pass

    return sorted(urls)


def main(host: str = "0.0.0.0", port: int = 8000, listings_path: Path | None = None) -> None:
    global AGENT, MACROZONES, REGIONS, PROPERTY_TYPES

    try:
        AGENT, MACROZONES, REGIONS, PROPERTY_TYPES = _initialize_agent(listings_path)
    except FileNotFoundError as exc:
        print("No se pudo iniciar el servidor: archivo de terrenos no encontrado.")
        print(f"Ruta proporcionada: {exc.filename}")
        return
    except Exception as exc:  # pragma: no cover - reporte legible para CLI
        print("No se pudo cargar el inventario de terrenos:")
        print(f"  {exc}")
        return

    with make_server(host, port, application) as server:
        urls = _discover_local_urls(host, port)
        print("Servidor web iniciado. Accede desde:")
        for url in urls:
            print(f"  - {url}")
        print("Presiona Ctrl+C para detenerlo")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor detenido.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Servidor web del agente inmobiliario")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Dirección IP para escuchar (0.0.0.0 permite conexiones de la red local)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Puerto HTTP para exponer la aplicación",
    )
    parser.add_argument(
        "--listings",
        type=Path,
        default=DEFAULT_LISTINGS_PATH,
        help="Archivo JSON con el inventario de terrenos",
    )
    args = parser.parse_args()
    main(host=args.host, port=args.port, listings_path=args.listings)
