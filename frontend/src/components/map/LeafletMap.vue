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

  if (imageUrl) {
    const image = document.createElement('img')
    image.src = imageUrl
    image.alt = ''
    preview.appendChild(image)
  } else {
    const fallback = document.createElement('span')
    fallback.className = 'map-place-image-fallback'
    fallback.textContent = '42'
    preview.appendChild(fallback)
  }

  const title = document.createElement('strong')
  title.textContent = name
  preview.appendChild(title)
  return preview
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

    const marker = L.marker(latLng, { icon }).bindTooltip(
      createPlacePreview(placeName, props.images[idx] ?? null),
      {
        permanent: false,
        direction: 'top',
        offset: [0, -20],
        className: 'place-preview-tooltip',
      },
    )

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

.place-preview-tooltip::before {
  border-top-color: rgba(255, 255, 255, 0.96) !important;
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
  background: linear-gradient(145deg, #ffe5eb, #ece5ff);
  color: #d25f78;
  font-size: 18px;
  font-weight: 900;
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
