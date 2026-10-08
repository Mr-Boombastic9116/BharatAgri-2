import numpy as np
from PIL import Image, ImageDraw
import scipy.ndimage as ndi

def get_convex_hull_area(mask):
    """Approximate convex hull area using scipy / grid bounding convex polygon."""
    from scipy.spatial import ConvexHull
    ys, xs = np.where(mask)
    if len(xs) < 4:
        return float(len(xs))
    points = np.column_stack((xs, ys))
    try:
        hull = ConvexHull(points)
        return float(hull.volume)  # In 2D, volume is area
    except Exception:
        return float(len(xs))

def separate_mango_instances(peel_mask, l_est, chroma, min_area=600):
    """
    State-of-the-art hybrid instance segmentation for mangoes:
    1. Distance Transform (EDT)
    2. Peak detection with plateau suppression & prominence filtering
    3. Watershed segmentation on -EDT
    4. Post-watershed geometric validation & false-split merger:
       - Merges pairs if combined shape is convex / natural single fruit
       - Merges pairs if contact boundary lacks saddle depth / edge crease
    """
    dist = ndi.distance_transform_edt(peel_mask)
    max_d = np.max(dist)
    if max_d < 10:
        lbl, _ = ndi.label(peel_mask)
        return lbl, []

    # 1. Peak detection with dynamic footprint based on mango radius
    footprint_rad = max(18, int(max_d * 0.40))
    footprint = np.ones((footprint_rad, footprint_rad), dtype=bool)
    local_max = (dist == ndi.maximum_filter(dist, footprint=footprint)) & (dist > max(15.0, max_d * 0.35)) & peel_mask
    
    lbl_peaks, n_peaks = ndi.label(local_max)
    peaks = []
    for i in range(1, n_peaks + 1):
        ys, xs = np.where(lbl_peaks == i)
        cy = int(np.mean(ys))
        cx = int(np.mean(xs))
        d_val = float(dist[cy, cx])
        peaks.append({'cx': cx, 'cy': cy, 'd': d_val})

    # Cluster peaks that are very close (plateau merging)
    merged_peaks = []
    for p in sorted(peaks, key=lambda x: x['d'], reverse=True):
        too_close = False
        for mp in merged_peaks:
            dist_between = np.hypot(p['cx'] - mp['cx'], p['cy'] - mp['cy'])
            if dist_between < max(25.0, min(p['d'], mp['d']) * 0.65):
                too_close = True
                break
        if not too_close:
            merged_peaks.append(p)

    # If only 1 peak found, it is a single mango!
    if len(merged_peaks) <= 1:
        lbl_inst, _ = ndi.label(peel_mask)
        return lbl_inst, merged_peaks

    # 2. Marker seeds for watershed
    markers = np.zeros(peel_mask.shape, dtype=np.int32)
    for idx, p in enumerate(merged_peaks, 1):
        # Mark 5x5 seed around center
        y1, y2 = max(0, p['cy'] - 2), min(peel_mask.shape[0], p['cy'] + 3)
        x1, x2 = max(0, p['cx'] - 2), min(peel_mask.shape[1], p['cx'] + 3)
        markers[y1:y2, x1:x2] = idx

    # Voronoi / Distance watershed partition
    _, indices = ndi.distance_transform_edt(markers == 0, return_indices=True)
    segmented = markers[indices[0], indices[1]]
    segmented[~peel_mask] = 0

    # 3. Post-segmentation validation & False-Split Merge Check
    # Check each pair of adjacent labels
    labels = [l for l in np.unique(segmented) if l > 0]
    changed = True
    while changed and len(labels) > 1:
        changed = False
        pairs_to_check = []
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                l1, l2 = labels[i], labels[j]
                m1 = (segmented == l1)
                m2 = (segmented == l2)
                # Check adjacency via dilation
                m1_dil = ndi.binary_dilation(m1, structure=np.ones((5, 5), dtype=bool))
                contact = m1_dil & m2
                if np.sum(contact) > 0:
                    pairs_to_check.append((l1, l2, np.sum(contact)))

        for l1, l2, contact_len in pairs_to_check:
            m1 = (segmented == l1)
            m2 = (segmented == l2)
            a1 = float(np.sum(m1))
            a2 = float(np.sum(m2))
            if a1 == 0 or a2 == 0:
                continue

            # Combined mask
            m_comb = m1 | m2
            a_comb = a1 + a2

            # Check solidity: if single mango was split, combined solidity is high
            sol1 = a1 / max(1.0, get_convex_hull_area(m1))
            sol2 = a2 / max(1.0, get_convex_hull_area(m2))
            sol_comb = a_comb / max(1.0, get_convex_hull_area(m_comb))

            # Check boundary evidence:
            # On the contact line, check EDT saddle depth
            m1_dil = ndi.binary_dilation(m1, structure=np.ones((3, 3), dtype=bool))
            contact_pts = m1_dil & m2
            contact_edts = dist[contact_pts]
            min_contact_d = np.min(contact_edts) if len(contact_edts) > 0 else 0.0
            
            # Find peak heights
            p1_d = max([p['d'] for p in merged_peaks if markers[p['cy'], p['cx']] == l1] or [max_d])
            p2_d = max([p['d'] for p in merged_peaks if markers[p['cy'], p['cx']] == l2] or [max_d])
            saddle_ratio = min_contact_d / max(1.0, min(p1_d, p2_d))

            # Rule to merge:
            # 1. Extreme asymmetry: one part is tiny (< 18% of dominant) and wraps around
            is_asymmetric = (min(a1, a2) / max(a1, a2)) < 0.20
            # 2. No true neck/saddle: contact EDT is high (> 60% of peak height) meaning thick body connection
            no_saddle = saddle_ratio > 0.60
            # 3. High combined convexity: combined shape is very solid (> 0.90) and better than individual
            high_convexity = sol_comb >= 0.88 and (sol_comb >= sol1 or sol_comb >= sol2)

            if is_asymmetric or (no_saddle and high_convexity):
                # MERGE l2 into l1
                segmented[segmented == l2] = l1
                labels = [l for l in np.unique(segmented) if l > 0]
                changed = True
                break

    return segmented, merged_peaks
