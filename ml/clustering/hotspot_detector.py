import numpy as np
from sklearn.cluster import DBSCAN

def detect_hotspots(points_xy, eps_m=220, min_samples=4):
    """Return DBSCAN labels for projected x/y coordinates in metres."""
    if len(points_xy) == 0:
        return np.array([], dtype=int)
    return DBSCAN(
        eps=eps_m,
        min_samples=min_samples,
    ).fit_predict(points_xy)
