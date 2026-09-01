import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./App.css";

// API bridge for local development and Vercel production.
const LOCAL_API = "http://127.0.0.1:8000";
const CONFIGURED_API = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const nativeFetch = window.fetch.bind(window);

function jsonResponse(payload, status = 200) {
  return new Response(JSON.stringify(payload), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const demoPriority = [
  {
    ward_number: 1,
    category: "Waterlogging",
    location: "Central Jabalpur",
    complaint_count: 42,
    persistence_score: 91,
    priority_score: 92,
    severity: "Critical",
  },
  {
    ward_number: 2,
    category: "Potholes",
    location: "Adhartal Road",
    complaint_count: 36,
    persistence_score: 83,
    priority_score: 88,
    severity: "Critical",
  },
  {
    ward_number: 3,
    category: "Road Damage",
    location: "Jabalpur",
    complaint_count: 31,
    persistence_score: 72,
    priority_score: 80,
    severity: "Critical",
  },
  {
    ward_number: 4,
    category: "Drainage",
    location: "South Jabalpur",
    complaint_count: 29,
    persistence_score: 78,
    priority_score: 86,
    severity: "Critical",
  },
  {
    ward_number: 5,
    category: "Garbage Collection",
    location: "Jabalpur",
    complaint_count: 25,
    persistence_score: 69,
    priority_score: 74,
    severity: "High",
  },
];

const demoPredictions = [
  {
    ward_number: 1,
    category: "Waterlogging",
    prediction_probability: 92,
  },
  {
    ward_number: 4,
    category: "Drainage",
    prediction_probability: 86,
  },
  {
    ward_number: 2,
    category: "Potholes",
    prediction_probability: 81,
  },
  {
    ward_number: 3,
    category: "Road Damage",
    prediction_probability: 76,
  },
  {
    ward_number: 5,
    category: "Garbage Collection",
    prediction_probability: 68,
  },
];

window.fetch = (input, init) => {
  const url = typeof input === "string" ? input : input?.url || "";

  if (!url.startsWith(LOCAL_API)) {
    return nativeFetch(input, init);
  }

  const endpoint = url.slice(LOCAL_API.length) || "/";

  // Local development → real FastAPI backend.
  if (import.meta.env.DEV) {
    return nativeFetch(input, init);
  }

  // Production → deployed FastAPI backend when configured.
  if (CONFIGURED_API) {
    return nativeFetch(`${CONFIGURED_API}${endpoint}`, init);
  }

  // Production fallback until backend is deployed.
  if (endpoint.startsWith("/priority")) {
    return Promise.resolve(jsonResponse(demoPriority));
  }

  if (endpoint.startsWith("/predictions")) {
    return Promise.resolve(
      jsonResponse({
        predictions: demoPredictions,
      })
    );
  }

  return Promise.resolve(
    jsonResponse({
      status: "ok",
      items: [],
    })
  );
};

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);