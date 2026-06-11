import React, { useRef, useEffect, useState } from 'react';
import L from 'leaflet';
import { Map, MapPin, TrendingUp } from 'lucide-react';
import { fetchForecast } from '../utils/api';
import type { ForecastData } from '../utils/api';

interface HeatmapFeature {
  type: string;
  geometry: {
    type: string;
    coordinates: [number, number]; // [lng, lat]
  };
  properties: {
    cluster_id: number;
    location_name: string;
    risk_score: number;
    crime_count: number;
    dominant_crime: string;
    severity: string;
    fir_ids: number[];
    date_range: string;
  };
}

interface HeatmapData {
  type: string;
  features: HeatmapFeature[];
}

interface MapPanelProps {
  heatmapData: HeatmapData | null;
  onHotspotClick: (followUpQuery: string) => void;
}

export const MapPanel: React.FC<MapPanelProps> = ({ heatmapData, onHotspotClick }) => {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);
  const markersGroupRef = useRef<L.FeatureGroup | null>(null);
  const forecastGroupRef = useRef<L.FeatureGroup | null>(null);
  const [showForecast, setShowForecast] = useState(false);
  const [forecastData, setForecastData] = useState<ForecastData | null>(null);
  const [forecastLoading, setForecastLoading] = useState(false);

  useEffect(() => {
    if (!mapContainerRef.current) return;

    // Initialize Leaflet map instance once
    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        zoomControl: false,
        attributionControl: false
      }).setView([12.9716, 77.5946], 11); // Default center on Bengaluru

      // Setup CartoDB Dark Matter tiles (premium dark UI look)
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19
      }).addTo(map);

      // Add Zoom Control at custom position
      L.control.zoom({
        position: 'bottomright'
      }).addTo(map);

      mapInstanceRef.current = map;
      markersGroupRef.current = L.featureGroup().addTo(map);
      forecastGroupRef.current = L.featureGroup().addTo(map);
    }

    return () => {
      // Keep map persisted between renders, clear only layers on destroy if necessary
    };
  }, []);

  useEffect(() => {
    if (!mapInstanceRef.current || !markersGroupRef.current) return;

    // Clear previous vector paths and circles
    markersGroupRef.current.clearLayers();

    if (!heatmapData || !heatmapData.features || heatmapData.features.length === 0) {
      // Recenter on Bengaluru if no features
      mapInstanceRef.current.setView([12.9716, 77.5946], 11);
      return;
    }

    const features = heatmapData.features;
    features.forEach((feature) => {
      const [lng, lat] = feature.geometry.coordinates;
      const props = feature.properties;

      // Color coding severity levels
      let color = '#ef4444'; // Rose/Red (High risk)
      if (props.severity === 'Amber' || props.severity === 'Medium') {
        color = '#f59e0b'; // Amber (Medium risk)
      } else if (props.severity === 'Low') {
        color = '#10b981'; // Emerald/Green (Low risk)
      }

      // Draw risk circle zone overlay
      const circle = L.circle([lat, lng], {
        radius: 350, // 350 meters radius
        color: color,
        fillColor: color,
        fillOpacity: 0.3,
        weight: 1.5
      });

      // Renders popup content container DOM element
      const popupContent = document.createElement('div');
      popupContent.className = 'p-1.5 text-xs font-sans text-slate-100 flex flex-col gap-1.5 min-w-[200px] bg-slate-900';
      popupContent.innerHTML = `
        <div class="font-bold border-b border-slate-700 pb-1 text-cyan-400 text-sm uppercase tracking-wide">${props.location_name}</div>
        <div class="flex justify-between"><span class="text-slate-400 font-semibold">Risk Rating:</span> <span class="font-bold text-amber-400">${props.risk_score}</span></div>
        <div class="flex justify-between"><span class="text-slate-400 font-semibold">Incident Count:</span> <span class="font-bold text-slate-200">${props.crime_count}</span></div>
        <div class="flex justify-between"><span class="text-slate-400 font-semibold">Primary Crime:</span> <span class="font-bold text-slate-200">${props.dominant_crime}</span></div>
        <div class="text-[10px] text-slate-400 italic mt-1">Logged: ${props.date_range}</div>
        <button id="query-hotspot-${props.cluster_id}" class="mt-2 w-full bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold py-1.5 px-2 rounded cursor-pointer text-center text-[10px] uppercase tracking-wider transition-colors duration-200">
          Run Contextual Query
        </button>
      `;

      // Mount follow-up contextual query handler
      popupContent.querySelector('button')?.addEventListener('click', () => {
        const followUp = `Show all ${props.dominant_crime.toLowerCase().replace(' ', ' ')} cases near ${props.location_name.split(' ')[0]}`;
        onHotspotClick(followUp);
      });

      circle.bindPopup(popupContent);
      markersGroupRef.current?.addLayer(circle);
    });

    // Fit map bounds to encompass all visual hotspots
    try {
      const bounds = markersGroupRef.current.getBounds();
      if (bounds.isValid()) {
        mapInstanceRef.current.fitBounds(bounds, { padding: [40, 40] });
      }
    } catch (e) {
      console.error('Error fitting map bounds', e);
    }

  }, [heatmapData, onHotspotClick]);

  // Fetch predicted hotspots when the forecast overlay is enabled
  useEffect(() => {
    if (!showForecast || forecastData) return;
    setForecastLoading(true);
    fetchForecast()
      .then((data) => setForecastData(data))
      .catch((e) => console.error('Forecast fetch failed', e))
      .finally(() => setForecastLoading(false));
  }, [showForecast, forecastData]);

  // Render forecast overlay as dashed trend-colored prediction zones
  useEffect(() => {
    if (!mapInstanceRef.current || !forecastGroupRef.current) return;
    forecastGroupRef.current.clearLayers();
    if (!showForecast || !forecastData) return;

    forecastData.features.forEach((feature) => {
      const [lng, lat] = feature.geometry.coordinates;
      const props = feature.properties;

      let color = '#a855f7'; // Purple (Rising prediction)
      if (props.trend === 'Stable') {
        color = '#38bdf8'; // Sky blue
      } else if (props.trend === 'Declining') {
        color = '#64748b'; // Slate
      }

      const circle = L.circle([lat, lng], {
        radius: 450,
        color: color,
        fillColor: color,
        fillOpacity: 0.12,
        weight: 2,
        dashArray: '6 6'
      });

      circle.bindPopup(`
        <div class="p-1.5 text-xs font-sans text-slate-100 flex flex-col gap-1.5 min-w-[200px] bg-slate-900">
          <div class="font-bold border-b border-slate-700 pb-1 text-purple-400 text-sm uppercase tracking-wide">Forecast: ${props.location_name}</div>
          <div class="flex justify-between"><span class="text-slate-400 font-semibold">Trend (next 7d):</span> <span class="font-bold text-slate-200">${props.trend}</span></div>
          <div class="flex justify-between"><span class="text-slate-400 font-semibold">Predicted / week:</span> <span class="font-bold text-amber-400">${props.predicted_weekly_incidents}</span></div>
          <div class="flex justify-between"><span class="text-slate-400 font-semibold">Historical avg:</span> <span class="font-bold text-slate-200">${props.historical_weekly_avg}</span></div>
          <div class="flex justify-between"><span class="text-slate-400 font-semibold">Primary Crime:</span> <span class="font-bold text-slate-200">${props.dominant_crime}</span></div>
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
            className={`text-[10px] font-bold uppercase tracking-wider flex items-center gap-1 px-2 py-1 rounded border transition-colors duration-200 ${
              showForecast
                ? 'bg-purple-500/20 border-purple-500 text-purple-300'
                : 'bg-slate-900/60 border-slate-700 text-slate-400 hover:text-slate-200'
            }`}
            title="Toggle predicted hotspot overlay (next 7 days)"
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
        
        {(!heatmapData || heatmapData.features.length === 0) && (
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
