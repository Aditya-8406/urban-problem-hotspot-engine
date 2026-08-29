export const CITY = {
  name: "Jabalpur",
  state: "Madhya Pradesh",
  country: "India",
  center: [23.1815, 79.9864],
};

export const categories = [
  "Garbage Collection",
  "Drainage",
  "Waterlogging",
  "Road Damage",
  "Potholes",
  "Street Lighting",
  "Water Supply",
  "Sewerage",
];

export const hotspots = [
  {
    id: "H01",
    wards: "12–13",
    title: "Garbage Collection → Drainage → Waterlogging",
    priorityScore: 92,
    priority: "CRITICAL",
    complaints: 0,
    persistence: 0,
    severity: "Critical",
    impact: "High",
    relatedProblems: [
      "Garbage Collection",
      "Drainage",
      "Waterlogging",
    ],
    relationships: [
      "Garbage Collection",
      "Drainage",
      "Waterlogging",
    ],
  },

  {
    id: "H02",
    wards: "24–26",
    title: "Pothole / Damaged Road",
    priorityScore: 88,
    priority: "HIGH",
    complaints: 0,
    persistence: 0,
    severity: "High",
    impact: "High",
    relatedProblems: [
      "Potholes",
      "Road Damage",
    ],
    relationships: [
      "Damaged Road",
      "Potholes",
    ],
  },

  {
    id: "H03",
    wards: "—",
    title: "Jabalpur Urban Problem Hotspot",
    priorityScore: 80,
    priority: "HIGH",
    complaints: 0,
    persistence: 0,
    severity: "High",
    impact: "Medium",
    relatedProblems: [],
    relationships: [],
  },

  {
    id: "H10",
    wards: "39–40",
    title: "Drainage → Waterlogging → Damaged Road",
    priorityScore: 86,
    priority: "HIGH",
    complaints: 0,
    persistence: 0,
    severity: "High",
    impact: "High",
    relatedProblems: [
      "Drainage",
      "Waterlogging",
      "Damaged Road",
    ],
    relationships: [
      "Drainage",
      "Waterlogging",
      "Damaged Road",
    ],
  },
];

export const complaints = [];

export const resolvedComplaints = [];