<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

interface Props {
  coords: [number, number][]
  places: string[]
  images?: Array<string | null>
  static?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  images: () => [],
  static: false,
})

const mapContainer = ref<HTMLDivElement | null>(null)
let map: L.Map | null = null
let markerGroup: L.LayerGroup | null = null
let polyline: L.Polyline | null = null

// Custom styled markers matching wireframe pin styles
const createNumberedIcon = (num: string | number) => {
  return L.divIcon({
    html: `<div class="leaflet-custom-marker"><i>${num}</i></div>`,
    className: 'custom-div-icon',
    iconSize: [30, 30],
    iconAnchor: [15, 30],
  })
}

function createPlacePreview(name: string, imageUrl: string | null) {
  const preview = document.createElement('div')
  preview.className = 'map-place-preview'

  const createImageFallback = () => {
    const fallback = document.createElement('span')
    fallback.className = 'map-place-image-fallback'
    fallback.textContent = '사진 준비 중'
    return fallback
  }

  if (imageUrl) {
    const image = document.createElement('img')
    image.src = imageUrl.replace(/^http:/, 'https:')
    image.alt = `${name} 장소 사진`
    image.referrerPolicy = 'no-referrer'
    image.decoding = 'async'
    image.addEventListener('error', () => image.replaceWith(createImageFallback()), { once: true })
    preview.appendChild(image)
  } else {
    preview.appendChild(createImageFallback())
  }

  const title = document.createElement('strong')
  title.textContent = name
  preview.appendChild(title)
  return preview
}

function openPlacePreview(
  marker: L.Marker,
  latLng: L.LatLngTuple,
  placeName: string,
  imageUrl: string | null,
) {
  if (!map) return

  const mapSize = map.getSize()
  const currentPoint = map.latLngToContainerPoint(latLng)
  const direction: L.Direction = currentPoint.y < mapSize.y / 2 ? 'bottom' : 'top'
  const previewSpace = 136
  const markerSpace = 32
  const horizontalSpace = 72

  map.panInside(latLng, {
    paddingTopLeft: L.point(horizontalSpace, direction === 'bottom' ? markerSpace : previewSpace),
    paddingBottomRight: L.point(
      horizontalSpace,
      direction === 'bottom' ? previewSpace : markerSpace,
    ),
    animate: false,
  })

  const safePoint = map.latLngToContainerPoint(latLng)
  const minCenterX = horizontalSpace
  const maxCenterX = Math.max(minCenterX, mapSize.x - horizontalSpace)
  const clampedCenterX = Math.min(Math.max(safePoint.x, minCenterX), maxCenterX)
  const horizontalOffset = Math.round(clampedCenterX - safePoint.x)

  marker.unbindTooltip()
  marker
    .bindTooltip(createPlacePreview(placeName, imageUrl), {
      permanent: false,
      direction,
      offset: L.point(horizontalOffset, direction === 'bottom' ? 18 : -20),
      className: 'place-preview-tooltip',
    })
    .openTooltip()
}

function initMap() {
  if (!mapContainer.value) return

  // Center around Seoul Hanyang University
  map = L.map(mapContainer.value, {
    zoomControl: !props.static,
    attributionControl: false,
    dragging: !props.static,
    touchZoom: !props.static,
    doubleClickZoom: !props.static,
    scrollWheelZoom: !props.static,
    boxZoom: !props.static,
    keyboard: !props.static,
  }).setView([37.5564, 127.0445], 14)

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
  }).addTo(map)

  markerGroup = L.layerGroup().addTo(map)

  updateMarkersAndLines()
}

function updateMarkersAndLines() {
  if (!map || !markerGroup) return

  markerGroup.clearLayers()
  if (polyline) {
    polyline.remove()
    polyline = null
  }

  const points: L.LatLngExpression[] = []

  props.coords.forEach((coord, idx) => {
    const latLng: L.LatLngTuple = [coord[0], coord[1]]
    points.push(latLng)

    const placeName = props.places[idx] || ''
    const icon = createNumberedIcon(idx + 1)

    const imageUrl = props.images[idx] ?? null
    const marker = L.marker(latLng, { icon })
    marker.on('mouseover', () => openPlacePreview(marker, latLng, placeName, imageUrl))
    marker.on('mouseout', () => marker.closeTooltip())

    markerGroup!.addLayer(marker)
  })

  if (points.length > 1) {
    polyline = L.polyline(points, {
      color: '#ff6079',
      weight: 4,
      opacity: 0.8,
      dashArray: '5, 10',
    }).addTo(map)
  }

  if (points.length > 0) {
    const bounds = L.latLngBounds(points)
    map.fitBounds(bounds, { padding: [30, 30] })
  }
}

watch(
  () => [props.coords, props.places, props.images],
  () => {
    updateMarkersAndLines()
  },
  { deep: true },
)

onMounted(() => {
  initMap()
  setTimeout(() => {
    if (map) map.invalidateSize()
  }, 100)
})

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
})
</script>

<template>
  <div ref="mapContainer" :class="['leaflet-map-element', { 'static-map': static }]"></div>
</template>

<style>
.leaflet-map-element {
  width: 100%;
  height: 100%;
  z-index: 1;
}

.leaflet-custom-marker {
  pointer-events: none;
  width: 30px;
  height: 30px;
  display: grid;
  place-items: center;
  border: 3px solid #fff;
  border-radius: 50% 50% 50% 5px;
  transform: rotate(-45deg) translateY(-2px);
  background: #ff8295;
  color: #fff;
  font-size: 10px;
  font-weight: 900;
  box-shadow: 0 6px 11px rgba(70, 50, 55, 0.2);
}

.leaflet-custom-marker i {
  font-style: normal;
  transform: rotate(45deg);
}

.custom-div-icon {
  background: transparent;
  border: none;
}

.place-preview-tooltip {
  padding: 0;
  overflow: hidden;
  border: 1px solid rgba(232, 214, 221, 0.92);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 10px 22px rgba(77, 53, 61, 0.18);
}

.leaflet-tooltip-top.place-preview-tooltip::before {
  border-top-color: rgba(255, 255, 255, 0.96) !important;
}

.leaflet-tooltip-bottom.place-preview-tooltip::before {
  border-bottom-color: rgba(255, 255, 255, 0.96) !important;
}

.map-place-preview {
  width: 128px;
  display: grid;
}

.map-place-preview img,
.map-place-image-fallback {
  width: 128px;
  height: 72px;
  object-fit: cover;
}

.map-place-image-fallback {
  display: grid;
  place-items: center;
  background: #f2efed;
  color: #95858a;
  font-size: 9px;
  font-weight: 800;
}

.map-place-preview strong {
  overflow: hidden;
  padding: 9px 10px;
  color: #55474a;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
