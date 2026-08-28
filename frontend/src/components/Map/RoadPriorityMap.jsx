import React, { useEffect, useState } from "react";
import {
  MapContainer,
  TileLayer,
  GeoJSON,
  Popup,
  useMap,
} from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

const API_URL = "http://127.0.0.1:8000";


const PRIORITY_COLORS = {
  CRITICAL: "#dc2626",
  HIGH: "#f97316",
  MEDIUM: "#eab308",
  LOW: "#22c55e",
};


function MapBounds({ features }) {
  const map = useMap();

  useEffect(() => {
    if (!features.length) return;

    const geoJsonLayer = L.geoJSON({
      type: "FeatureCollection",
      features,
    });

    const bounds = geoJsonLayer.getBounds();

    if (bounds.isValid()) {
      map.fitBounds(bounds, {
        padding: [30, 30],
      });
    }
  }, [features, map]);

  return null;
}


function RoadFeature(feature, layer) {
  if (!feature || !feature.properties) {
    return;
  }

  const properties = feature.properties;

  const color =
    PRIORITY_COLORS[properties.priority_level] || "#64748b";

  layer.setStyle({
    color,
    weight: properties.priority_level === "CRITICAL" ? 7 : 5,
    opacity: 0.85,
  });

  layer.bindPopup(`
    <div style="min-width:260px;font-family:Arial,sans-serif">
      <h3 style="margin:0 0 8px">
        ${properties.osm_name || properties.segment_name}
      </h3>

      <div style="
        display:inline-block;
        padding:4px 8px;
        border-radius:4px;
        background:${color};
        color:white;
        font-weight:bold;
        margin-bottom:10px;
      ">
        ${properties.priority_level}
      </div>

      <table style="width:100%;border-collapse:collapse">
        <tr>
          <td><b>Priority Score</b></td>
          <td>${properties.road_priority_score}</td>
        </tr>

        <tr>
          <td><b>Ward</b></td>
          <td>${properties.ward_number}</td>
        </tr>

        <tr>
          <td><b>Complaints</b></td>
          <td>${properties.complaint_count}</td>
        </tr>

        <tr>
          <td><b>Active Months</b></td>
          <td>${properties.active_months}</td>
        </tr>

        <tr>
          <td><b>Avg Severity</b></td>
          <td>${properties.avg_severity ?? "N/A"}/5</td>
        </tr>

        <tr>
          <td><b>Unresolved</b></td>
          <td>${properties.unresolved_count}</td>
        </tr>

        <tr>
          <td><b>Length</b></td>
          <td>${properties.length_m} m</td>
        </tr>
      </table>

      <p style="margin-top:10px">
        ${properties.explanation}
      </p>
    </div>
  `);
}


export default function RoadPriorityMap({
  priority = "",
  ward = "",
}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function loadRoads() {
      try {
        setLoading(true);
        setError(null);

        const params = new URLSearchParams();

        if (priority) {
          params.set("priority_level", priority);
        }

        if (ward) {
          params.set("ward_number", ward);
        }

        const query = params.toString();

        const response = await fetch(
          `${API_URL}/roads/map${query ? `?${query}` : ""}`
        );

        if (!response.ok) {
          throw new Error(
            `Backend returned HTTP ${response.status}`
          );
        }

        const geojson = await response.json();

        setData(geojson);
      } catch (err) {
        console.error(err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    loadRoads();
  }, [priority, ward]);


  if (loading) {
    return (
      <div className="map-status">
        Loading road network...
      </div>
    );
  }


  if (error) {
    return (
      <div className="map-status map-error">
        <strong>Unable to load road data.</strong>
        <br />
        {error}
      </div>
    );
  }


  const features = data?.features || [];


  return (
    <div className="road-map-wrapper">

      <MapContainer
        center={[23.1815, 79.9864]}
        zoom={12}
        scrollWheelZoom={true}
        className="road-map"
      >

        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        <MapBounds features={features} />

        {data && (
          <GeoJSON
            key={`${priority}-${ward}-${features.length}`}
            data={data}
            onEachFeature={RoadFeature}
          />
        )}

      </MapContainer>


      <div className="map-legend">

        <strong>Road Priority</strong>

        <div>
          <span
            className="legend-color"
            style={{
              background: PRIORITY_COLORS.CRITICAL,
            }}
          />
          CRITICAL
        </div>

        <div>
          <span
            className="legend-color"
            style={{
              background: PRIORITY_COLORS.HIGH,
            }}
          />
          HIGH
        </div>

        <div>
          <span
            className="legend-color"
            style={{
              background: PRIORITY_COLORS.MEDIUM,
            }}
          />
          MEDIUM
        </div>

        <div>
          <span
            className="legend-color"
            style={{
              background: PRIORITY_COLORS.LOW,
            }}
          />
          LOW
        </div>

      </div>


      <div className="map-count">
        {features.length} prioritized roads
      </div>

    </div>
  );
}