import React, { useEffect, useMemo, useRef, useState } from "react";
import {
  BrowserRouter,
  Routes,
  Route,
  NavLink,
  useNavigate,
  useParams,
  Navigate,
} from "react-router-dom";
import "leaflet/dist/leaflet.css";
import { MapContainer, TileLayer, Marker, Popup, CircleMarker, useMap } from "react-leaflet";
import L from "leaflet";
import { CITY, categories, hotspots as cityHotspots } from "./Data/jabalpurData";
import "./App.css";

const DEMO_USERS = [
  { email: "citizen@urbannova.demo", password: "citizen123", role: "citizen", name: "Demo Citizen" },
  { email: "officer@urbannova.demo", password: "officer123", role: "officer", name: "Municipal Officer" },
];

const departments = ["Road & Infrastructure", "Drainage & Sewerage", "Sanitation", "Street Lighting", "Water Supply"];
const statuses = ["Submitted", "Under Review", "Assigned", "In Progress", "Resolved"];
const WARDS = Array.from({ length: 79 }, (_, i) => `Ward ${i + 1}`);

const DEMO_SEED_VERSION = "v3-448";
const DEMO_PHOTO_COLORS = ["#dbeafe", "#dcfce7", "#fef3c7", "#fee2e2", "#f3e8ff", "#e0f2fe"];
function demoEvidenceDataUrl(category, ward, kind = "Citizen evidence") {
  const bg = DEMO_PHOTO_COLORS[(Number(ward.replace(/\D/g, "")) || 1) % DEMO_PHOTO_COLORS.length];
  const safe = String(category).replace(/[<>&]/g, "");
  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="640" height="400"><rect width="100%" height="100%" fill="${bg}"/><rect x="24" y="24" width="592" height="352" rx="20" fill="white" opacity=".82"/><text x="40" y="115" font-family="Arial" font-size="28" font-weight="700" fill="#0f172a">UrbanNova Demo</text><text x="40" y="165" font-family="Arial" font-size="24" fill="#334155">${safe}</text><text x="40" y="205" font-family="Arial" font-size="20" fill="#64748b">${ward}</text><text x="40" y="320" font-family="Arial" font-size="18" fill="#475569">${kind} · Demo image</text></svg>`)}`;
}
const demoCategoryDescriptions = {
  "Garbage Collection": ["Garbage accumulation near residential lane.", "Missed waste collection at community point.", "Overflowing garbage bins need urgent pickup."],
  "Drainage": ["Blocked drain causing standing water.", "Drain overflow reported after rainfall.", "Open drain needs cleaning and inspection."],
  "Waterlogging": ["Waterlogging blocking a residential road.", "Standing water affecting pedestrian movement.", "Low-lying road remains flooded after rain."],
  "Road Damage": ["Damaged road surface near market.", "Cracked carriageway requires repair.", "Uneven road surface creating traffic risk."],
  "Potholes": ["Multiple deep potholes affecting traffic.", "Large potholes reported near school.", "Potholes causing unsafe two-wheeler movement."],
  "Street Lighting": ["Several street lights are not working.", "Street light outage reported on main road.", "Dark stretch requires lighting inspection."],
  "Water Supply": ["Low water pressure reported by residents.", "Irregular water supply in the locality.", "Water supply interruption reported by residents."],
  "Sewerage": ["Sewer line overflow reported.", "Sewer blockage causing foul smell.", "Damaged sewer connection needs attention."]
};
const demoDepartments = {
  "Garbage Collection": "Sanitation", "Drainage": "Drainage & Sewerage", "Waterlogging": "Drainage & Sewerage",
  "Road Damage": "Road & Infrastructure", "Potholes": "Road & Infrastructure", "Street Lighting": "Street Lighting",
  "Water Supply": "Water Supply", "Sewerage": "Drainage & Sewerage"
};
function buildDemoComplaints() {
  const rows = [];
  let n = 1;
  categories.forEach((category, catIndex) => {
    for (let i = 0; i < 56; i++) {
      const wardNo = ((catIndex * 9 + i * 7) % 79) + 1;
      const ward = `Ward ${wardNo}`;
      const desc = demoCategoryDescriptions[category][i % demoCategoryDescriptions[category].length];
      const criticalWords = i % 11 === 0 ? " severe and urgent" : i % 7 === 0 ? " blocked" : "";
      const ai = severityScore(category, desc + criticalWords);
      const statusCycle = ["Submitted", "Under Review", "Assigned", "In Progress", "Resolved", "Submitted", "In Progress", "Under Review"];
      const status = statusCycle[(i + catIndex) % statusCycle.length];
      const lat = 23.1815 + ((wardNo % 10) - 5) * 0.006 + (catIndex % 3) * 0.001;
      const lng = 79.9864 + (((wardNo * 3) % 11) - 5) * 0.006 + (catIndex % 2) * 0.001;
      const created = new Date(Date.now() - ((catIndex * 56 + i + 1) * 3 * 3600 * 1000)).toISOString();
      rows.push({
        id: `DEMO-${String(n).padStart(4, "0")}`, ward, category, description: desc + criticalWords,
        location: `${ward}, Jabalpur`, lat, lng, aadhaar: "", mobile: "", aiScore: ai.score, severity: ai.severity, status,
        createdAt: created, citizenEmail: "demo@urbannova.local", department: demoDepartments[category], expectedResolution: status === "Resolved" ? "Completed" : "Not assigned",
        updates: status === "Resolved" ? [{ text: "Work completed and verified with after-work evidence.", at: new Date().toLocaleString() }] : [],
        photo: demoEvidenceDataUrl(category, ward, "Citizen evidence"), photoName: "Demo citizen evidence",
        resolutionPhoto: status === "Resolved" ? demoEvidenceDataUrl(category, ward, "Resolution evidence") : "",
        resolutionPhotoName: status === "Resolved" ? "Demo resolution evidence" : "", resolvedAt: status === "Resolved" ? new Date(created).toISOString() : "", demo: true
      });
      n++;
    }
  });
  return rows;
}
const DEMO_COMPLAINTS = buildDemoComplaints();
const noticesDefault = [
  { id: "N-001", title: "Pre-Monsoon Drain Cleaning Drive", date: "27 Aug 2026", body: "Drain cleaning and desilting work is being intensified in identified waterlogging-prone areas of Jabalpur before the monsoon spell.", department: "Drainage & Sewerage" },
  { id: "N-002", title: "Temporary Traffic Advisory — Wright Town", date: "26 Aug 2026", body: "Citizens are advised to allow additional travel time near selected road repair zones. Please follow temporary barricading and diversion signs.", department: "Road & Infrastructure" },
  { id: "N-003", title: "Citizen Complaint Response Update", date: "24 Aug 2026", body: "Residents can continue reporting civic issues through UrbanNova. Critical complaints are reviewed on priority by the municipal control team.", department: "Citizen Services" }
];
function loadNotices() { try { return JSON.parse(localStorage.getItem("urbannova_notices") || JSON.stringify(noticesDefault)); } catch { return noticesDefault; } }
function saveNotices(items) { localStorage.setItem("urbannova_notices", JSON.stringify(items)); }

const defaultPoints = [
  { id: "H01", lat: 23.1815, lng: 79.9864, title: "Garbage → Drainage → Waterlogging", severity: "Critical", score: 92, category: "Waterlogging", location: "Central Jabalpur" },
  { id: "H02", lat: 23.1677, lng: 79.9330, title: "Pothole / Damaged Road", severity: "High", score: 88, category: "Potholes", location: "Adhartal Road" },
  { id: "H03", lat: 23.1900, lng: 79.9500, title: "Urban Problem Hotspot", severity: "High", score: 80, category: "Road Damage", location: "Jabalpur" },
  { id: "H10", lat: 23.1590, lng: 79.9860, title: "Drainage → Waterlogging → Damaged Road", severity: "High", score: 86, category: "Drainage", location: "South Jabalpur" },
];

function loadComplaints() {
  try {
    const stored = JSON.parse(localStorage.getItem("urbannova_complaints") || "[]");
    const seeded = localStorage.getItem("urbannova_demo_seed_version");
    if (seeded !== DEMO_SEED_VERSION) {
      const real = Array.isArray(stored) ? stored.filter(c => !c.demo) : [];
      const merged = [...real, ...DEMO_COMPLAINTS];
      localStorage.setItem("urbannova_complaints", JSON.stringify(merged));
      localStorage.setItem("urbannova_demo_seed_version", DEMO_SEED_VERSION);
      return merged;
    }
    return Array.isArray(stored) ? stored : [];
  } catch { return DEMO_COMPLAINTS; }
}
function saveComplaints(items) { localStorage.setItem("urbannova_complaints", JSON.stringify(items)); }
function loadSession() {
  try { return JSON.parse(localStorage.getItem("urbannova_session") || "null"); } catch { return null; }
}
function severityScore(category, description) {
  const text = `${category} ${description}`.toLowerCase();
  let score = 35;
  const weights = {
    critical: 30, dangerous: 25, blocked: 22, accident: 28, "life risk": 30,
    severe: 22, emergency: 28, "completely blocked": 25, flooded: 20,
    "major pothole": 18, overflow: 16, "health risk": 20, "traffic": 10,
  };
  Object.entries(weights).forEach(([word, value]) => { if (text.includes(word)) score += value; });
  if (["Waterlogging", "Drainage", "Sewerage"].includes(category)) score += 8;
  if (["Potholes", "Road Damage"].includes(category)) score += 5;
  score = Math.min(100, score);
  const severity = score >= 80 ? "Critical" : score >= 60 ? "High" : score >= 40 ? "Medium" : "Low";
  return { score, severity };
}
function markerIcon(severity) {
  const color = severity === "Critical" ? "#dc2626" : severity === "High" ? "#f97316" : severity === "Medium" ? "#eab308" : "#16a34a";
  return L.divIcon({ className: "problem-marker-wrap", html: `<div class="problem-marker" style="background:${color}"></div>`, iconSize: [24, 24], iconAnchor: [12, 12] });
}

function GoogleMap({ points, onPointClick }) {
  const [ready, setReady] = useState(false);
  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
  useEffect(() => {
    if (!apiKey) return;
    if (window.google?.maps) { setReady(true); return; }
    const existing = document.querySelector('script[data-google-maps="urbannova"]');
    if (existing) { existing.addEventListener("load", () => setReady(true)); return; }
    const script = document.createElement("script");
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}`;
    script.async = true; script.defer = true; script.dataset.googleMaps = "urbannova";
    script.onload = () => setReady(true); document.head.appendChild(script);
  }, [apiKey]);
  useEffect(() => {
    if (!ready) return;
    const el = document.getElementById("google-map");
    if (!el) return;
    const map = new window.google.maps.Map(el, { center: { lat: CITY.center[0], lng: CITY.center[1] }, zoom: 12, mapTypeControl: true, streetViewControl: false, fullscreenControl: true });
    points.forEach((p) => {
      const marker = new window.google.maps.Marker({ position: { lat: p.lat, lng: p.lng }, map, title: `${p.title} — ${p.severity}` });
      const info = new window.google.maps.InfoWindow({ content: `<div style="padding:8px"><b>${p.title}</b><br/>${p.location}<br/>Severity: ${p.severity}<br/>Score: ${p.score}/100</div>` });
      marker.addListener("click", () => { info.open({ map, anchor: marker }); onPointClick?.(p); });
    });
  }, [ready, points, onPointClick]);
  if (!apiKey) return <LeafletMap points={points} onPointClick={onPointClick} />;
  return ready ? <div id="google-map" className="real-map" /> : <div className="map-loading">Loading Google Maps…</div>;
}
function LeafletMap({ points, onPointClick }) {
  return <MapContainer center={CITY.center} zoom={12} scrollWheelZoom className="real-map">
    <TileLayer attribution='&copy; OpenStreetMap contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
    {points.map(p => <Marker key={p.id} position={[p.lat, p.lng]} icon={markerIcon(p.severity)} eventHandlers={{ click: () => onPointClick?.(p) }}><Popup><b>{p.title}</b><br />{p.location}<br />Severity: {p.severity}<br />Score: {p.score}/100</Popup></Marker>)}
  </MapContainer>;
}

function Protected({ role, children }) { const session = loadSession(); return session?.role === role ? children : <Navigate to="/login" replace />; }

function Layout({ children, session, logout }) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const items = session?.role === "officer" ? [
    ["/officer", "▦", "Officer Dashboard"], ["/complaints", "＋", "Complaints"], ["/ward-analytics", "▥", "Ward Analytics"], ["/hotspots", "⌖", "Hotspots"], ["/relationships", "⌘", "Relationships"], ["/priority", "↑", "Priority Ranking"], ["/predictor", "◉", "Risk Predictor"], ["/notices", "▣", "Notices"], ["/about", "ⓘ", "About"], ["/help", "?", "Help Desk"]
  ] : [["/citizen", "⌂", "Citizen Home"], ["/complaints", "＋", "Report Complaint"], ["/my-complaints", "✓", "My Complaints"], ["/hotspots", "⌖", "City Hotspots"], ["/notices", "▣", "Notices"], ["/about", "ⓘ", "About"], ["/help", "?", "Help Desk"]];
  return <div className="app-shell"><aside className={`sidebar ${sidebarOpen ? "" : "collapsed"}`}><div className="brand"><div className="brand-icon">U</div>{sidebarOpen && <div><div className="brand-title">UrbanNova</div><div className="brand-subtitle">Jabalpur Problem Hotspot Engine</div></div>}</div><div className="sidebar-section">{sidebarOpen && <div className="section-label">{session?.role === "officer" ? "MUNICIPAL CONTROL" : "CITIZEN SERVICES"}</div>}{items.map(([path, icon, label]) => <NavLink key={path} to={path} className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}><span className="nav-icon">{icon}</span>{sidebarOpen && <span>{label}</span>}</NavLink>)}</div>{sidebarOpen && <div className="sidebar-bottom"><div className="system-status"><span className="status-dot" /><div><strong>System Online</strong><small>Jabalpur · Live</small></div></div><div className="municipality-card"><div className="avatar">{session?.role === "officer" ? "MO" : "C"}</div><div><strong>{session?.name}</strong><small>{session?.role === "officer" ? "Municipal Officer" : "Citizen"}</small></div></div><button className="logout-button" onClick={logout}>Log out</button></div>}</aside><main className="main-content"><header className="topbar"><button className="menu-button" onClick={() => setSidebarOpen(!sidebarOpen)}>☰</button><div className="topbar-title"><span className="live-dot" /> LIVE MUNICIPAL INTELLIGENCE</div><div className="topbar-right"><span>Jabalpur, MP</span><div className="profile-circle">{session?.role === "officer" ? "MO" : "C"}</div></div></header><div className="page-content">{children}</div></main></div>;
}
function PageHeader({ eyebrow, title, description, action }) { return <div className="page-header"><div>{eyebrow && <div className="eyebrow">{eyebrow}</div>}<h1>{title}</h1>{description && <p>{description}</p>}</div>{action && <div>{action}</div>}</div>; }
function SeverityBadge({ severity }) { return <span className={`severity-badge ${severity.toLowerCase()}`}><span className="badge-dot" />{severity}</span>; }
function StatCard({ icon, label, value, change, type }) { return <div className="stat-card"><div className={`stat-icon ${type || ""}`}>{icon}</div><div className="stat-info"><span>{label}</span><strong>{value}</strong>{change && <small>{change}</small>}</div></div>; }

function WardGraphModal({ ward, complaints, onClose }) {
  if (!ward) return null;

  const wardComplaints = complaints.filter(c => c.ward === ward);
  const categoryCounts = categories
    .map(category => ({
      category,
      count: wardComplaints.filter(c => c.category === category).length
    }))
    .filter(x => x.count > 0)
    .sort((a, b) => b.count - a.count);

  const maxCategory = Math.max(...categoryCounts.map(x => x.count), 1);
  const resolved = wardComplaints.filter(c => c.status === "Resolved").length;
  const active = wardComplaints.length - resolved;
  const topProblem = categoryCounts[0]?.category || "No complaints";

  return (
    <div className="camera-modal-backdrop" onClick={onClose}>
      <div className="camera-modal ward-graph-modal" onClick={e => e.stopPropagation()}>
        <div className="camera-modal-head">
          <div>
            <span className="eyebrow">WARD INTELLIGENCE</span>
            <h2>{ward}</h2>
            <p>Complaint distribution for the selected ward.</p>
          </div>
          <button className="secondary-button" onClick={onClose}>Close</button>
        </div>

        <div className="stats-grid complaint-stats">
          <StatCard icon="◎" label="Total Complaints" value={wardComplaints.length} change="Selected ward" type="blue" />
          <StatCard icon="!" label="Active" value={active} change="Needs attention" type="orange" />
          <StatCard icon="✓" label="Resolved" value={resolved} change="Completed" type="green" />
          <StatCard icon="TOP" label="Top Problem" value={topProblem} change="Highest volume" type="red" />
        </div>

        <section className="panel ward-graph-card">
          <div className="panel-header">
            <div>
              <h2>Problems by category</h2>
              <p>Tap a map complaint marker to inspect its ward.</p>
            </div>
          </div>

          {categoryCounts.length === 0 ? (
            <div className="empty-state">
              <h3>No complaint data for this ward</h3>
              <p>The selected marker does not have matching ward complaint records.</p>
            </div>
          ) : (
            <div className="category-bar-chart">
              {categoryCounts.map(x => (
                <div className="category-bar-row" key={x.category}>
                  <div className="category-bar-label">
                    <strong>{x.category}</strong>
                    <span>{x.count}</span>
                  </div>
                  <div className="ward-bar-track">
                    <div
                      className="category-bar-fill"
                      style={{ width: `${Math.max((x.count / maxCategory) * 100, 4)}%` }}
                    >
                      <span>{x.count}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}

function Dashboard({ officer = false }) {
  const navigate = useNavigate(); const complaints = loadComplaints(); const resolved = complaints.filter(c => c.status === "Resolved").length;
  const points = useMemo(() => [...defaultPoints, ...complaints.filter(c => c.lat && c.lng).map(c => ({ id: c.id, lat: c.lat, lng: c.lng, title: c.category, severity: c.severity, score: c.aiScore, location: c.location, ward: c.ward }))], [complaints]);
  const [selectedWard, setSelectedWard] = useState("");
  return <><PageHeader eyebrow={officer ? "MUNICIPAL CONTROL" : "CITIZEN VIEW"} title={officer ? "Jabalpur Municipal Intelligence" : "Jabalpur Urban Problem Map"} description={officer ? "Monitor complaints, hotspots and interventions across Jabalpur." : "See where problems are concentrated and report issues directly."} action={!officer && <button className="primary-button" onClick={() => navigate("/complaints")}>+ Report Complaint</button>} /><div className="stats-grid"><StatCard icon="◎" label="Total Complaints" value={complaints.length} change="Citizen reports" type="blue" /><StatCard icon="⌖" label="Active Hotspots" value={defaultPoints.length} change="Across Jabalpur" type="orange" /><StatCard icon="!" label="Critical Hotspots" value={defaultPoints.filter(p => p.severity === "Critical").length} change="Immediate attention" type="red" /><StatCard icon="✓" label="Resolved Complaints" value={resolved} change="Officer updates" type="green" /></div><section className="panel map-panel"><div className="panel-header"><div><h2>Jabalpur Problem Map</h2><p>Colored markers show different problem severity. Click a marker for details.</p></div><div className="map-legend-inline"><span>🔴 Critical</span><span>🟠 High</span><span>🟡 Medium</span><span>🟢 Low</span></div></div><GoogleMap
    points={points}
    onPointClick={p => {
      if (p.ward) setSelectedWard(p.ward);
      else if (p.id) navigate(`/hotspots/${p.id}`);
    }}
  /></section>{selectedWard && <WardGraphModal ward={selectedWard} complaints={complaints} onClose={() => setSelectedWard("")} />}</>;
}

function ComplaintForm({ session }) {
  const [form, setForm] = useState({ category: "", description: "", ward: "", location: "", lat: null, lng: null, aadhaar: "", mobile: "" });
  const [photo, setPhoto] = useState(""); const [photoName, setPhotoName] = useState("");
  const [otp, setOtp] = useState(""); const [otpSent, setOtpSent] = useState(false);
  const [verified, setVerified] = useState(false); const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false); const [locationReady, setLocationReady] = useState(false);
  const [cameraError, setCameraError] = useState(""); const [cameraReady, setCameraReady] = useState(false);
  const videoRef = useRef(null); const streamRef = useRef(null);
  const ai = severityScore(form.category, form.description);

  useEffect(() => {
    let cancelled = false;
    async function startCamera() {
      if (!navigator.mediaDevices?.getUserMedia) { setCameraError("Live camera access is not supported by this browser."); return; }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false });
        if (cancelled) { stream.getTracks().forEach(t => t.stop()); return; }
        streamRef.current = stream;
        if (videoRef.current) { videoRef.current.srcObject = stream; await videoRef.current.play(); }
        setCameraReady(true); setCameraError("");
      } catch (err) { setCameraError("Camera permission is required. Please allow camera access and try again."); }
    }
    if (session?.role === "citizen") startCamera();
    return () => { cancelled = true; streamRef.current?.getTracks().forEach(t => t.stop()); streamRef.current = null; };
  }, [session?.role]);

  function capturePhoto() {
    const video = videoRef.current;
    if (!video || video.readyState < 2) { alert("Camera is not ready yet."); return; }
    const canvas = document.createElement("canvas");
    canvas.width = video.videoWidth || 1280; canvas.height = video.videoHeight || 720;
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    setPhoto(canvas.toDataURL("image/jpeg", 0.82)); setPhotoName("Live camera capture");
  }
  function locate() {
    if (!navigator.geolocation) { alert("GPS is not available in this browser."); return; }
    setBusy(true);
    navigator.geolocation.getCurrentPosition(pos => {
      setForm(f => ({ ...f, lat: pos.coords.latitude, lng: pos.coords.longitude, location: `${pos.coords.latitude.toFixed(5)}, ${pos.coords.longitude.toFixed(5)}` }));
      setLocationReady(true); setBusy(false);
    }, () => { alert("Location permission is required. Complaint location cannot be entered manually."); setBusy(false); }, { enableHighAccuracy: true, timeout: 10000 });
  }
  function sendOtp() {
    if (!/^\d{10}$/.test(form.mobile)) { alert("Enter a valid 10-digit mobile number."); return; }
    setOtpSent(true); setVerified(false); alert("Demo OTP: 123456 (connect an SMS provider for real OTP delivery)");
  }
  function verifyOtp() { if (otp === "123456") { setVerified(true); alert("Mobile number verified."); } else alert("Invalid demo OTP. Use 123456."); }
  function submit(e) {
    e.preventDefault();
    if (!form.category || !form.description || !form.ward || !locationReady || form.lat === null || form.lng === null) { alert("Please fill all required fields and capture live GPS location."); return; }
    if (!photo) { alert("A live camera photo is mandatory."); return; }
    if (!/^\d{12}$/.test(form.aadhaar)) { alert("Enter a valid 12-digit Aadhaar number."); return; }
    if (!/^\d{10}$/.test(form.mobile)) { alert("Enter a valid 10-digit mobile number."); return; }
    if (!verified) { alert("Verify the mobile number with OTP before submitting."); return; }
    const recent = loadComplaints().find(c => c.citizenEmail === session?.email && c.category === form.category && Date.now() - new Date(c.createdAt).getTime() < 86400000);
    if (recent) { alert(`You already submitted a ${form.category} complaint in the last 24 hours.`); return; }
    const item = { id: `CMP-${Date.now().toString().slice(-6)}`, ...form, photo, photoName, aiScore: ai.score, severity: ai.severity, status: "Submitted", createdAt: new Date().toISOString(), citizenEmail: session?.email || "citizen@urbannova.demo", department: "Not assigned", expectedResolution: "Not assigned", updates: [], resolutionPhoto: "" };
    saveComplaints([item, ...loadComplaints()]); setResult(item);
    setForm({ category: "", description: "", ward: "", location: "", lat: null, lng: null, aadhaar: "", mobile: "" });
    setPhoto(""); setPhotoName(""); setOtp(""); setOtpSent(false); setVerified(false); setLocationReady(false);
  }
  if (session?.role !== "citizen") return <OfficerComplaints />;

  if (result) return <div className="success-screen"><div className="success-icon">✓</div><h1>Complaint Submitted</h1><p>Your complaint has entered the municipal workflow.</p><div className="ai-result"><span>AI DETECTED SEVERITY</span><strong>{result.severity} · {result.aiScore}/100</strong><small>Complaint ID: {result.id}</small></div><button className="primary-button" onClick={() => setResult(null)}>Submit Another</button></div>;
  return <><PageHeader eyebrow="CITIZEN SERVICES" title="Report an Urban Problem" description="UrbanNova uses live evidence, live GPS and a demo AI severity layer to register civic complaints." />
    <div className="complaint-layout"><section className="panel complaint-form-panel"><form onSubmit={submit}>
      <div className="form-section-title"><span>01</span> Problem Details</div>
      <div className="form-group"><label>Problem Category <span className="required-mark">*</span></label><select required value={form.category} onChange={e => setForm({ ...form, category: e.target.value })}><option value="">Select category</option>{categories.map(c => <option key={c}>{c}</option>)}</select></div>
      <div className="form-group"><label>Description <span className="required-mark">*</span></label><textarea required placeholder="Example: severe waterlogging has blocked traffic for 3 hours..." value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} /></div>
      <div className="ai-live"><div><span>AI SEVERITY ASSESSMENT</span><strong>{form.description || form.category ? `${ai.severity} · ${ai.score}/100` : "Waiting for complaint details"}</strong></div><small>Frontend prediction demo · ready for backend AI integration</small></div>
      <div className="form-group"><label>Ward Number <span className="required-mark">*</span></label><select required value={form.ward} onChange={e => setForm({ ...form, ward: e.target.value })}><option value="">Select your ward</option>{WARDS.map(w => <option key={w}>{w}</option>)}</select><small className="field-help">Select the ward where the issue is located.</small></div>
      <div className="form-section-title"><span>02</span> Live Location</div>
      <div className="live-location-box"><div><strong>{locationReady ? "✓ Live location captured" : "Location required"}</strong><span>{form.location || "Your complaint must be submitted from your current GPS position."}</span></div><button type="button" className="location-button" onClick={locate}>{busy ? "Detecting…" : locationReady ? "Refresh live location" : "◎ Capture my live location"}</button></div>
      <div className="form-section-title"><span>03</span> Live Camera Evidence</div>
      <div className="camera-box">
        <video ref={videoRef} className="camera-preview" playsInline muted autoPlay aria-label="Live camera preview" />
        <div className="camera-status">{cameraError || (!cameraReady ? "Starting camera…" : "Camera live — gallery upload is disabled")}</div>
        <button type="button" className="primary-button camera-capture-button" onClick={capturePhoto} disabled={!cameraReady}>◉ Capture Photo</button>
      </div>
      {photo && <div className="captured-photo"><img className="evidence-preview" src={photo} alt="Captured complaint evidence" /><span>✓ {photoName}</span></div>}
      <div className="form-section-title"><span>04</span> Citizen Verification</div>
      <div className="form-row">
        <div className="form-group"><label>Aadhaar Number <span className="required-mark">*</span></label><input required inputMode="numeric" maxLength="12" placeholder="12-digit Aadhaar" value={form.aadhaar} onChange={e => setForm({ ...form, aadhaar: e.target.value.replace(/\D/g, "") })} /></div>
        <div className="form-group"><label>Mobile Number <span className="required-mark">*</span></label><input required inputMode="numeric" maxLength="10" placeholder="10-digit mobile" value={form.mobile} onChange={e => setForm({ ...form, mobile: e.target.value.replace(/\D/g, "") })} /></div>
      </div>
      <div className="otp-row"><button type="button" className="secondary-button" onClick={sendOtp}>Send OTP</button>{otpSent && <><input required inputMode="numeric" maxLength="6" placeholder="Demo OTP" value={otp} onChange={e => setOtp(e.target.value.replace(/\D/g, ""))} /><button type="button" className="secondary-button" onClick={verifyOtp}>{verified ? "✓ Verified" : "Verify OTP"}</button></>}</div>
      <small className="security-note">Fields marked <b className="required-mark">*</b> are required. Demo OTP is 123456. Aadhaar is validated for format only and should be securely handled by a backend in production.</small>
      <button className="submit-button" type="submit">Submit Verified Complaint →</button>
    </form></section><aside className="complaint-info"><div className="info-card blue-info"><div className="info-card-icon">AI</div><h3>How severity works</h3><p>The demo model considers category and words such as severe, blocked, dangerous, overflow, accident, traffic and health risk.</p></div><div className="process-card"><h3>Municipal workflow</h3>{["Live complaint recorded", "AI severity detected", "Officer reviews & assigns", "Work completed + after photo", "Resolution verified"].map((x, i) => <div className="process-step" key={x}><span>{i + 1}</span><div><strong>{x}</strong></div></div>)}</div></aside></div></>;
}

function OfficerComplaints() {
  const [items, setItems] = useState(loadComplaints());
  const [search, setSearch] = useState(""); const [category, setCategory] = useState("All");
  const [status, setStatus] = useState("All"); const [severity, setSeverity] = useState("All");
  const [department, setDepartment] = useState("All"); const [sort, setSort] = useState("newest");

  useEffect(() => { const refresh = () => setItems(loadComplaints()); window.addEventListener("storage", refresh); return () => window.removeEventListener("storage", refresh); }, []);
  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return [...items].filter(c => {
      const text = [c.id, c.category, c.description, c.location, c.citizenEmail].join(" ").toLowerCase();
      return (!q || text.includes(q)) && (category === "All" || c.category === category) && (status === "All" || c.status === status) && (severity === "All" || c.severity === severity) && (department === "All" || c.department === department);
    }).sort((a, b) => {
      if (sort === "oldest") return new Date(a.createdAt) - new Date(b.createdAt);
      if (sort === "severity") return (b.aiScore || 0) - (a.aiScore || 0);
      if (sort === "category") return a.category.localeCompare(b.category);
      if (sort === "status") return a.status.localeCompare(b.status);
      return new Date(b.createdAt) - new Date(a.createdAt);
    });
  }, [items, search, category, status, severity, department, sort]);

  const count = (fn) => items.filter(fn).length;
  return <><PageHeader eyebrow="MUNICIPAL CONTROL" title="Complaints" description="Review, filter and sort every citizen complaint. Officers do not create complaints from this section." />
    <div className="stats-grid complaint-stats">
      <StatCard icon="◎" label="Total Complaints" value={items.length} change="All citizen reports" type="blue" />
      <StatCard icon="!" label="Critical" value={count(c => c.severity === "Critical")} change="Highest priority" type="red" />
      <StatCard icon="↻" label="Under Review / Active" value={count(c => c.status !== "Resolved")} change="Needs attention" type="orange" />
      <StatCard icon="✓" label="Resolved" value={count(c => c.status === "Resolved")} change="Completed reports" type="green" />
    </div>
    <section className="panel">
      <div className="filter-toolbar">
        <input className="complaint-search" placeholder="Search ID, category, location, description…" value={search} onChange={e => setSearch(e.target.value)} />
        <select value={category} onChange={e => setCategory(e.target.value)}><option>All</option>{categories.map(c => <option key={c}>{c}</option>)}</select>
        <select value={status} onChange={e => setStatus(e.target.value)}><option>All</option>{statuses.map(s => <option key={s}>{s}</option>)}</select>
        <select value={severity} onChange={e => setSeverity(e.target.value)}><option>All</option><option>Critical</option><option>High</option><option>Medium</option><option>Low</option></select>
        <select value={department} onChange={e => setDepartment(e.target.value)}><option>All</option>{departments.map(d => <option key={d}>{d}</option>)}</select>
        <select value={sort} onChange={e => setSort(e.target.value)}><option value="newest">Newest first</option><option value="oldest">Oldest first</option><option value="severity">Highest severity</option><option value="category">Category A–Z</option><option value="status">Status A–Z</option></select>
      </div>
      <div className="filter-summary">Showing <b>{filtered.length}</b> of <b>{items.length}</b> complaints</div>
      {filtered.length === 0 ? <div className="empty-state"><h3>No complaints found</h3><p>Try changing the search text or filters.</p></div> :
        <div className="table-wrapper"><table><thead><tr><th>ID</th><th>Category</th><th>Description / Location</th><th>Severity</th><th>Status</th><th>Department</th><th>Reported</th></tr></thead>
          <tbody>{filtered.map(c => <tr key={c.id}><td><strong>{c.id}</strong></td><td>{c.category}</td><td><strong>{c.description}</strong><br /><span className="table-muted">{c.location || "Location unavailable"}</span></td><td><SeverityBadge severity={c.severity || "Medium"} /><br /><span className="table-muted">{c.aiScore || 0}/100</span></td><td><span className={`status-pill ${(c.status || "Submitted").toLowerCase().replace(/\s+/g, "-")}`}>{c.status || "Submitted"}</span></td><td>{c.department || "Not assigned"}</td><td>{c.createdAt ? new Date(c.createdAt).toLocaleString() : "—"}</td></tr>)}</tbody></table></div>}
    </section>
  </>;
}
function Complaints({ session }) { return <ComplaintForm session={session} />; }
function MyComplaints() { const session = loadSession(); const items = loadComplaints().filter(c => c.citizenEmail === session?.email); return <><PageHeader eyebrow="CITIZEN TRACKING" title="My Complaints" description="Track municipal action, expected resolution and latest situation updates." />{items.length === 0 ? <div className="empty-state">No complaints yet. <NavLink to="/complaints">Report your first complaint →</NavLink></div> : <div className="complaint-cards">{items.map(c => <ComplaintStatusCard key={c.id} complaint={c} />)}</div>}</> }
function ComplaintStatusCard({ complaint }) { return <div className="panel complaint-status-card"><div className="status-card-top"><div><strong>{complaint.id}</strong><h3>{complaint.category}</h3><p>{complaint.location}</p></div><SeverityBadge severity={complaint.severity} /></div><div className="timeline">{statuses.map((s, i) => <div className={`timeline-step ${statuses.indexOf(complaint.status) >= i ? "done" : ""}`} key={s}><span>{statuses.indexOf(complaint.status) >= i ? "✓" : i + 1}</span><small>{s}</small></div>)}</div><div className="status-grid"><div><span>AI Score</span><strong>{complaint.aiScore}/100</strong></div><div><span>Department</span><strong>{complaint.department}</strong></div><div><span>Expected Resolution</span><strong>{complaint.expectedResolution}</strong></div><div><span>Latest Situation</span><strong>{complaint.updates?.[0]?.text || "Awaiting officer update"}</strong></div></div></div> }

function ResolutionCamera({ complaint, onCancel, onCaptured }) {
  const videoRef = useRef(null); const streamRef = useRef(null);
  const [ready, setReady] = useState(false); const [error, setError] = useState("");
  useEffect(() => {
    let cancelled = false;
    async function start() {
      if (!navigator.mediaDevices?.getUserMedia) { setError("Live camera access is not supported by this browser."); return; }
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false });
        if (cancelled) { stream.getTracks().forEach(t => t.stop()); return; }
        streamRef.current = stream;
        if (videoRef.current) { videoRef.current.srcObject = stream; await videoRef.current.play(); }
        setReady(true); setError("");
      } catch (err) { setError("Camera permission is required. Allow camera access to capture the resolution photo."); }
    }
    start();
    return () => { cancelled = true; streamRef.current?.getTracks().forEach(t => t.stop()); streamRef.current = null; };
  }, []);
  function capture() {
    const video = videoRef.current;
    if (!video || video.readyState < 2) { alert("Camera is not ready yet."); return; }
    const canvas = document.createElement("canvas"); canvas.width = video.videoWidth || 1280; canvas.height = video.videoHeight || 720;
    canvas.getContext("2d").drawImage(video, 0, 0, canvas.width, canvas.height);
    onCaptured(canvas.toDataURL("image/jpeg", 0.84));
  }
  return <div className="camera-modal-backdrop"><div className="camera-modal">
    <div className="camera-modal-head"><div><span className="eyebrow">RESOLUTION VERIFICATION</span><h2>Capture live after-work photo</h2><p>{complaint.id} · {complaint.category} · {complaint.ward || "Ward not selected"}</p></div><button className="secondary-button" onClick={onCancel}>Cancel</button></div>
    <div className="camera-box resolution-camera-box"><video ref={videoRef} className="camera-preview" playsInline muted autoPlay aria-label="Officer live resolution camera" /><div className="camera-status">{error || (!ready ? "Starting live camera…" : "Camera live — gallery upload is disabled")}</div></div>
    {error && <div className="camera-error-message">{error}</div>}
    <div className="resolution-camera-actions"><button className="secondary-button" onClick={onCancel}>Cancel</button><button className="primary-button" disabled={!ready} onClick={capture}>◉ Capture & Mark Resolved</button></div>
    <small className="security-note">This resolution cannot be completed until a fresh image is captured from the live camera. No gallery/file upload is available.</small>
  </div></div>;
}
function OfficerDashboard() {
  const [complaints, setComplaints] = useState(loadComplaints());
  useEffect(() => { const refresh = () => setComplaints(loadComplaints()); window.addEventListener("storage", refresh); return () => window.removeEventListener("storage", refresh); }, []);
  return <><Dashboard officer /><section className="panel recent-panel"><div className="panel-header"><div><h2>Officer Action Queue</h2><p>Citizen evidence is visible below. Resolved status requires a fresh live after-work photo.</p></div></div><OfficerTable complaints={complaints} onChange={setComplaints} /></section></>;
}
function OfficerTable({ complaints, onChange }) {
  const [sort, setSort] = useState("newest"); const [resolutionComplaint, setResolutionComplaint] = useState(null);
  function update(id, patch) { const next = loadComplaints().map(c => c.id === id ? { ...c, ...patch } : c); saveComplaints(next); onChange(next); }
  const sorted = [...complaints].sort((a, b) => sort === "priority" ? (b.aiScore || 0) - (a.aiScore || 0) : new Date(b.createdAt) - new Date(a.createdAt));
  function openResolution(c) { setResolutionComplaint(c); }
  function completeResolution(photo) {
    const c = resolutionComplaint;
    update(c.id, { resolutionPhoto: photo, resolutionPhotoName: "Live camera capture", status: "Resolved", resolvedAt: new Date().toISOString(), expectedResolution: "Completed", updates: [{ text: "Complaint resolved after live after-work evidence was captured.", at: new Date().toLocaleString() }, ...(c.updates || [])] });
    setResolutionComplaint(null);
  }
  return <div className="officer-queue">
    <div className="sort-bar"><strong>Sort complaints</strong><button className={sort === "newest" ? "active-sort" : ""} onClick={() => setSort("newest")}>Newest</button><button className={sort === "priority" ? "active-sort" : ""} onClick={() => setSort("priority")}>Priority</button></div>
    {sorted.length === 0 ? <div className="empty-state">No citizen complaints have been submitted yet.</div> : sorted.map(c => <div className="officer-card" key={c.id}>
      <div className="officer-card-head"><div><strong>{c.id}</strong><h3>{c.category}</h3><p>{c.ward || "Ward not selected"} · {c.location} · AI severity <b>{c.severity} ({c.aiScore})</b></p></div><SeverityBadge severity={c.severity} /></div>
      <div className="officer-evidence-grid"><div><div className="evidence-title">Citizen complaint photo</div>{c.photo ? <img className="officer-evidence-image" src={c.photo} alt={`Citizen evidence for ${c.id}`} onClick={() => window.open(c.photo, "_blank", "noopener,noreferrer")} /> : <div className="evidence-placeholder">No citizen photo available</div>}<small>{c.photoName || "Citizen submitted evidence"}</small></div>{c.resolutionPhoto && <div><div className="evidence-title">Resolution photo</div><img className="officer-evidence-image" src={c.resolutionPhoto} alt={`Resolution evidence for ${c.id}`} onClick={() => window.open(c.resolutionPhoto, "_blank", "noopener,noreferrer")} /><small>{c.resolutionPhotoName || "Resolution evidence"}</small></div>}</div>
      <div className="officer-controls"><label>Status<select value={c.status} onChange={e => { if (e.target.value === "Resolved" && !c.resolutionPhoto) { openResolution(c); return; } update(c.id, { status: e.target.value }) }}>{statuses.map(st => <option key={st}>{st}</option>)}</select></label><label>Department<select value={c.department} onChange={e => update(c.id, { department: e.target.value })}><option>Not assigned</option>{departments.map(d => <option key={d}>{d}</option>)}</select></label><label>Expected resolution<input type="datetime-local" onChange={e => update(c.id, { expectedResolution: e.target.value ? new Date(e.target.value).toLocaleString() : "Not assigned" })} /></label><label>Current situation<input placeholder="e.g. repair team dispatched" onKeyDown={e => { if (e.key === "Enter" && e.currentTarget.value.trim()) { const old = loadComplaints().find(x => x.id === c.id); update(c.id, { updates: [{ text: e.currentTarget.value, at: new Date().toLocaleString() }, ...(old?.updates || [])] }); e.currentTarget.value = ""; } }} /></label></div>
      {c.status !== "Resolved" && <div className="resolve-action-row"><button className="primary-button" onClick={() => openResolution(c)}>📷 Capture live photo & Mark Resolved</button><span>Required before completion</span></div>}
    </div>)}
    {resolutionComplaint && <ResolutionCamera complaint={resolutionComplaint} onCancel={() => setResolutionComplaint(null)} onCaptured={completeResolution} />}
  </div>;
}
function WardAnalytics() {
  const [category, setCategory] = useState("All Problems"); const [status, setStatus] = useState("All Statuses");
  const complaints = loadComplaints();
  const filtered = complaints.filter(c => (category === "All Problems" || c.category === category) && (status === "All Statuses" || c.status === status));
  const wardCounts = WARDS.map(ward => ({ ward, count: filtered.filter(c => c.ward === ward).length }));
  const maxWard = Math.max(...wardCounts.map(x => x.count), 1);
  const categoryCounts = categories.map(cat => ({ category: cat, count: filtered.filter(c => c.category === cat).length }));
  const maxCategory = Math.max(...categoryCounts.map(x => x.count), 1);
  const statusCounts = statuses.map(st => ({ status: st, count: filtered.filter(c => c.status === st).length }));
  const maxStatus = Math.max(...statusCounts.map(x => x.count), 1);
  return <><PageHeader eyebrow="WARD ANALYTICS" title="Problems by Ward & Category" description={`Live dashboard using ${complaints.length} complaints, including ${complaints.filter(c => c.demo).length} demo complaints for analytics.`} />
    <div className="stats-grid complaint-stats"><StatCard icon="◎" label="All Complaints" value={complaints.length} /><StatCard icon="▥" label="Wards Covered" value={new Set(complaints.map(c => c.ward).filter(Boolean)).size} /><StatCard icon="✓" label="Resolved" value={complaints.filter(c => c.status === "Resolved").length} /><StatCard icon="↻" label="Pending / Active" value={complaints.filter(c => c.status !== "Resolved").length} /></div>
    <section className="panel ward-analytics-panel"><div className="analytics-toolbar"><div><strong>Filter analytics</strong><p>Filter both graphs and see the complaint numbers for every ward.</p></div><div className="analytics-filter-group"><label>Problem type<select value={category} onChange={e => setCategory(e.target.value)}><option>All Problems</option>{categories.map(c => <option key={c}>{c}</option>)}</select></label><label>Status<select value={status} onChange={e => setStatus(e.target.value)}><option>All Statuses</option>{statuses.map(st => <option key={st}>{st}</option>)}</select></label></div></div></section>
    <section className="panel ward-analytics-panel"><div className="panel-header"><div><h2>All 79 wards — complaint count</h2><p>{filtered.length} complaints match the selected filters. Every ward is shown, including wards with zero matching complaints.</p></div></div><div className="ward-bar-chart ward-bar-chart-scroll">{wardCounts.map(x => <div className="ward-bar-row" key={x.ward}><div className="ward-bar-label"><strong>{x.ward}</strong><span>{x.count}</span></div><div className="ward-bar-track"><div className="ward-bar-fill" style={{ width: `${x.count ? Math.max((x.count / maxWard) * 100, 2) : 0}%` }}><span>{x.count}</span></div></div></div>)}</div></section>
    <section className="panel ward-analytics-panel"><div className="panel-header"><div><h2>All problem categories</h2><p>Complaint volume across every civic problem category.</p></div></div><div className="category-bar-chart">{categoryCounts.map(x => <div className="category-bar-row" key={x.category}><div className="category-bar-label"><strong>{x.category}</strong><span>{x.count}</span></div><div className="ward-bar-track"><div className="category-bar-fill" style={{ width: `${x.count ? Math.max((x.count / maxCategory) * 100, 2) : 0}%` }}><span>{x.count}</span></div></div></div>)}</div></section>
    <section className="panel ward-analytics-panel"><div className="panel-header"><div><h2>Status distribution</h2><p>See how the complete demo and citizen dataset is distributed between pending and resolved states.</p></div></div><div className="category-bar-chart">{statusCounts.map(x => <div className="category-bar-row" key={x.status}><div className="category-bar-label"><strong>{x.status}</strong><span>{x.count}</span></div><div className="ward-bar-track"><div className="status-bar-fill" style={{ width: `${x.count ? Math.max((x.count / maxStatus) * 100, 2) : 0}%` }}><span>{x.count}</span></div></div></div>)}</div></section>
  </>;
}
const hotspotDisplay = defaultPoints.map((p, i) => ({ ...p, complaints: [12, 10, 8, 7][i] || 5, persistence: [91, 83, 72, 78][i] || 60, impact: [4200, 3100, 2800, 2400][i] || 1200 }));
function Hotspots() { const navigate = useNavigate(); return <><PageHeader eyebrow="SPATIAL INTELLIGENCE" title="Jabalpur Urban Hotspots" description="Persistent clusters of problems detected from complaint patterns." /><section className="panel map-panel"><div className="panel-header"><div><h2>Hotspots across Jabalpur</h2><p>Different marker colors represent severity.</p></div></div><GoogleMap points={hotspotDisplay} onPointClick={p => navigate(`/hotspots/${p.id}`)} /></section><div className="hotspot-grid">{hotspotDisplay.map(h => <div className="hotspot-card" key={h.id} onClick={() => navigate(`/hotspots/${h.id}`)}><div className="hotspot-card-top"><SeverityBadge severity={h.severity} /><div className="score-circle"><strong>{h.score}</strong><small>/100</small></div></div><h3>{h.title}</h3><p>{h.location}</p><div className="hotspot-metrics"><div><span>Complaints</span><strong>{h.complaints}</strong></div><div><span>Persistence</span><strong>{h.persistence}%</strong></div><div><span>Impact</span><strong>{h.impact.toLocaleString()}</strong></div></div></div>)}</div></> }
function HotspotDetails() { const { id } = useParams(); const h = hotspotDisplay.find(x => x.id === id) || hotspotDisplay[0]; return <><PageHeader eyebrow={`${h.location} · Jabalpur`} title={h.title} description="Priority score combines complaint density, persistence, severity and impact." action={<SeverityBadge severity={h.severity} />} /><div className="detail-score-card"><div><span>PRIORITY SCORE</span><strong>{h.score}</strong><small>/100</small></div><div className="score-explanation"><strong>{h.severity} priority intervention</strong><p>Related problems: {cityHotspots.find(x => x.id === h.id)?.relatedProblems?.join(" → ") || h.category}.</p></div></div><div className="detail-stats"><StatCard icon="◎" label="Complaint Count" value={h.complaints} /><StatCard icon="◷" label="Persistence" value={`${h.persistence}%`} /><StatCard icon="!" label="Severity" value={h.severity} /><StatCard icon="◉" label="Impact" value={h.impact.toLocaleString()} /></div><section className="panel"><div className="panel-header"><div><h2>Exact hotspot location</h2><p>{h.lat.toFixed(5)}, {h.lng.toFixed(5)}</p></div></div><GoogleMap points={[h]} /></section></> }
function Relationships() { const chain = ["Drain Overflow", "Waterlogging", "Road Damage", "Potholes"]; return <><PageHeader eyebrow="ROOT-CAUSE INTELLIGENCE" title="Problem Relationship Graph" description="A visual chain showing how one urban problem can trigger another." /><section className="panel graph-panel"><div className="relationship-chain">{chain.map((n, i) => <React.Fragment key={n}><div className={`graph-node ${i === 0 ? "root" : i === 1 ? "current" : "impact"}`}><div className="node-number">{i + 1}</div><div><strong>{n}</strong><span>{i === 0 ? "Potential upstream cause" : i === 1 ? "Current observed problem" : "Downstream impact"}</span></div></div>{i < chain.length - 1 && <div className="graph-arrow"><span>↓</span></div>}</React.Fragment>)}</div></section></> }
function PriorityRanking() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch("http://127.0.0.1:8000/priority?limit=20")
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Priority API request failed: ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        if (data.status && data.status !== "ok") {
          throw new Error(data.message || "Priority API returned an error.");
        }

        const rows = Array.isArray(data)
          ? data
          : data.priority || data.priorities || data.rankings || data.results || data.items || [];

        setItems(rows);
      })
      .catch((err) => {
        console.error("Priority API error:", err);
        setError(err.message);
      })
      .finally(() => setLoading(false));
  }, []);

  function getValue(item, keys, fallback = "—") {
    for (const key of keys) {
      if (item?.[key] !== undefined && item?.[key] !== null) return item[key];
    }
    return fallback;
  }

  function getSeverity(item) {
    const severity = getValue(item, ["severity", "priority_level", "risk"], "");
    if (severity) return String(severity);
    const score = Number(getValue(item, ["priority_score", "score", "priority"], 0));
    return score >= 80 ? "Critical" : score >= 60 ? "High" : score >= 40 ? "Medium" : "Low";
  }

  return (
    <>
      <PageHeader
        eyebrow="DECISION SUPPORT"
        title="Priority Ranking"
        description="Live municipal priority ranking from the UrbanNova backend."
      />

      {loading && (
        <div className="panel" style={{ padding: "30px", textAlign: "center" }}>
          <h2>Loading priority ranking...</h2>
          <p>Fetching the latest ranked hotspots from the UrbanNova engine.</p>
        </div>
      )}

      {error && (
        <div
          className="panel"
          style={{
            padding: "30px",
            border: "1px solid #ef4444",
            marginBottom: "20px",
          }}
        >
          <h2>Unable to load priority ranking</h2>
          <p>{error}</p>
          <p>
            Make sure the backend is running at{" "}
            <strong>http://127.0.0.1:8000</strong>.
          </p>
        </div>
      )}

      {!loading && !error && items.length === 0 && (
        <div className="panel" style={{ padding: "30px", textAlign: "center" }}>
          <h2>No priority records available</h2>
          <p>The priority API did not return any ranked records.</p>
        </div>
      )}

      {!loading && !error && items.length > 0 && (
        <section className="panel ranking-panel">
          <div className="ranking-list">
            {items.map((item, index) => {
              const ward = getValue(item, ["ward_number", "ward", "ward_no"], "Unknown ward");
              const category = getValue(item, ["category", "problem_type", "issue"], "Urban problem");
              const location = getValue(item, ["location", "area", "name"], `Ward ${ward}`);
              const complaints = getValue(item, ["complaints", "complaint_count", "count"], "—");
              const persistence = getValue(item, ["persistence", "persistence_score"], "—");
              const score = Number(getValue(item, ["priority_score", "score", "priority"], 0));
              const severity = getSeverity(item);

              return (
                <div className="ranking-row" key={`${ward}-${category}-${index}`}>
                  <div className="ranking-number">
                    {String(index + 1).padStart(2, "0")}
                  </div>

                  <div className="ranking-location">
                    <strong>{category}</strong>
                    <span>{location} · Ward {ward}</span>
                  </div>

                  <div className="ranking-metric">
                    <span>Complaints</span>
                    <strong>{complaints}</strong>
                  </div>

                  <div className="ranking-metric">
                    <span>Persistence</span>
                    <strong>
                      {persistence === "—" ? "—" : `${persistence}%`}
                    </strong>
                  </div>

                  <div className="ranking-score">
                    <strong>{score}</strong>
                    <SeverityBadge severity={severity} />
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}
    </>
  );
}
function Login() { const navigate = useNavigate(); const [mode, setMode] = useState("login"); const [role, setRole] = useState("citizen"); const [form, setForm] = useState({ name: "", email: "", password: "" }); function submit(e) { e.preventDefault(); let user = DEMO_USERS.find(u => u.email === form.email && u.password === form.password && u.role === role); if (mode === "signup") { if (!form.name || !form.email || !form.password) { alert("Fill all fields"); return; } user = { name: form.name, email: form.email, password: form.password, role }; } if (!user) { alert(`Demo ${role} login: ${role === "citizen" ? "citizen@urbannova.demo / citizen123" : "officer@urbannova.demo / officer123"}`); return; } localStorage.setItem("urbannova_session", JSON.stringify({ name: user.name, email: user.email, role: user.role })); window.location.href = role === "officer" ? "/officer" : "/citizen"; } return <div className="auth-page"><div className="auth-card"><div className="auth-logo">U</div><h1>UrbanNova</h1><p>Jabalpur Urban Problem Hotspot Engine</p><div className="role-switch"><button className={role === "citizen" ? "active" : ""} onClick={() => setRole("citizen")}>👤 Citizen</button><button className={role === "officer" ? "active" : ""} onClick={() => setRole("officer")}>🏛️ Municipal Officer</button></div><div className="auth-tabs"><button className={mode === "login" ? "active" : ""} onClick={() => setMode("login")}>Login</button><button className={mode === "signup" ? "active" : ""} onClick={() => setMode("signup")}>Sign up</button></div><form onSubmit={submit}>{mode === "signup" && <input placeholder="Full name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />}<input type="email" placeholder="Email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} /><input type="password" placeholder="Password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} /><button className="submit-button">{mode === "login" ? "Login" : "Create Account"}</button></form><div className="demo-login">{role === "citizen" ? <>Citizen demo: <b>citizen@urbannova.demo</b> / <b>citizen123</b></> : <>Officer demo: <b>officer@urbannova.demo</b> / <b>officer123</b></>}</div></div></div> }
function HelpDesk() {
  return <><PageHeader eyebrow="CITIZEN SUPPORT" title="Help Desk" description="Quick answers and support for reporting civic problems through UrbanNova." />
    <section className="panel faq-panel"><h2>Frequently Asked Questions</h2>
      <div className="faq-item"><h3>How to report an issue?</h3><p>Go to 'Report Complaint', fill in your details, take a live picture of the issue, and submit.</p></div>
      <div className="faq-item"><h3>Why is live location required?</h3><p>Live location ensures accuracy and helps the municipal team pinpoint the exact problem area efficiently.</p></div>
      <div className="faq-item"><h3>Can I submit multiple issues?</h3><p>You can submit one complaint per category every 24 hours to prevent spam and allow efficient processing.</p></div>
      <div className="contact-box"><h2>Contact Us</h2><p>Email: <a href="mailto:support@urbannova.gov.in">support@urbannova.gov.in</a></p><p>Toll-Free: <strong>1800-11-2233</strong></p></div>
    </section></>
}


function About() {
  return <><PageHeader eyebrow="ABOUT URBANNOVA" title="Jabalpur Civic Administration" description="UrbanNova is a civic intelligence interface for citizens and municipal teams." />
    <section className="panel about-panel"><h2>Current Municipal Officials</h2>
      <div className="official-grid">
        <div><strong>Mayor</strong><span>Shri Jagat Bahadur Singh 'Annu'</span></div>
        <div><strong>Municipal Commissioner</strong><span>Smt. Preeti Yadav, IAS</span></div>
        <div><strong>Chairman, JMC</strong><span>Shri Rikunj Vij</span></div>
        <div><strong>Smart City CEO</strong><span>Smt. Nidhi Singh Rajput</span></div>
      </div>
      <div className="about-description"><p><b>UrbanNova</b> is a civic tech platform built to streamline the identification, reporting, and resolution of urban issues across Jabalpur. Our goal is to empower citizens and optimize municipal workflows using AI and spatial intelligence.</p></div>
    </section></>
}


const predictions = [
  { id: "P1", area: "Central Jabalpur", issue: "Waterlogging", risk: "High", reason: "Drain overflow + recurring low-lying hotspot pattern", window: "During heavy rainfall", action: "Pre-clean drains and monitor road-side inlets." },
  { id: "P2", area: "Adhartal Road", issue: "Road surface deterioration", risk: "Medium", reason: "Repeated pothole / road-damage reports", window: "Next 2–8 weeks", action: "Inspect surface and schedule preventive patching." },
  { id: "P3", area: "South Jabalpur", issue: "Drainage blockage", risk: "High", reason: "Drainage-to-waterlogging relationship pattern", window: "During intense rain", action: "Inspect connected drains before rainfall peaks." }
];
function Predictor() {
  const [predictions, setPredictions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadPredictions() {
      try {
        setLoading(true);
        setError("");

        const response = await fetch(
          "http://127.0.0.1:8000/predictions?limit=20&min_probability=0"
        );

        if (!response.ok) {
          throw new Error(`API returned ${response.status}`);
        }

        const data = await response.json();

        setPredictions(data.predictions || []);
      } catch (err) {
        console.error("Prediction API error:", err);
        setError("Unable to load predictions from the prediction engine.");
      } finally {
        setLoading(false);
      }
    }

    loadPredictions();
  }, []);

  function getRisk(probability) {
    if (probability >= 80) return "High";
    if (probability >= 60) return "Medium";
    return "Low";
  }

  function getAction(category) {
    const actions = {
      Drainage: "Inspect and clean connected drains before rainfall.",
      "Garbage Collection":
        "Increase collection frequency and inspect recurring accumulation points.",
      Waterlogging:
        "Pre-clean drainage inlets and monitor low-lying road sections.",
      Streetlight:
        "Inspect failed fixtures and schedule preventive maintenance.",
      Pothole:
        "Inspect the road section and schedule preventive patching.",
      "Damaged Road":
        "Inspect the road surface and schedule corrective maintenance.",
      "Water Supply":
        "Inspect the local water network and monitor supply interruptions.",
      Sewerage:
        "Inspect sewer lines and clear recurring blockage locations."
    };

    return (
      actions[category] ||
      "Inspect the affected area and schedule preventive intervention."
    );
  }

  return (
    <>
      <PageHeader
        eyebrow="PREDICTIVE CIVIC INTELLIGENCE"
        title="Future Issue Predictor"
        description="AI-generated predictions based on historical complaint patterns. Predictions are advisory and support preventive municipal action."
      />

      {loading && (
        <section className="panel">
          <h2>Loading prediction engine...</h2>
          <p>Fetching the latest predictions from the backend.</p>
        </section>
      )}

      {!loading && error && (
        <section className="panel">
          <h2>Prediction Engine Unavailable</h2>
          <p>{error}</p>
          <button
            className="primary-button"
            onClick={() => window.location.reload()}
          >
            Retry
          </button>
        </section>
      )}

      {!loading && !error && predictions.length === 0 && (
        <section className="panel">
          <h2>No predictions available</h2>
          <p>The prediction engine returned no results.</p>
        </section>
      )}

      {!loading && !error && predictions.length > 0 && (
        <>
          <div className="stats-grid">
            <StatCard
              icon="AI"
              label="Predictions"
              value={predictions.length}
              change="Latest model output"
              type="blue"
            />

            <StatCard
              icon="!"
              label="High Risk"
              value={
                predictions.filter(
                  (p) => getRisk(p.prediction_probability) === "High"
                ).length
              }
              change="Preventive attention"
              type="red"
            />

            <StatCard
              icon="UP"
              label="Top Probability"
              value={`${Math.round(
                predictions[0]?.prediction_probability || 0
              )}%`}
              change="Highest predicted risk"
              type="orange"
            />

            <StatCard
              icon="MAP"
              label="Wards Covered"
              value={
                new Set(predictions.map((p) => p.ward_number)).size
              }
              change="Affected wards"
              type="green"
            />
          </div>

          <div className="prediction-grid">
            {predictions.map((p, index) => {
              const probability = Number(p.prediction_probability || 0);
              const risk = getRisk(probability);

              return (
                <div
                  className="panel prediction-card"
                  key={`${p.ward_number}-${p.category}-${index}`}
                >
                  <div className="prediction-top">
                    <span className={`risk-pill ${risk.toLowerCase()}`}>
                      {risk} Risk
                    </span>

                    <span>
                      {probability.toFixed(2)}% probability
                    </span>
                  </div>

                  <h2>{p.category}</h2>

                  <strong>Ward {p.ward_number}</strong>

                  <p>
                    The prediction engine estimates a{" "}
                    <b>{probability.toFixed(2)}%</b> probability that{" "}
                    <b>{p.category}</b> will be reported in Ward{" "}
                    <b>{p.ward_number}</b> during the next prediction
                    period.
                  </p>

                  <div className="prediction-action">
                    <b>Recommended preventive action</b>
                    <span>{getAction(p.category)}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}
    </>
  );
}
function Notices() { const session = loadSession(); const [items, setItems] = useState(loadNotices()); const [form, setForm] = useState({ title: "", date: "", body: "", department: "Citizen Services" }); const [editing, setEditing] = useState(null); function persist(next) { setItems(next); saveNotices(next) } function add(e) { e.preventDefault(); if (!form.title || !form.body) { alert("Add a notice title and description."); return; } if (editing) { persist(items.map(n => n.id === editing ? { ...n, ...form } : n)); setEditing(null) } else { persist([{ id: `N-${Date.now()}`, ...form }, ...items]) } setForm({ title: "", date: "", body: "", department: "Citizen Services" }); } function remove(id) { persist(items.filter(n => n.id !== id)) } function edit(n) { setEditing(n.id); setForm({ title: n.title, date: n.date || "", body: n.body, department: n.department || "Citizen Services" }) } return <><PageHeader eyebrow="PUBLIC INFORMATION" title="Notices" description="Public notices published by the municipal control team." />{session?.role === "officer" && <section className="panel notice-editor"><h2>Officer Notice Management</h2><form onSubmit={add} className="notice-form"><input placeholder="Notice title" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} /><input type="date" value={form.date} onChange={e => setForm({ ...form, date: e.target.value })} /><select value={form.department} onChange={e => setForm({ ...form, department: e.target.value })}>{departments.map(d => <option key={d}>{d}</option>)}<option>Citizen Services</option></select><textarea placeholder="Notice details" value={form.body} onChange={e => setForm({ ...form, body: e.target.value })} /><button className="primary-button">{editing ? "Save Changes" : "Publish Notice"}</button>{editing && <button type="button" className="secondary-button" onClick={() => { setEditing(null); setForm({ title: "", date: "", body: "", department: "Citizen Services" }) }}>Cancel</button>}</form></section>}<div className="notice-list">{items.map(n => <article className="panel notice-card" key={n.id}><div className="notice-meta"><span>{n.department}</span><small>{n.date || "Published today"}</small></div><h2>{n.title}</h2><p>{n.body}</p>{session?.role === "officer" && <div><button className="secondary-button" onClick={() => edit(n)}>Edit</button> <button className="danger-button" onClick={() => remove(n.id)}>Delete</button></div>}</article>)}</div></> }
function App() { const [session, setSession] = useState(loadSession()); function logout() { localStorage.removeItem("urbannova_session"); setSession(null); window.location.href = "/login"; } return <BrowserRouter><Routes><Route path="/login" element={<Login />} /><Route path="/citizen" element={<Protected role="citizen"><Layout session={session} logout={logout}><Dashboard /></Layout></Protected>} /><Route path="/officer" element={<Protected role="officer"><Layout session={session} logout={logout}><OfficerDashboard /></Layout></Protected>} /><Route path="/complaints" element={<Protected role={session?.role || "none"}><Layout session={session} logout={logout}><Complaints session={session} /></Layout></Protected>} /><Route path="/ward-analytics" element={<Protected role="officer"><Layout session={session} logout={logout}><WardAnalytics /></Layout></Protected>} /><Route path="/my-complaints" element={<Protected role="citizen"><Layout session={session} logout={logout}><MyComplaints /></Layout></Protected>} /><Route path="/hotspots" element={<Protected role={session?.role || "none"}><Layout session={session} logout={logout}><Hotspots /></Layout></Protected>} /><Route path="/hotspots/:id" element={<Protected role={session?.role || "none"}><Layout session={session} logout={logout}><HotspotDetails /></Layout></Protected>} /><Route path="/relationships" element={<Protected role="officer"><Layout session={session} logout={logout}><Relationships /></Layout></Protected>} /><Route path="/priority" element={<Protected role="officer"><Layout session={session} logout={logout}><PriorityRanking /></Layout></Protected>} /><Route path="/notices" element={<Protected role={session?.role || "none"}><Layout session={session} logout={logout}><Notices /></Layout></Protected>} /><Route path="/about" element={<Protected role={session?.role || "none"}><Layout session={session} logout={logout}><About /></Layout></Protected>} /><Route path="/help" element={<Protected role={session?.role || "none"}><Layout session={session} logout={logout}><HelpDesk /></Layout></Protected>} /><Route path="/predictor" element={<Protected role="officer"><Layout session={session} logout={logout}><Predictor /></Layout></Protected>} /><Route path="*" element={<Navigate to={session?.role === "officer" ? "/officer" : session?.role === "citizen" ? "/citizen" : "/login"} replace />} /></Routes></BrowserRouter> }
export default App;
