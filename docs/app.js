const DATA_URL_PARAM = 'data';
const DEFAULT_DATA_URL = 'data/listings.json';

const MACROZONE_BY_REGION = {
  "Arica y Parinacota": "Norte Grande",
  "Tarapacá": "Norte Grande",
  "Tarapaca": "Norte Grande",
  "Antofagasta": "Norte Grande",
  "Atacama": "Norte Chico",
  "Coquimbo": "Norte Chico",
  "Valparaíso": "Zona Centro",
  "Valparaiso": "Zona Centro",
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
  "La Araucania": "Zona Sur",
  "Los Ríos": "Zona Sur",
  "Los Rios": "Zona Sur",
  "Los Lagos": "Zona Austral",
  "Aysén del General Carlos Ibáñez del Campo": "Zona Austral",
  "Aysen del General Carlos Ibanez del Campo": "Zona Austral",
  "Magallanes y de la Antártica Chilena": "Zona Austral",
  "Magallanes y de la Antartica Chilena": "Zona Austral"
};

let listings = [];
let searchForm = null;
let statusElement = null;
let resultsContainer = null;
let sourceIndicator = null;
let communesByRegion = new Map();
let allCommunes = new Set();

function getDataUrl() {
  const params = new URLSearchParams(window.location.search);
  const custom = params.get(DATA_URL_PARAM);
  if (custom) {
    return custom;
  }
  return DEFAULT_DATA_URL;
}

function normalize(value) {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace('ñ', 'n')
    .replace('Ñ', 'N');
}

function getMacrozone(region) {
  if (!region) return 'Zona Desconocida';
  return (
    MACROZONE_BY_REGION[region] ||
    MACROZONE_BY_REGION[normalize(region)] ||
    'Zona Desconocida'
  );
}

function toStringOrEmpty(value, fallback = '') {
  if (typeof value === 'string') return value;
  if (value === null || value === undefined) return fallback;
  return String(value);
}

function ensureArrayOfStrings(value) {
  if (!Array.isArray(value)) return [];
  return value
    .map((item) => toStringOrEmpty(item).trim())
    .filter(Boolean);
}

function normalizeListing(item, index) {
  if (typeof item !== 'object' || item === null || Array.isArray(item)) {
    throw new Error(`El elemento ${index + 1} no es un objeto válido.`);
  }

  const required = [
    'id',
    'name',
    'region',
    'commune',
    'property_type',
    'area_m2',
    'price_per_m2'
  ];

  for (const key of required) {
    if (!(key in item)) {
      throw new Error(`Falta el campo obligatorio "${key}" en el terreno ${index + 1}.`);
    }
  }

  const area = Number(item.area_m2);
  const price = Number(item.price_per_m2);
  if (!Number.isFinite(area) || area <= 0) {
    throw new Error(`El terreno ${index + 1} tiene una superficie inválida.`);
  }
  if (!Number.isFinite(price) || price < 0) {
    throw new Error(`El terreno ${index + 1} tiene un precio por m² inválido.`);
  }

  const services = ensureArrayOfStrings(item.services);
  const transport =
    item.transport && typeof item.transport === 'object' && !Array.isArray(item.transport)
      ? item.transport
      : {};

  let url = toStringOrEmpty(item.url).trim();
  if (url && !/^https?:\/\//i.test(url)) {
    url = `https://${url.replace(/^\/+/, '')}`;
  }

  const listing = {
    id: toStringOrEmpty(item.id),
    name: toStringOrEmpty(item.name),
    region: toStringOrEmpty(item.region),
    province: toStringOrEmpty(item.province),
    commune: toStringOrEmpty(item.commune),
    locality: toStringOrEmpty(item.locality),
    property_type: toStringOrEmpty(item.property_type),
    area_m2: area,
    price_per_m2: price,
    zoning: toStringOrEmpty(item.zoning),
    services,
    transport,
    topography: toStringOrEmpty(item.topography),
    notes: toStringOrEmpty(item.notes),
    url
  };

  return {
    ...listing,
    macrozone: getMacrozone(listing.region),
    total_price: listing.area_m2 * listing.price_per_m2
  };
}

function prepareListings(data) {
  if (!Array.isArray(data)) {
    throw new Error('El archivo JSON debe contener una lista de terrenos.');
  }
  return data.map((item, index) => normalizeListing(item, index));
}

function buildGeographyLookups() {
  communesByRegion = new Map();
  allCommunes = new Set();
  listings.forEach((item) => {
    if (item.region) {
      if (!communesByRegion.has(item.region)) {
        communesByRegion.set(item.region, new Set());
      }
      if (item.commune) {
        communesByRegion.get(item.region).add(item.commune);
      }
    }
    if (item.commune) {
      allCommunes.add(item.commune);
    }
  });
}

function updateSourceIndicator(label, href, isLocal) {
  if (!sourceIndicator) return;
  sourceIndicator.textContent = label;
  if (href) {
    sourceIndicator.setAttribute('href', href);
    sourceIndicator.removeAttribute('aria-disabled');
    sourceIndicator.classList.remove('is-local');
  } else {
    sourceIndicator.removeAttribute('href');
    sourceIndicator.setAttribute('aria-disabled', 'true');
    sourceIndicator.classList.add('is-local');
  }
  if (isLocal) {
    sourceIndicator.dataset.source = 'local';
  } else {
    delete sourceIndicator.dataset.source;
  }
}

function displayMessage(message, type = 'info') {
  if (!statusElement) return;
  statusElement.textContent = message;
  statusElement.className = 'feedback';
  if (type === 'error') {
    statusElement.classList.add('feedback--error');
  } else if (type === 'success') {
    statusElement.classList.add('feedback--success');
  } else if (type === 'info') {
    statusElement.classList.add('feedback--info');
  }
}

function hydrateFilters() {
  if (!searchForm || !listings.length) return;

  const params = new URLSearchParams(window.location.search);

  const regionSelect = searchForm.querySelector('#region');
  const communeSelect = searchForm.querySelector('#commune');
  const typeSelect = searchForm.querySelector('#property_type');

  const regions = Array.from(new Set(listings.map((item) => item.region).filter(Boolean)))
    .sort((a, b) => a.localeCompare(b, 'es', { sensitivity: 'base' }));
  const propertyTypes = Array.from(
    new Set(listings.map((item) => item.property_type).filter(Boolean))
  ).sort((a, b) => a.localeCompare(b, 'es', { sensitivity: 'base' }));

  const regionValue = params.get('region') || (regionSelect ? regionSelect.value : '');
  const communeValue = params.get('commune') || (communeSelect ? communeSelect.value : '');
  const typeValue = params.get('property_type') || (typeSelect ? typeSelect.value : '');

  populateOptions(regionSelect, regions, regionValue);
  populateCommuneOptions(regionValue, communeValue);
  populateOptions(typeSelect, propertyTypes, typeValue);
}

function populateOptions(select, values, previousValue = '') {
  if (!select) return;
  select.innerHTML = '<option value="">Todas</option>';
  const sorted = Array.from(values).sort((a, b) =>
    a.localeCompare(b, 'es', { sensitivity: 'base' })
  );
  sorted.forEach((value) => {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = value;
    select.appendChild(option);
  });
  if (previousValue && values.includes(previousValue)) {
    select.value = previousValue;
  } else {
    select.value = '';
  }
}

function populateCommuneOptions(region, previousValue = '') {
  if (!searchForm) return;
  const communeSelect = searchForm.querySelector('#commune');
  if (!communeSelect) return;
  let communes = [];
  if (region && communesByRegion.has(region)) {
    communes = Array.from(communesByRegion.get(region));
  } else {
    communes = Array.from(allCommunes);
  }
  populateOptions(communeSelect, communes, previousValue);
}

function readCriteria(form) {
  const formData = new FormData(form);
  const criteria = {
    preferred_regions: readList(formData.get('region')),
    preferred_communes: readList(formData.get('commune')),
    desired_property_types: readList(formData.get('property_type')),
    min_area_m2: parseFloat(formData.get('min_area')) || 0,
    min_area_hectares: 0,
    max_total_price: parseFloat(formData.get('max_price')) || null,
    max_price_per_m2: parseFloat(formData.get('max_price_m2')) || null,
    required_services: readCsv(formData.get('required_services')),
    preferred_services: readCsv(formData.get('preferred_services')),
    top: parseInt(formData.get('top'), 10) || 5
  };

  const areaUnit = formData.get('area_unit') || 'm2';
  if (areaUnit === 'ha' && criteria.min_area_m2) {
    criteria.min_area_hectares = criteria.min_area_m2;
    criteria.min_area_m2 = 0;
  }
  return criteria;
}

function readList(value) {
  if (!value) return [];
  return [value];
}

function readCsv(value) {
  if (!value) return [];
  return value
    .split(/[,;]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function areaThreshold(criteria) {
  const minM2 = Math.max(criteria.min_area_m2 || 0, 0);
  if (criteria.min_area_hectares) {
    return Math.max(minM2, criteria.min_area_hectares * 10000);
  }
  return minM2;
}

function matches(listing, criteria) {
  if (criteria.preferred_regions.length) {
    const set = new Set(criteria.preferred_regions.map((value) => value.toLowerCase()));
    if (!set.has(listing.region.toLowerCase())) {
      return false;
    }
  }
  if (criteria.preferred_communes.length) {
    const set = new Set(criteria.preferred_communes.map((value) => value.toLowerCase()));
    if (!set.has(listing.commune.toLowerCase())) {
      return false;
    }
  }
  if (criteria.desired_property_types.length) {
    const set = new Set(criteria.desired_property_types.map((value) => value.toLowerCase()));
    if (!set.has(listing.property_type.toLowerCase())) {
      return false;
    }
  }
  const minArea = areaThreshold(criteria);
  if (minArea && listing.area_m2 < minArea) {
    return false;
  }
  if (criteria.max_total_price && listing.total_price > criteria.max_total_price) {
    return false;
  }
  if (criteria.max_price_per_m2 && listing.price_per_m2 > criteria.max_price_per_m2) {
    return false;
  }
  const services = new Set((listing.services || []).map((value) => value.toLowerCase()));
  for (const required of criteria.required_services) {
    if (!services.has(required.toLowerCase())) {
      return false;
    }
  }
  return true;
}

function scoreListing(listing, criteria) {
  let score = 0;
  const breakdown = {};
  const highlights = {
    area_m2: listing.area_m2,
    area_ha: listing.area_m2 / 10000,
    precio_total_clp: listing.total_price,
    precio_m2_clp: listing.price_per_m2,
    commune: listing.commune,
    region: listing.region,
    macrozona: listing.macrozone,
    transporte: listing.transport
  };

  // ubicación
  let ubicacionValue = 0.7;
  if (criteria.preferred_communes.length) {
    if (criteria.preferred_communes.includes(listing.commune)) {
      ubicacionValue = 1.0;
      highlights.ubicacion = 'Comuna preferida';
    } else {
      ubicacionValue = 0.3;
      highlights.ubicacion = 'Comuna alternativa';
    }
  } else if (criteria.preferred_regions.length) {
    if (criteria.preferred_regions.includes(listing.region)) {
      ubicacionValue = 1.0;
      highlights.ubicacion = 'Región preferida';
    } else {
      ubicacionValue = 0.4;
      highlights.ubicacion = 'Región alternativa';
    }
  } else {
    highlights.ubicacion = 'Sin preferencia';
  }
  breakdown['Ubicación'] = ubicacionValue * 0.25;
  score += breakdown['Ubicación'];

  // servicios
  const services = new Set((listing.services || []).map((value) => value.toLowerCase()));
  const required = new Set(criteria.required_services.map((value) => value.toLowerCase()));
  const preferred = new Set(criteria.preferred_services.map((value) => value.toLowerCase()));
  const covered = [...required].filter((value) => services.has(value));
  const preferredCovered = [...preferred].filter((value) => services.has(value));
  const coverage = required.size ? covered.length / required.size : 1;
  const preferredScore = preferred.size ? preferredCovered.length / preferred.size : 0.5;
  const servicesScore = 0.4 * (0.6 * coverage + 0.4 * preferredScore);
  breakdown['Servicios'] = servicesScore;
  score += servicesScore;
  highlights.servicios_cubiertos = covered;
  highlights.servicios_preferidos = preferredCovered;

  // precio
  let priceComponent = criteria.max_total_price
    ? Math.max(0, 1 - Math.min(listing.total_price / criteria.max_total_price, 1.5))
    : 0.6;
  if (criteria.max_price_per_m2) {
    const ratioM2 = listing.price_per_m2 / criteria.max_price_per_m2;
    priceComponent = (priceComponent + Math.max(0, 1 - Math.min(ratioM2, 1.5))) / 2;
  }
  breakdown['Precio'] = priceComponent * 0.2;
  score += breakdown['Precio'];

  // transporte
  const transportScore = transportAvailabilityScore(
    listing.transport || {},
    criteria.transport_importance || {}
  );
  breakdown['Conectividad'] = transportScore * 0.15;
  score += breakdown['Conectividad'];

  // superficie
  const ratio = listing.area_m2 / Math.max(areaThreshold(criteria) || 1, 1);
  const areaScore = Math.min(ratio / 4, 1);
  breakdown['Superficie'] = areaScore * 0.2;
  score += breakdown['Superficie'];

  return { score, breakdown, highlights };
}

function transportAvailabilityScore(data, importance) {
  const keys = Object.keys(importance || {});
  if (!keys.length) {
    return 0.6;
  }
  const total = keys.reduce((sum, key) => sum + (importance[key] || 0), 0) || 1;
  return keys.reduce((acc, key) => {
    const weight = (importance[key] || 0) / total;
    return acc + weight * modeAvailability(key, data);
  }, 0);
}

function modeAvailability(mode, data) {
  const normalized = mode.toLowerCase();
  if (normalized === 'carretera') {
    const distance = data?.distancia_km;
    if (typeof distance === 'number' && !Number.isNaN(distance)) {
      return Math.max(0, 1 - Math.min(distance / 10, 1));
    }
    return 'carretera' in data ? 0.7 : 0;
  }
  if (normalized === 'ferrocarril') {
    const value = data?.ferrocarril;
    if (typeof value === 'boolean') {
      return value ? 1 : 0;
    }
    return value ? 0.5 : 0;
  }
  if (normalized === 'aeropuerto') {
    const distance = data?.aeropuerto_km;
    if (typeof distance === 'number' && !Number.isNaN(distance)) {
      return Math.max(0, 1 - Math.min(distance / 50, 1));
    }
    return 0;
  }
  return data && data[normalized] ? 0.5 : 0;
}

function renderResults(results) {
  if (!resultsContainer) return;
  if (!results.length) {
    const message = listings.length
      ? 'No se encontraron terrenos que cumplan los criterios.'
      : 'Carga un inventario JSON para comenzar la búsqueda.';
    resultsContainer.innerHTML = `<p class="empty">${message}</p>`;
    return;
  }
  const table = document.createElement('table');
  table.className = 'results';
  table.innerHTML = `
    <thead>
      <tr>
        <th>Terreno</th>
        <th>Superficie</th>
        <th>Precio</th>
        <th>Score</th>
        <th>Publicación</th>
      </tr>
    </thead>
    <tbody>
      ${results
        .map(({ listing, score }) => {
          const areaHa = listing.area_m2 / 10000;
          const total = formatCurrency(listing.total_price);
          const priceM2 = formatCurrency(listing.price_per_m2);
          const link = listing.url
            ? `<a href="${listing.url}" target="_blank" rel="noopener">Ver publicación</a>`
            : '<span>Sin enlace</span>';
          return `
            <tr>
              <td><strong>${listing.name}</strong><br><small>${listing.commune}, ${listing.region}</small></td>
              <td>${listing.area_m2.toLocaleString('es-CL')} m²<br>${areaHa.toFixed(2)} ha</td>
              <td>${total} CLP<br><small>${priceM2} CLP/m²</small></td>
              <td>${score.toFixed(3)}</td>
              <td>${link}</td>
            </tr>
          `;
        })
        .join('')}
    </tbody>
  `;
  resultsContainer.innerHTML = '';
  resultsContainer.appendChild(table);
}

function formatCurrency(value) {
  return value
    .toLocaleString('es-CL', {
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    })
    .replace(/\./g, '.');
}

function performSearch() {
  if (!searchForm) return;
  if (!listings.length) {
    renderResults([]);
    return;
  }
  const criteria = readCriteria(searchForm);
  const filtered = listings
    .filter((listing) => matches(listing, criteria))
    .map((listing) => {
      const result = scoreListing(listing, criteria);
      return { listing, score: result.score };
    })
    .sort((a, b) => b.score - a.score)
    .slice(0, criteria.top);
  renderResults(filtered);
}

function restoreLastSearch(form) {
  const params = new URLSearchParams(window.location.search);
  const fields = [
    'region',
    'commune',
    'property_type',
    'min_area',
    'area_unit',
    'required_services',
    'preferred_services',
    'max_price',
    'max_price_m2',
    'top'
  ];
  fields.forEach((field) => {
    if (!params.has(field)) return;
    const input = form.querySelector(`[name="${field}"]`);
    if (!input) return;
    const value = params.get(field);
    input.value = value || '';
  });
}

function persistSearch(form) {
  const data = new FormData(form);
  const params = new URLSearchParams(window.location.search);
  [
    'region',
    'commune',
    'property_type',
    'min_area',
    'area_unit',
    'required_services',
    'preferred_services',
    'max_price',
    'max_price_m2',
    'top'
  ].forEach((key) => {
    const value = data.get(key);
    if (value) {
      params.set(key, value);
    } else {
      params.delete(key);
    }
  });
  const query = params.toString();
  const newUrl = query ? `${window.location.pathname}?${query}` : window.location.pathname;
  history.replaceState(null, '', newUrl);
}

async function fetchListings(url) {
  const response = await fetch(url, { cache: 'no-store' });
  if (!response.ok) {
    throw new Error(`No se pudo cargar el inventario: ${response.status} ${response.statusText}`);
  }
  const data = await response.json();
  return prepareListings(data);
}

function clearDataParam() {
  const params = new URLSearchParams(window.location.search);
  if (!params.has(DATA_URL_PARAM)) return;
  params.delete(DATA_URL_PARAM);
  const query = params.toString();
  const newUrl = query ? `${window.location.pathname}?${query}` : window.location.pathname;
  history.replaceState(null, '', newUrl);
}

function useListings(data, { label, href, isLocal }) {
  listings = data;
  buildGeographyLookups();
  hydrateFilters();
  performSearch();
  updateSourceIndicator(label, href, isLocal);
  if (isLocal) {
    displayMessage(`Inventario local cargado: ${label}`, 'success');
  } else {
    displayMessage(`Inventario cargado: ${label}`, 'success');
  }
}

async function loadInitialListings() {
  try {
    displayMessage('Cargando inventario…', 'info');
    const url = getDataUrl();
    const data = await fetchListings(url);
    useListings(data, { label: url, href: url, isLocal: false });
  } catch (error) {
    console.error(error);
    displayMessage(error.message, 'error');
    renderResults([]);
  }
}

async function handleFileUpload(event) {
  const file = event.target.files && event.target.files[0];
  if (!file) return;
  try {
    displayMessage(`Leyendo "${file.name}"…`, 'info');
    const text = await file.text();
    const parsed = JSON.parse(text);
    const data = prepareListings(parsed);
    useListings(data, { label: `${file.name}`, href: '', isLocal: true });
    clearDataParam();
  } catch (error) {
    console.error(error);
    displayMessage(`No se pudo leer el inventario: ${error.message}`, 'error');
  } finally {
    event.target.value = '';
  }
}

async function bootstrap() {
  searchForm = document.querySelector('#search-form');
  statusElement = document.querySelector('[data-feedback]');
  resultsContainer = document.querySelector('#results');
  sourceIndicator = document.querySelector('[data-current-source]');

  if (!searchForm || !resultsContainer) return;

  restoreLastSearch(searchForm);

  const regionSelect = searchForm.querySelector('#region');
  if (regionSelect) {
    regionSelect.addEventListener('change', () => {
      populateCommuneOptions(regionSelect.value, '');
    });
  }

  searchForm.addEventListener('submit', (event) => {
    event.preventDefault();
    performSearch();
    persistSearch(searchForm);
  });

  const uploadInput = document.querySelector('#inventory-upload');
  if (uploadInput) {
    uploadInput.addEventListener('change', handleFileUpload);
  }

  await loadInitialListings();
}

document.addEventListener('DOMContentLoaded', bootstrap);
