"""Mapa interactivo de Google Maps dentro de la aplicación.

* elegir_ubicacion(): el cliente marca su casa (clic en el mapa, arrastrar el
  marcador o buscar una dirección).
* ver_ubicacion(): el cobrador ve la casa marcada y abre la ruta en el navegador.

Si no hay llave de Google configurada, se usa OpenStreetMap automáticamente
(mismo diseño, sin registro ni tarjeta).

Configuración de Google (opcional)
----------------------------------
1. En Google Cloud crea una llave y habilita "Maps JavaScript API" y
   "Geocoding API".
2. Guarda la llave en la variable de entorno GOOGLE_MAPS_API_KEY, o en un
   archivo de texto `google_maps_key.txt` en la raíz del proyecto (no lo subas a Git).
3. Si restringes la llave por "referentes HTTP", agrega:
   https://sistema-crediticio.local/*
4. pip install PySide6-Addons   (componente del navegador de Qt)
"""
from __future__ import annotations

import json
import os
import re
from urllib.parse import quote

from app.config.rutas import PROYECTO_DIR
from app.logica.ubicacion import validar_coordenadas
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout,
)

try:
    from PySide6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE = True
except ImportError:                      # PySide6-Addons no instalado
    QWebEngineView = None
    WEBENGINE = False

# Centro por defecto del mapa: León, Nicaragua.
CENTRO_DEFECTO = (12.4379, -86.8780)
URL_BASE = "https://sistema-crediticio.local/"
ARCHIVO_CLAVE = PROYECTO_DIR / "google_maps_key.txt"


def clave_api() -> str:
    """Llave de Google Maps (variable de entorno o archivo junto al programa)."""
    clave = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    if not clave and ARCHIVO_CLAVE.exists():
        clave = ARCHIVO_CLAVE.read_text(encoding="utf-8").strip()
    return clave


_ESTILO = """
    QDialog { background-color: #F7F4EC; }
    QLabel { color: #112847; font-size: 14px; }
    QPushButton { background-color: #112847; color: white; border: none;
                  border-radius: 10px; padding: 10px 18px; font-size: 14px; font-weight: bold; }
    QPushButton:hover { background-color: #1B3A63; }
    QPushButton#secundario { background-color: #EFE6CF; color: #112847; }
    QPushButton#secundario:hover { background-color: #E2DAC8; }
"""

_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root { --navy:#112847; --navy2:#1B3A63; --oro:#C49A48; --crema:#F7F4EC; --borde:#E2DAC8; }
  html, body { height:100%; margin:0; font-family:'Segoe UI','Ubuntu',Roboto,sans-serif; background:var(--crema); }
  #mapa { position:absolute; inset:0; }
  #barra { position:absolute; z-index:5; top:14px; left:14px; right:210px; max-width:560px;
           display:__BARRA__; background:#fff; border-radius:14px; overflow:hidden;
           box-shadow:0 6px 20px rgba(17,40,71,.28); }
  #q { flex:1; border:0; outline:0; padding:13px 16px; font-size:15px; color:var(--navy); background:transparent; }
  #q::placeholder { color:#8A93A6; }
  #ir { border:0; background:var(--navy); color:#fff; font-weight:700; font-size:14px;
        padding:0 22px; cursor:pointer; transition:background .15s; }
  #ir:hover { background:var(--oro); }
  #tarjeta { position:absolute; z-index:5; left:50%; bottom:22px; transform:translateX(-50%);
             width:min(560px, calc(100% - 28px)); box-sizing:border-box; background:#fff;
             border-radius:14px; padding:12px 18px; border-left:5px solid var(--oro);
             box-shadow:0 6px 20px rgba(17,40,71,.28); color:var(--navy); }
  #titulo { font-size:11px; letter-spacing:.08em; text-transform:uppercase; color:#8A93A6; font-weight:700; }
  #texto { font-size:15px; font-weight:600; margin-top:2px; }
  #coords { font-size:12px; color:#6B7488; margin-top:2px; }
  #error { position:absolute; inset:0; z-index:10; display:none; align-items:center; justify-content:center;
           background:var(--crema); color:var(--navy); text-align:center; padding:30px; }
  #error div { max-width:420px; line-height:1.5; }
  #error b { font-size:18px; display:block; margin-bottom:6px; }
</style></head>
<body>
<div id="mapa"></div>
<div id="barra"><input id="q" placeholder="Buscar barrio, calle o punto de referencia..." autocomplete="off"><button id="ir">Buscar</button></div>
<div id="tarjeta"><div id="titulo">__TITULO__</div><div id="texto">__AYUDA__</div><div id="coords"></div></div>
<div id="error"><div><b id="errtitulo">No se pudo cargar el mapa</b><span id="errtexto"></span></div></div>
<script>
  var EDITABLE = __EDITABLE__;
  var punto = __PUNTO__;
  var DIRECCION = __DIRECCION__;
  var CENTRO = __CENTRO__;
  var mapa, marcador, geocoder;
  window.coords = punto;

  var ESTILO = [
    {elementType:'geometry', stylers:[{color:'#F7F4EC'}]},
    {elementType:'labels.text.fill', stylers:[{color:'#4A5568'}]},
    {elementType:'labels.text.stroke', stylers:[{color:'#FBF9F4'}]},
    {featureType:'water', elementType:'geometry', stylers:[{color:'#C6D6E6'}]},
    {featureType:'landscape.natural', elementType:'geometry', stylers:[{color:'#EFEBDD'}]},
    {featureType:'poi.park', elementType:'geometry', stylers:[{color:'#D9E6C9'}]},
    {featureType:'poi.business', stylers:[{visibility:'off'}]},
    {featureType:'poi', elementType:'labels.icon', stylers:[{visibility:'off'}]},
    {featureType:'road', elementType:'geometry', stylers:[{color:'#FFFFFF'}]},
    {featureType:'road', elementType:'geometry.stroke', stylers:[{color:'#E2DAC8'}]},
    {featureType:'road.arterial', elementType:'geometry', stylers:[{color:'#FFFBF0'}]},
    {featureType:'road.highway', elementType:'geometry', stylers:[{color:'#F1DDB0'}]},
    {featureType:'road.highway', elementType:'geometry.stroke', stylers:[{color:'#C49A48'}]},
    {featureType:'transit', stylers:[{visibility:'off'}]},
    {featureType:'administrative', elementType:'geometry.stroke', stylers:[{color:'#C49A48'}]}
  ];

  var PIN = '<svg xmlns="http://www.w3.org/2000/svg" width="44" height="56" viewBox="0 0 44 56">' +
    '<path d="M22 2C11.5 2 3.5 10 3.5 20.2c0 13.6 15.1 29.8 17.6 32.4a1.3 1.3 0 0 0 1.8 0C25.4 50 40.5 33.8 40.5 20.2 40.5 10 32.5 2 22 2z" fill="#112847" stroke="#FFFFFF" stroke-width="3"/>' +
    '<circle cx="22" cy="20" r="8" fill="#C49A48"/><circle cx="22" cy="20" r="3.2" fill="#112847"/></svg>';

  function mostrarError(titulo, texto) {
    document.getElementById('errtitulo').textContent = titulo;
    document.getElementById('errtexto').textContent = texto;
    document.getElementById('error').style.display = 'flex';
  }
  window.gm_authFailure = function () {
    mostrarError('Llave de Google Maps no válida',
      'Revisa que la llave sea correcta, que "Maps JavaScript API" esté habilitada y que ' +
      'la restricción de referentes incluya https://sistema-crediticio.local/*');
  };

  function actualizarTarjeta(lat, lng) {
    document.getElementById('titulo').textContent = 'Ubicación marcada';
    document.getElementById('coords').textContent = lat.toFixed(6) + ', ' + lng.toFixed(6);
    document.getElementById('texto').textContent = 'Buscando dirección...';
    geocoder.geocode({location: {lat: lat, lng: lng}}, function (r, estado) {
      var t = (estado === 'OK' && r && r.length) ? r[0].formatted_address : 'Punto marcado en el mapa';
      document.getElementById('texto').textContent = t;
    });
  }

  function poner(lat, lng, animar) {
    window.coords = {lat: lat, lng: lng};
    if (!marcador) {
      marcador = new google.maps.Marker({
        map: mapa, position: {lat: lat, lng: lng}, draggable: EDITABLE,
        icon: {url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(PIN),
               scaledSize: new google.maps.Size(40, 51), anchor: new google.maps.Point(20, 51)},
        animation: animar ? google.maps.Animation.DROP : null
      });
      marcador.addListener('dragend', function () {
        var p = marcador.getPosition(); window.coords = {lat: p.lat(), lng: p.lng()};
        actualizarTarjeta(p.lat(), p.lng());
      });
    } else {
      marcador.setPosition({lat: lat, lng: lng});
      if (animar) { marcador.setAnimation(google.maps.Animation.DROP); }
    }
    actualizarTarjeta(lat, lng);
  }

  function buscar() {
    var texto = document.getElementById('q').value.trim();
    if (!texto) { return; }
    geocoder.geocode({address: texto, region: 'NI', componentRestrictions: {country: 'NI'}},
      function (r, estado) {
        if (estado !== 'OK' || !r.length) {
          document.getElementById('titulo').textContent = 'Sin resultados';
          document.getElementById('texto').textContent = 'No se encontró. Marca el punto con un clic en el mapa.';
          return;
        }
        var loc = r[0].geometry.location;
        mapa.panTo(loc); mapa.setZoom(18);
        poner(loc.lat(), loc.lng(), true);
      });
  }

  function iniciar() {
    geocoder = new google.maps.Geocoder();
    mapa = new google.maps.Map(document.getElementById('mapa'), {
      center: punto ? {lat: punto.lat, lng: punto.lng} : {lat: CENTRO[0], lng: CENTRO[1]},
      zoom: punto ? 18 : 14, styles: ESTILO, clickableIcons: false, gestureHandling: 'greedy',
      streetViewControl: false, fullscreenControl: false, rotateControl: false,
      mapTypeControl: true,
      mapTypeControlOptions: {mapTypeIds: ['roadmap', 'hybrid'],
        style: google.maps.MapTypeControlStyle.HORIZONTAL_BAR,
        position: google.maps.ControlPosition.TOP_RIGHT},
      zoomControlOptions: {position: google.maps.ControlPosition.RIGHT_CENTER}
    });
    document.getElementById('q').value = DIRECCION;
    if (punto) { poner(punto.lat, punto.lng, false); }
    else if (DIRECCION) { buscar(); }
    if (EDITABLE) {
      mapa.addListener('click', function (e) { poner(e.latLng.lat(), e.latLng.lng(), true); });
      document.getElementById('ir').onclick = buscar;
      document.getElementById('q').addEventListener('keydown', function (e) { if (e.key === 'Enter') { buscar(); } });
    }
  }
  window.iniciar = iniciar;

  var s = document.createElement('script');
  s.src = 'https://maps.googleapis.com/maps/api/js?key=__CLAVE__&callback=iniciar&loading=async&language=es&region=NI&v=weekly';
  s.async = true;
  s.onerror = function () { mostrarError('Sin conexión', 'No se pudo contactar con Google Maps. Revisa tu internet.'); };
  document.head.appendChild(s);
</script></body></html>"""


# --------------------------------------------------------------------------
# Respaldo sin llave: OpenStreetMap + Leaflet (se usa si no hay llave de Google)
# --------------------------------------------------------------------------
_CSS = re.search(r"<style>.*?</style>", _HTML, re.S).group(0)

_HTML_OSM = """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
__CSS__
</head>
<body>
<div id="mapa"></div>
<div id="barra"><input id="q" placeholder="Buscar barrio, calle o punto de referencia..." autocomplete="off"><button id="ir">Buscar</button></div>
<div id="tarjeta"><div id="titulo">__TITULO__</div><div id="texto">__AYUDA__</div><div id="coords"></div></div>
<div id="error"><div><b id="errtitulo">No se pudo cargar el mapa</b><span id="errtexto"></span></div></div>
<script>
  var EDITABLE = __EDITABLE__;
  var punto = __PUNTO__;
  var DIRECCION = __DIRECCION__;
  var CENTRO = __CENTRO__;
  window.coords = punto;
  document.getElementById('barra').style.right = '14px';
  if (typeof L === 'undefined') {
    document.getElementById('errtexto').textContent = 'No se pudo contactar con el servidor de mapas. Revisa tu internet.';
    document.getElementById('error').style.display = 'flex';
  } else {
    var PIN = '<svg xmlns="http://www.w3.org/2000/svg" width="44" height="56" viewBox="0 0 44 56">' +
      '<path d="M22 2C11.5 2 3.5 10 3.5 20.2c0 13.6 15.1 29.8 17.6 32.4a1.3 1.3 0 0 0 1.8 0C25.4 50 40.5 33.8 40.5 20.2 40.5 10 32.5 2 22 2z" fill="#112847" stroke="#FFFFFF" stroke-width="3"/>' +
      '<circle cx="22" cy="20" r="8" fill="#C49A48"/><circle cx="22" cy="20" r="3.2" fill="#112847"/></svg>';
    var icono = L.divIcon({html: PIN, className: '', iconSize: [40, 51], iconAnchor: [20, 51]});
    var mapa = L.map('mapa', {zoomControl: false}).setView(punto ? [punto.lat, punto.lng] : CENTRO, punto ? 18 : 14);
    L.control.zoom({position: 'bottomright'}).addTo(mapa);
    L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 19, attribution: '&copy; OpenStreetMap'}).addTo(mapa);
    var marcador = null;
    function tarjeta(lat, lng) {
      document.getElementById('titulo').textContent = 'Ubicación marcada';
      document.getElementById('coords').textContent = lat.toFixed(6) + ', ' + lng.toFixed(6);
      document.getElementById('texto').textContent = 'Buscando dirección...';
      fetch('https://nominatim.openstreetmap.org/reverse?format=jsonv2&accept-language=es&lat=' + lat + '&lon=' + lng)
        .then(function (r) { return r.json(); })
        .then(function (d) { document.getElementById('texto').textContent = d.display_name || 'Punto marcado en el mapa'; })
        .catch(function () { document.getElementById('texto').textContent = 'Punto marcado en el mapa'; });
    }
    function poner(lat, lng) {
      window.coords = {lat: lat, lng: lng};
      if (!marcador) {
        marcador = L.marker([lat, lng], {icon: icono, draggable: EDITABLE}).addTo(mapa);
        marcador.on('dragend', function () {
          var p = marcador.getLatLng(); window.coords = {lat: p.lat, lng: p.lng}; tarjeta(p.lat, p.lng);
        });
      } else { marcador.setLatLng([lat, lng]); }
      tarjeta(lat, lng);
    }
    document.getElementById('q').value = DIRECCION;
    if (punto) { poner(punto.lat, punto.lng); }
    else if (DIRECCION) { buscar(); }
    function buscar() {
        var texto = document.getElementById('q').value.trim();
        if (!texto) { return; }
        fetch('https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=ni&q=' + encodeURIComponent(texto))
          .then(function (r) { return r.json(); })
          .then(function (d) {
            if (!d.length) {
              document.getElementById('titulo').textContent = 'Sin resultados';
              document.getElementById('texto').textContent = 'No se encontró. Marca el punto con un clic en el mapa.';
              return;
            }
            var lat = parseFloat(d[0].lat), lng = parseFloat(d[0].lon);
            mapa.setView([lat, lng], 18); poner(lat, lng);
          })
          .catch(function () { document.getElementById('texto').textContent = 'No se pudo buscar. Revisa tu conexión.'; });
      }
    if (EDITABLE) {
      mapa.on('click', function (e) { poner(e.latlng.lat, e.latlng.lng); });
      document.getElementById('ir').onclick = buscar;
      document.getElementById('q').addEventListener('keydown', function (e) { if (e.key === 'Enter') { buscar(); } });
    }
  }
</script></body></html>"""


def _html(lat, lng, editable: bool, direccion: str = "") -> str:
    lat, lng = validar_coordenadas(lat, lng)
    punto = json.dumps({"lat": float(lat), "lng": float(lng)}) if lat is not None and lng is not None else "null"
    ayuda = ("Haz clic en el mapa o arrastra el marcador sobre tu casa."
             if editable else "Ubicación marcada por el cliente.")
    plantilla = _HTML if clave_api() else _HTML_OSM.replace("__CSS__", _CSS)
    return (plantilla.replace("__PUNTO__", punto)
                 .replace("__CENTRO__", json.dumps(list(CENTRO_DEFECTO)))
                 .replace("__EDITABLE__", "true" if editable else "false")
                 .replace("__BARRA__", "flex" if editable else "none")
                 .replace("__TITULO__", "Ubicación" if editable else "Casa del cliente")
                 .replace("__AYUDA__", ayuda)
                 .replace("__CLAVE__", quote(clave_api(), safe=""))
                 .replace("__DIRECCION__", json.dumps(direccion, ensure_ascii=True).replace("<", "\\u003c")))


def _vista(parent_layout, lat, lng, editable: bool, direccion: str = ""):
    vista = QWebEngineView()
    # La URL base https permite que Google Maps valide la llave y el referente.
    vista.setHtml(_html(lat, lng, editable, direccion), QUrl(URL_BASE))
    parent_layout.addWidget(vista, 1)
    return vista


def _sin_webengine(parent) -> None:
    QMessageBox.warning(
        parent, "Mapa no disponible",
        "Falta el componente del mapa. Instálalo con:\n\n    pip install PySide6-Addons",
    )


def enlace_ruta(lat, lng, direccion: str = "") -> str:
    lat, lng = validar_coordenadas(lat, lng)
    destino = f"{float(lat):.7f},{float(lng):.7f}" if lat is not None else direccion
    return "https://www.google.com/maps/dir/?api=1&destination=" + quote(destino, safe=",")


class DialogoElegirUbicacion(QDialog):
    def __init__(self, lat=None, lng=None, parent=None, direccion: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Marca tu casa en el mapa")
        self.resize(940, 660)
        self.setStyleSheet(_ESTILO)
        self.resultado: tuple[float, float] | None = None

        caja = QVBoxLayout(self)
        caja.setContentsMargins(12, 12, 12, 12)
        self.vista = _vista(caja, lat, lng, editable=True, direccion=direccion)

        botones = QHBoxLayout()
        botones.addStretch()
        cancelar = QPushButton("Cancelar")
        cancelar.setObjectName("secundario")
        cancelar.clicked.connect(self.reject)
        guardar = QPushButton("Guardar ubicación")
        guardar.clicked.connect(self._guardar)
        botones.addWidget(cancelar)
        botones.addWidget(guardar)
        caja.addLayout(botones)

    def _guardar(self) -> None:
        self.vista.page().runJavaScript("JSON.stringify(window.coords)", self._recibir)

    def _recibir(self, texto) -> None:
        try:
            datos = json.loads(texto) if texto else None
            if datos:
                self.resultado = validar_coordenadas(datos["lat"], datos["lng"])
        except (ValueError, TypeError, KeyError):
            QMessageBox.warning(self, "Ubicación inválida", "Vuelve a marcar el punto en el mapa.")
            return
        if not datos:
            QMessageBox.warning(self, "Sin ubicación",
                                "Haz clic en el mapa para marcar tu casa antes de guardar.")
            return
        self.accept()


class DialogoVerUbicacion(QDialog):
    def __init__(self, titulo: str, direccion: str, lat, lng, parent=None):
        super().__init__(parent)
        self.setWindowTitle(titulo)
        self.resize(940, 660)
        self.setStyleSheet(_ESTILO)

        caja = QVBoxLayout(self)
        caja.setContentsMargins(12, 12, 12, 12)
        if direccion:
            etiqueta = QLabel(f"Dirección: {direccion}")
            etiqueta.setTextFormat(Qt.TextFormat.PlainText)
            etiqueta.setWordWrap(True)
            caja.addWidget(etiqueta)
        _vista(caja, lat, lng, editable=False, direccion=direccion)

        botones = QHBoxLayout()
        botones.addStretch()
        cerrar = QPushButton("Cerrar")
        cerrar.setObjectName("secundario")
        cerrar.clicked.connect(self.accept)
        ruta = QPushButton("Cómo llegar (abrir en Google Maps)")
        ruta.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(enlace_ruta(lat, lng, direccion))))
        botones.addWidget(cerrar)
        botones.addWidget(ruta)
        caja.addLayout(botones)


def elegir_ubicacion(parent, lat=None, lng=None, direccion: str = "") -> tuple[float, float] | None:
    """Abre el mapa para marcar un punto. Devuelve (lat, lng) o None si cancela."""
    if not WEBENGINE:
        _sin_webengine(parent)
        return None
    dialogo = DialogoElegirUbicacion(lat, lng, parent, direccion=direccion)
    return dialogo.resultado if dialogo.exec() == QDialog.DialogCode.Accepted else None


def ver_ubicacion(parent, nombre: str, direccion: str, lat, lng) -> None:
    """Muestra la casa marcada de un cliente (para el cobrador)."""
    if (lat is None or lng is None) and not direccion.strip():
        QMessageBox.information(parent, "Sin ubicación",
                                f"{nombre} todavía no marcó su casa en el mapa.")
        return
    if not WEBENGINE:
        QDesktopServices.openUrl(QUrl(enlace_ruta(lat, lng, direccion)))   # al menos abre Google Maps
        return
    DialogoVerUbicacion(f"Ubicación de {nombre}", direccion, lat, lng, parent).exec()
