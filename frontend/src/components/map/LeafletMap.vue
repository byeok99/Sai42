<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from 'vue'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const props = defineProps<{
  coords: [number, number][]
  places: string[]
}>()

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

function initMap() {
  if (!mapContainer.value) return

  // Center around Seoul Hanyang University
  map = L.map(mapContainer.value, {
    zoomControl: false,
    attributionControl: false,
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

    const marker = L.marker(latLng, { icon }).bindTooltip(placeName, {
      permanent: false,
      direction: 'top',
    })

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
  () => props.coords,
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
  <div ref="mapContainer" class="leaflet-map-element"></div>
</template>

<style>
.leaflet-map-element {
  width: 100%;
  height: 100%;
  z-index: 1;
}

.leaflet-custom-marker {
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
</style>
