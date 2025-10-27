# Agente de búsqueda de terrenos

Este repositorio contiene un agente sencillo en Python para filtrar y priorizar 
terrenos orientados a proyectos industriales, habitacionales o energéticos.
Utiliza un inventario en formato JSON y un archivo de criterios para evaluar
las opciones más atractivas.

## Estructura del proyecto

```
.
├── config/
│   └── industrial_criteria.json    # Ejemplo de criterios de búsqueda
├── data/
│   └── sample_listings.json        # Inventario de terrenos de muestra
├── docs/
│   ├── index.html                  # Interfaz web estática compatible con GitHub Pages
│   ├── app.js                      # Lógica del buscador en el navegador
│   └── styles.css                  # Estilos de la aplicación
├── src/
│   ├── main.py                     # CLI del agente
│   └── realestate/                 # Librería reutilizable
│       ├── __init__.py
│       ├── agent.py
│       └── data_loader.py
└── README.md
```

## Usa el buscador sin instalar nada (solo navegador)

Si no cuentas con Python, puedes usar íntegramente la versión web incluida en la
carpeta `docs/`. Hay dos formas sencillas de hacerlo:

### Opción A: abrir la página directamente desde tu equipo

1. Descarga este repositorio como ZIP desde GitHub (botón verde **Code →
   Download ZIP**) y descomprímelo.
2. Dentro de la carpeta extraída abre `docs/index.html` con tu navegador
   favorito. El explorador mostrará la interfaz del buscador usando el inventario
   de ejemplo (`docs/data/listings.json`).
3. Ajusta los filtros o carga tu propio archivo JSON con el botón **Selecciona un
   archivo JSON local**. Toda la lógica corre en el navegador, por lo que no
   necesitas servidores ni software adicional.

> ℹ️ En algunos navegadores (como Chrome) puede que abrir archivos `file://`
> impida cargar el JSON por seguridad. Si te ocurre, usa la opción B o cualquier
> servicio gratuito para publicar archivos estáticos (Netlify, Vercel, etc.).

### Opción B: publicarlo en GitHub Pages paso a paso

1. **Copia el repositorio a tu cuenta**
   - Ve a [github.com/new](https://github.com/new) y crea un repositorio vacío (por
     ejemplo `sitrans-terrenos`).
   - Regresa a este proyecto, pulsa el botón verde **Code → Download ZIP** y
     descomprime el archivo en tu computador.
   - Arrastra la carpeta completa (`config/`, `data/`, `docs/`, etc.) a la página
     de tu repositorio recién creado usando **Add file → Upload files** y confirma
     con **Commit changes**. No necesitas usar la terminal.
2. **Activa la publicación**
   - En el repositorio subido, abre la pestaña **Settings** y elige **Pages** en
     el menú lateral.
   - En **Source**, selecciona *Deploy from a branch*.
   - En el selector **Branch**, elige `main` (o la rama donde subiste los
     archivos) y en la lista de carpetas define `/docs`. Guarda con **Save**.
   - GitHub mostrará un mensaje indicando que está generando el sitio. Cuando el
     proceso termine aparecerá un enlace con el formato
     `https://tu-usuario.github.io/sitrans-terrenos/`.
3. **Usa la aplicación desde cualquier dispositivo**
   - Visita la URL publicada desde tu celular, tablet o computador. Podrás filtrar
     terrenos inmediatamente.
   - Si deseas reemplazar el inventario por uno propio, modifica
     `docs/data/listings.json` desde la interfaz web de GitHub (**Add file → Edit
     file**), guarda los cambios y repite el proceso de publicación.
   - Para probar inventarios externos sin hacer commits, añade el parámetro
     `?data=` en la URL con la dirección de tu JSON público o utiliza el botón
     para cargar un archivo local.

## Requisitos

- Python 3.10 o superior (solo si quieres ejecutar la versión CLI o el servidor
  local opcional; la versión web no requiere instalación).

## Uso rápido (modo CLI con Python)

1. Crear un entorno virtual (opcional):

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

2. Ejecutar el agente con los archivos de ejemplo:

   ```bash
   python -m src.main
   ```

   El comando imprimirá un ranking con los mejores terrenos, su puntuación y
   los elementos que cumplen de los criterios cargados.

3. Levantar la interfaz web opcional (solo usa la biblioteca estándar):

   ```bash
   python -m src.web
   ```

   Mantén la terminal abierta. Cuando el servidor se inicie verás un mensaje con
   las direcciones disponibles, por ejemplo:

   ```
   Servidor web iniciado. Accede desde:
     - http://127.0.0.1:8000
     - http://192.168.0.15:8000
   Presiona Ctrl+C para detenerlo
   ```

   Abre la primera URL en el mismo computador o cualquiera de las direcciones
   locales para filtrar terrenos por región, comuna, tipo de predio,
   superficie mínima en m² o hectáreas, precios máximos y servicios requeridos.
   Los resultados muestran enlaces directos a las publicaciones configuradas en
   el inventario.

   - **Acceso desde otros dispositivos (computador o celular):** asegúrate de
     que el equipo donde ejecutas el comando y tu celular estén conectados a la
     misma red Wi-Fi o cableada. Usa alguna de las URL que imprime la consola
     (`http://192.168.x.x:8000`) en el navegador del dispositivo remoto. Si no
     puedes abrirlas, revisa el firewall del sistema operativo.
   - **Elegir host y puerto:** ejecuta `python -m src.web --host 0.0.0.0 --port
     9000` si necesitas publicar la app en un puerto distinto o escuchar solo en
     una interfaz específica.
   - **Inventario propio para la web:** pasa tu archivo JSON con `python -m
     src.web --listings data/mis_terrenos.json`. El servidor validará la ruta y
     mostrará un mensaje claro si no la encuentra.

### Ejecutar el buscador desde GitHub Pages

Si prefieres compartir el agente como una página estática (sin ejecutar Python
en el servidor) habilita GitHub Pages desde la pestaña **Settings → Pages** y
selecciona la carpeta `docs/` del branch principal. El flujo recomendado es:

1. Sube o reemplaza tu inventario en `docs/data/listings.json`. Puedes generar
   el archivo copiando el formato descrito en [Inventario de terrenos](#inventario-de-terrenos---listings).
2. Espera a que GitHub publique el sitio (puede tardar un par de minutos). El
   enlace tendrá la forma `https://tu-usuario.github.io/sitrans-terrenos/`.
3. Abre la URL desde cualquier dispositivo. La interfaz permite filtrar por
   región, comuna, tipo de predio, superficie mínima (m² o hectáreas),
   servicios obligatorios o preferidos y precios máximos.
4. Para probar otro inventario sin volver a desplegar, añade el parámetro
   `?data=` en la URL apuntando a tu JSON público, por ejemplo:
   `https://tu-usuario.github.io/sitrans-terrenos/?data=https://midominio.cl/listados.json`.
   También puedes cargar un archivo JSON directamente desde tu computador con
   el botón **Selecciona un archivo JSON local**; el archivo se procesa en el
   navegador y no se sube a Internet.

#### Activar GitHub Pages paso a paso

1. Ingresa a tu repositorio en GitHub desde un navegador de escritorio o
   móvil y pulsa la pestaña **Settings** situada en la parte superior (a la
   derecha de *Insights*).
2. En la barra lateral izquierda desplázate hasta la sección **Code and
   automation** y selecciona **Pages**.
3. Dentro del apartado **Build and deployment** ubica la opción **Source** y
   elige **Deploy from a branch**. Al hacerlo aparecerán dos selectores
   adicionales.
4. En el selector **Branch** escoge tu rama principal (`main`, `master` u otra
   que contenga la carpeta `docs/`). A su derecha, cambia el directorio a
   `/docs`. Presiona **Save** para guardar los cambios.
5. GitHub iniciará una publicación automática. Puedes seguir su progreso desde
   la pestaña **Actions** o revisando la notificación verde que aparece en la
   parte superior de **Pages**. Cuando finalice, la misma sección mostrará el
   enlace público definitivo.
6. Copia la URL publicada (por ejemplo,
   `https://tu-usuario.github.io/sitrans-terrenos/`) y ábrela desde tu
   computador o teléfono. Desde esa página podrás subir capturas o compartir el
   enlace mientras ajustas los filtros.

> 💡 El mismo contenido de `docs/` funciona en cualquier hosting estático o CDN.
> Basta con subir los archivos tal como están.

4. Consultar la ayuda de la interfaz de línea de comandos:

   ```bash
   python -m src.main --help
   ```

   Opciones principales:

   - `--listings`: ruta al archivo JSON con los terrenos.
   - `--criteria`: archivo JSON con los criterios de búsqueda.
   - `--top`: cantidad de terrenos a mostrar (por defecto 5).

5. Personalizar los criterios copiando el archivo `config/industrial_criteria.json`
   y ajustando los parámetros disponibles para Chile:

   - `preferred_regions`, `preferred_communes` y (opcional) `preferred_macrozones` para acotar la búsqueda geográfica.
   - `target_zonings`: usos de suelo válidos (industrial, agroindustrial, turístico, etc.).
   - `min_area_m2` o `min_area_hectares`, junto con `max_total_price` y `max_price_per_m2`.
   - `desired_property_types` para priorizar terrenos, lotes, sitios o parcelas.
   - `required_services` y `preferred_services` (electricidad, agua potable, gas natural, fibra óptica, etc.).
   - `transport_importance`: ponderaciones entre conectividad carretera/ferrocarril/aeropuerto.

6. Indicar archivos personalizados mediante la CLI:

   ```bash
   python -m src.main --listings data/mis_terrenos.json --criteria config/mis_criterios.json
   ```

## Formato de los archivos JSON

### Inventario de terrenos (`--listings`)

Cada terreno debe incluir al menos los siguientes campos:

```json
{
  "id": "CL-T-001",
  "name": "Parque Industrial La Negra",
  "region": "Antofagasta",
  "province": "Antofagasta",
  "commune": "Antofagasta",
  "locality": "La Negra",
  "property_type": "terreno",
  "area_m2": 35000,
  "price_per_m2": 190000,
  "zoning": "industrial",
  "services": ["electricidad", "agua potable", "gas natural"],
  "transport": {
    "carretera": "Ruta 5",
    "distancia_km": 0.8,
    "ferrocarril": true
  },
  "notes": "Terreno consolidado con acceso directo a Ruta 5",
  "url": "https://tuportal.cl/publicacion/CL-T-001"
}
```

Puedes generar tu archivo con una lista de objetos como el anterior. El cargador
espera al menos los campos mostrados (id, nombre, región, comuna, tipo de
propiedad, superficie, precio por m², servicios, transporte y la URL de la
publicación). Los campos
adicionales se ignorarán automáticamente.

### Criterios de búsqueda (`--criteria`)

El archivo JSON define los parámetros mínimos y deseados para filtrar y
ponderar los terrenos. Los campos opcionales pueden omitirse si no aplican a tu
caso.

```json
{
  "preferred_macrozones": ["Zona Centro"],
  "preferred_regions": ["Metropolitana de Santiago"],
  "preferred_communes": ["Pudahuel"],
  "target_zonings": ["industrial", "industrial mixto"],
  "min_area_hectares": 2.0,
  "max_total_price": 2500000000,
  "max_price_per_m2": 240000,
  "desired_property_types": ["terreno", "lote"],
  "required_services": ["electricidad", "agua potable"],
  "preferred_services": ["gas natural", "fibra óptica"],
  "transport_importance": {
    "carretera": 0.5,
    "ferrocarril": 0.3,
    "aeropuerto": 0.2
  }
}
```

## Uso como librería

Si quieres integrar el agente en otro proyecto Python puedes reutilizar las
clases del paquete `realestate`:

```python
from pathlib import Path

from src.realestate import RealEstateSearchAgent, SearchCriteria, load_listings

listings = load_listings(Path("data/sample_listings.json"))
criteria = SearchCriteria.from_dict({"min_area_m2": 10000})

agent = RealEstateSearchAgent(listings)
results = agent.search(criteria, top_n=3)

for result in results:
    print(result.listing.name, result.score)
```

El método `search` devuelve una lista de `SearchResult` con la información del
terreno y los indicadores relevantes para presentar al usuario.

## Extensiones sugeridas

- Integrar fuentes de datos reales (APIs o scrapers) y cargar los registros con
  `realestate.data_loader.listings_from_iterable`.
- Añadir nuevas métricas de evaluación (impacto ambiental, cercanía a puertos,
  disponibilidad de incentivos fiscales, etc.).
- Construir un front-end o chatbot que consuma la librería `realestate` para
  ofrecer recomendaciones interactivas.
