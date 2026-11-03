import { useEffect, useRef } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

export default function Map({ latitud, longitud, onChange, readOnly = false }) {
  const root = useRef(null), map = useRef(null), marker = useRef(null), change = useRef(onChange);
  change.current = onChange;
  useEffect(() => {
    const instance = L.map(root.current, { zoomAnimation: false, fadeAnimation: false, markerZoomAnimation: false }).setView([12.1364, -86.2514], 12);
    map.current = instance;
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>' }).addTo(instance);
    if (!readOnly) instance.on('click', e => change.current?.({ latitud: Number(e.latlng.lat.toFixed(7)), longitud: Number(e.latlng.lng.toFixed(7)) }));
    const resize = new ResizeObserver(() => instance.invalidateSize()); resize.observe(root.current);
    return () => { resize.disconnect(); instance.stop(); instance.remove(); map.current = null; marker.current = null; };
  }, [readOnly]);
  useEffect(() => {
    if (!map.current) return;
    if (marker.current) { marker.current.remove(); marker.current = null; }
    if (latitud !== null && latitud !== undefined && latitud !== '' && longitud !== null && longitud !== undefined && longitud !== '') {
      const point = [Number(latitud), Number(longitud)];
      if (point.every(Number.isFinite) && Math.abs(point[0]) <= 90 && Math.abs(point[1]) <= 180) {
        marker.current = L.circleMarker(point, { radius: 9, color: '#fff', weight: 3, fillColor: '#087f68', fillOpacity: 1 }).addTo(map.current);
        map.current.setView(point, 15, { animate: false });
      }
    }
  }, [latitud, longitud]);
  return <div ref={root} className="map" role="region" aria-label={readOnly ? 'Ubicación del cliente' : 'Seleccionar ubicación en el mapa'} />;
}
