import { BrowserRouter, Routes, Route, Link } from "react-router-dom";

function App() {
  return (
    <BrowserRouter>
      <nav>
        <Link to="/">Dashboard</Link>{" | "}
        <Link to="/complaints">Complaints</Link>{" | "}
        <Link to="/hotspots">Hotspots</Link>{" | "}
        <Link to="/analytics">Analytics</Link>
      </nav>
      <Routes>
        <Route path="/" element={<h1>Urban Problem Hotspot Engine</h1>} />
        <Route path="/complaints" element={<h1>Complaints</h1>} />
        <Route path="/hotspots" element={<h1>Hotspots</h1>} />
        <Route path="/analytics" element={<h1>Analytics</h1>} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
