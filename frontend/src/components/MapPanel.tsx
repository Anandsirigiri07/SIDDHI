import React, { useRef, useEffect, useState } from 'react';
import L from 'leaflet';
import { Map, MapPin, TrendingUp } from 'lucide-react';
import { fetchForecast } from '../utils/api';
import type { ForecastData } from '../utils/api';

interface MapPanelProps {
  heatmapData: any | null;
  onHotspotClick: (followUpQuery: string) => void;
  selectedEntity?: { type: string; id: string | number; source: string } | null;
  onSelectEntity?: (entity: { type: string; id: string | number; source: string }) => void;
}

export const MapPanel: React.FC<MapPanelProps> = ({ heatmapData, onHotspotClick, selectedEntity, onSelectEntity }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersGroupRef = useRef<L.FeatureGroup | null>(null);
  const forecastGroupRef = useRef<L.FeatureGroup | null>(null);
  const anomalyGroupRef = useRef<L.FeatureGroup | null>(null);

  const [showForecast, setShowForecast] = useState(false);
  const [forecastData, setForecastData] = useState<ForecastData | null>(null);
  const [forecastLoading, setForecastLoading] = useState(false);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        zoomControl: false,
        attributionControl: false
      }).setView([12.9716, 77.5946], 11);

      L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}', {
        maxZoom: 16
      }).addTo(map);

      L.control.zoom({ position: 'bottomright' }).addTo(map);

      mapInstanceRef.current = map;
      markersGroupRef.current = L.featureGroup().addTo(map);
      forecastGroupRef.current = L.featureGroup().addTo(map);
      anomalyGroupRef.current = L.featureGroup().addTo(map);
    }
  }, []);

  useEffect(() => {
    if (!mapInstanceRef.current || !markersGroupRef.current || !anomalyGroupRef.current) return;

    markersGroupRef.current.clearLayers();
    anomalyGroupRef.current.clearLayers();

    if (!heatmapData) {
      mapInstanceRef.current.setView([12.9716, 77.5946], 11);
      setTimeout(() => mapInstanceRef.current?.invalidateSize(), 100);
      return;
    }

    setTimeout(() => mapInstanceRef.current?.invalidateSize(), 100);

    const geojson = heatmapData.geojson || heatmapData.heatmap || (heatmapData.type === 'FeatureCollection' ? heatmapData : null);
    const features = geojson?.features || [];

    features.forEach((feature: any) => {
      const [lng, lat] = feature.geometry.coordinates;
      const props = feature.properties;

      let color = '#ef4444'; // Red
      if (props.severity === 'Amber' || props.severity === 'Medium') {
        color = '#f59e0b'; // Amber
      } else if (props.severity === 'Low') {
        color = '#10b981'; // Green
      }

      const isSelected = selectedEntity && (selectedEntity.type === 'location' || selectedEntity.type === 'hotspot') && String(selectedEntity.id) === String(props.cluster_id || props.location_name);

      const circle = L.circle([lat, lng], {
        radius: isSelected ? 500 : 350,
        color: isSelected ? '#00e5ff' : color,
        fillColor: color,
        fillOpacity: isSelected ? 0.5 : 0.3,
        weight: isSelected ? 3 : 1.5
      });

      const popupContent = document.createElement('div');
      popupContent.className = 'p-1.5 text-xs font-sans text-slate-100 flex flex-col gap-1.5 min-w-[200px] bg-slate-900';
      popupContent.innerHTML = `
        <div class="font-bold border-b border-slate-700 pb-1 text-cyan-400 text-sm uppercase tracking-wide">${props.location_name}</div>
        <div class="flex justify-between"><span class="text-slate-400 font-semibold">Risk Rating:</span> <span class="font-bold text-amber-400">${props.risk_score}</span></div>
        <div class="flex justify-between"><span class="text-slate-400 font-semibold">Incident Count:</span> <span class="font-bold text-slate-200">${props.crime_count}</span></div>
        <div class="flex justify-between"><span class="text-slate-400 font-semibold">Primary Crime:</span> <span class="font-bold text-slate-200">${props.dominant_crime}</span></div>
        <div class="text-[10px] text-slate-400 italic mt-1">Logged: ${props.date_range || 'Active Zone'}</div>
        <button id="query-hotspot-${props.cluster_id}" class="mt-2 w-full bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold py-1.5 px-2 rounded cursor-pointer text-center text-[10px] uppercase tracking-wider transition-colors duration-200">
          Run Contextual Query
        </button>
      `;

      popupContent.querySelector('button')?.addEventListener('click', () => {
        const crimeStr = (props.dominant_crime || 'Crime').toString().toLowerCase();
        const locStr = (props.location_name || 'Location').toString().split(' ')[0];
        const followUp = `Show all ${crimeStr} cases near ${locStr}`;
        onHotspotClick(followUp);
        if (onSelectEntity) {
          onSelectEntity({ type: 'location', id: props.location_name || 'Location', source: 'map' });
        }
      });

      circle.bindPopup(popupContent);
      markersGroupRef.current?.addLayer(circle);
    });

    // Render Anomaly Detection Markers (Feature 2)
    const anomalies = heatmapData.anomalies || [];
    anomalies.forEach((anom: any) => {
      if (anom.lat && anom.lng) {
        const pulseMarker = L.circle([anom.lat, anom.lng], {
          radius: 600,
          color: '#f43f5e',
          fillColor: '#f43f5e',
          fillOpacity: 0.25,
          weight: 2,
          dashArray: '4 4'
        });

        pulseMarker.bindPopup(`
          <div class="p-2 text-xs font-sans text-slate-100 flex flex-col gap-1.5 min-w-[220px] bg-slate-950 border border-rose-500/40 rounded-md">
            <div class="font-bold border-b border-rose-800/50 pb-1 text-rose-400 text-xs uppercase tracking-widest flex items-center gap-1">
              🚨 Anomaly Spike: ${anom.location_name}
            </div>
            <div class="flex justify-between"><span class="text-slate-400">Current 7d Incidents:</span> <span class="font-bold text-rose-300">${anom.current_7d_incidents}</span></div>
            <div class="flex justify-between"><span class="text-slate-400">Historical Avg:</span> <span class="font-bold text-slate-300">${anom.historical_weekly_avg}/wk</span></div>
            <div class="flex justify-between"><span class="text-slate-400">Baseline Deviation:</span> <span class="font-bold text-amber-400">+${anom.deviation_pct}%</span></div>
            <div class="flex justify-between"><span class="text-slate-400">Z-Score:</span> <span class="font-bold text-slate-200">${anom.z_score} (${anom.severity})</span></div>
            <div class="text-[10px] text-slate-400 mt-1 italic border-t border-slate-800 pt-1">${anom.explanation}</div>
          </div>
        `);
        anomalyGroupRef.current?.addLayer(pulseMarker);
      }
    });

    try {
      const bounds = markersGroupRef.current.getBounds();
      if (bounds.isValid()) {
        mapInstanceRef.current.fitBounds(bounds, { padding: [40, 40] });
      }
    } catch (e) {}

  }, [heatmapData, onHotspotClick, selectedEntity, onSelectEntity]);

  useEffect(() => {
    if (!showForecast || forecastData) return;
    setForecastLoading(true);
    fetchForecast()
      .then((data) => setForecastData(data))
      .catch((e) => console.error('Forecast fetch failed', e))
      .finally(() => setForecastLoading(false));
  }, [showForecast, forecastData]);

  useEffect(() => {
    if (!mapInstanceRef.current || !forecastGroupRef.current) return;
    forecastGroupRef.current.clearLayers();
    if (!showForecast || !forecastData) return;

    forecastData.features.forEach((feature: any) => {
      const [lng, lat] = feature.geometry.coordinates;
      const props = feature.properties;

      let color = '#a855f7';
      if (props.trend === 'Stable') color = '#38bdf8';
      else if (props.trend === 'Declining') color = '#64748b';

      const circle = L.circle([lat, lng], {
        radius: 450,
        color: color,
        fillColor: color,
        fillOpacity: 0.15,
        weight: 2,
        dashArray: '6 6'
      });

      const signalsList = (props.contributing_signals || []).map((s: string) => `<li class="text-[10px] text-slate-300">• ${s}</li>`).join('');

      circle.bindPopup(`
        <div class="p-2 text-xs font-sans text-slate-100 flex flex-col gap-1.5 min-w-[230px] bg-slate-900 border border-purple-500/30 rounded-md">
          <div class="font-bold border-b border-purple-800/40 pb-1 text-purple-400 text-xs uppercase tracking-wide">
            🔮 ML Forecast: ${props.location_name}
          </div>
          <div class="flex justify-between"><span class="text-slate-400">Trend (${props.prediction_window || 'Next 7d'}):</span> <span class="font-bold text-purple-300">${props.trend} (${props.expected_change_pct > 0 ? '+' : ''}${props.expected_change_pct || 0}%)</span></div>
          <div class="flex justify-between"><span class="text-slate-400">Forecast Strength:</span> <span class="font-bold text-amber-400">${props.forecast_strength || 'Moderate'}</span></div>
          <div class="flex justify-between"><span class="text-slate-400">Predicted Incidents:</span> <span class="font-bold text-slate-200">${props.predicted_weekly_incidents}/wk</span></div>
          <div class="flex justify-between"><span class="text-slate-400">Historical Avg:</span> <span class="font-bold text-slate-300">${props.historical_weekly_avg}/wk</span></div>
          <div class="mt-1 font-bold text-[10px] text-purple-300 uppercase tracking-wider">Contributing Signals:</div>
          <ul class="flex flex-col gap-0.5">${signalsList}</ul>
          <div class="text-[9px] text-slate-400 italic border-t border-slate-800 pt-1 mt-1 font-mono">${props.assessment || 'Elevated crime risk based on historical patterns.'}</div>
        </div>
      `);
      forecastGroupRef.current?.addLayer(circle);
    });
  }, [showForecast, forecastData]);

  return (
    <div className="glass-panel w-full rounded-lg flex flex-col h-[520px] shadow-2xl relative">
      <div className="p-3 border-b border-slate-800 flex items-center justify-between bg-slate-900/40">
        <div className="flex items-center gap-2">
          <Map className="w-4 h-4 text-cyan-500" />
          <h3 className="text-xs font-bold uppercase tracking-widest text-slate-300">
            Geospatial Hotspot Map Lens
          </h3>
        </div>
        
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowForecast((v) => !v)}
            className={`text-[10px] font-bold uppercase tracking-wider flex items-center gap-1 px-2 py-1 rounded border transition-colors duration-200 cursor-pointer ${
              showForecast
                ? 'bg-purple-500/20 border-purple-500 text-purple-300'
                : 'bg-slate-900/60 border-slate-700 text-slate-400 hover:text-slate-200'
            }`}
            title="Toggle explainable hotspot forecast (next 7 days)"
          >
            <TrendingUp className="w-3 h-3" />
            {forecastLoading ? 'Loading…' : 'Forecast'}
          </button>
          <span className="text-[10px] text-slate-400 font-mono flex items-center gap-1">
            <MapPin className="w-3 h-3 text-rose-500 animate-bounce" />
            Bengaluru Sector HUD
          </span>
        </div>
      </div>

      <div className="flex-1 relative">
        <div ref={mapContainerRef} className="w-full h-full" id="siddhi-leaflet-map" />
        
        {(!heatmapData || (!heatmapData.features?.length && !heatmapData.geojson?.features?.length && !heatmapData.heatmap?.features?.length && !heatmapData.anomalies?.length)) && (
          <div className="absolute inset-0 bg-slate-950/70 backdrop-blur-[1px] flex flex-col items-center justify-center text-center p-6 text-slate-500 select-none z-[1000] pointer-events-none">
            <Map className="w-12 h-12 text-slate-800 mb-3" />
            <p className="text-xs max-w-xs leading-relaxed uppercase tracking-wider">
              Awaiting query execution. Spatial risk overlays will map automatically on submit.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};
export default MapPanel;
