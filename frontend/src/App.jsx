import React, { useEffect, useState } from "react";
import RoadPriorityMap from "./components/Map/RoadPriorityMap";
import "./styles/dashboard.css";


function App() {
  const [priority, setPriority] = useState("");
  const [ward, setWard] = useState("");

  return (
    <div className="app">

      <header className="topbar">
        <div>
          <h1>Urban Problem Hotspot Engine</h1>
          <p>Municipal Road Priority Dashboard</p>
        </div>
      </header>


      <main className="dashboard">

        <section className="stats-grid">

          <div className="stat-card">
            <span>Total Complaints</span>
            <strong>1,811</strong>
          </div>

          <div className="stat-card">
            <span>Hotspots</span>
            <strong>367</strong>
          </div>

          <div className="stat-card">
            <span>Road Segments</span>
            <strong>14,225</strong>
          </div>

          <div className="stat-card">
            <span>Priority Roads</span>
            <strong>198</strong>
          </div>

        </section>


        <section className="controls">

          <div>
            <label>Priority</label>

            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
            >
              <option value="">All priorities</option>
              <option value="CRITICAL">Critical</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
            </select>
          </div>


          <div>
            <label>Ward</label>

            <input
              type="number"
              min="1"
              max="79"
              placeholder="All wards"
              value={ward}
              onChange={(e) => setWard(e.target.value)}
            />
          </div>


          <button
            className="clear-button"
            onClick={() => {
              setPriority("");
              setWard("");
            }}
          >
            Clear Filters
          </button>

        </section>


        <section className="map-section">

          <div className="section-header">
            <div>
              <h2>Road Priority Map</h2>
              <p>
                Real OSM road network linked to municipal complaints
              </p>
            </div>
          </div>


          <RoadPriorityMap
            priority={priority}
            ward={ward}
          />

        </section>

      </main>

    </div>
  );
}


export default App;