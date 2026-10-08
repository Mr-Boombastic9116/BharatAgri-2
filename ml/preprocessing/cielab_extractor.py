import numpy as np
from PIL import Image
import os

def rgb_to_cielab(rgb_img_np: np.ndarray) -> np.ndarray:
    """
    Convert an RGB numpy array (uint8, shape HxWx3) to CIELAB color space (float32, shape HxWx3).
    Follows standard CIE 1976 D65 reference illuminant transformation:
    sRGB -> Linear RGB -> CIE XYZ -> CIELAB.
    """
    if rgb_img_np.dtype != np.float32 and rgb_img_np.dtype != np.float64:
        rgb = rgb_img_np.astype(np.float32) / 255.0
    else:
        rgb = rgb_img_np.astype(np.float32)

    # 1. Gamma linearization (sRGB companding inverse)
    mask = rgb > 0.04045
    rgb_lin = np.empty_like(rgb)
    rgb_lin[mask] = np.power((rgb[mask] + 0.055) / 1.055, 2.4)
    rgb_lin[~mask] = rgb[~mask] / 12.92

    # 2. Linear RGB to CIE XYZ (Observer 2 deg, Illuminant D65)
    r = rgb_lin[..., 0]
    g = rgb_lin[..., 1]
    b = rgb_lin[..., 2]

    x = 0.4124564 * r + 0.3575761 * g + 0.1804375 * b
    y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
    z = 0.0193339 * r + 0.1191920 * g + 0.9503041 * b

    # 3. Normalize by D65 reference white point
    xn = 0.95047
    yn = 1.00000
    zn = 1.08883

    xr = x / xn
    yr = y / yn
    zr = z / zn

    # 4. Non-linear transform function f(t)
    delta = 6.0 / 29.0
    delta_sq = delta * delta
    delta_cb = delta * delta_sq

    def f_trans(t):
        out = np.empty_like(t)
        t_mask = t > delta_cb
        out[t_mask] = np.cbrt(t[t_mask])
        out[~t_mask] = (t[~t_mask] / (3.0 * delta_sq)) + (4.0 / 29.0)
        return out

    fx = f_trans(xr)
    fy = f_trans(yr)
    fz = f_trans(zr)

    # 5. Compute L*, a*, b*
    L_star = 116.0 * fy - 16.0
    a_star = 500.0 * (fx - fy)
    b_star = 200.0 * (fy - fz)

    lab = np.stack([L_star, a_star, b_star], axis=-1)
    return lab

def extract_mango_features(image_input, use_l: bool = False, target_size=(128, 128)) -> np.ndarray:
    """
    Extract statistical and visual condition features from a mango fruit image crop.
    
    If use_l is False (Models A, B, C): Extracts features from a* and b* chromaticity channels,
    avoiding luminance sensitivity as inspired by the paper's chromatic focus.
    
    If use_l is True (Optional Model D): Includes L* luminance distribution metrics.
    """
    if isinstance(image_input, str):
        if not os.path.exists(image_input):
            raise FileNotFoundError(f"Image not found at {image_input}")
        with Image.open(image_input) as img:
            rgb_img = img.convert('RGB')
    elif isinstance(image_input, Image.Image):
        rgb_img = image_input.convert('RGB')
    elif isinstance(image_input, np.ndarray):
        rgb_img = Image.fromarray(image_input.astype(np.uint8)).convert('RGB')
    else:
        raise ValueError("Unsupported image input type.")

    # Standardize scale
    if target_size is not None:
        rgb_img = rgb_img.resize(target_size, Image.Resampling.BILINEAR)

    rgb_np = np.array(rgb_img)

    # Segment fruit foreground (filter out pure black/white background borders if present)
    lum_sum = rgb_np.sum(axis=-1)
    fg_mask = (lum_sum > 25) & (lum_sum < 740)
    if not np.any(fg_mask):
        fg_mask = np.ones((rgb_np.shape[0], rgb_np.shape[1]), dtype=bool)

    lab_np = rgb_to_cielab(rgb_np)

    L = lab_np[..., 0][fg_mask]
    a = lab_np[..., 1][fg_mask]
    b = lab_np[..., 2][fg_mask]

    # Chroma = sqrt(a*^2 + b*^2)
    chroma = np.sqrt(np.square(a) + np.square(b))

    # Core a* statistics
    mean_a = float(np.mean(a))
    std_a = float(np.std(a))
    median_a = float(np.median(a))
    p10_a = float(np.percentile(a, 10))
    p25_a = float(np.percentile(a, 25))
    p75_a = float(np.percentile(a, 75))
    p90_a = float(np.percentile(a, 90))

    # Core b* statistics
    mean_b = float(np.mean(b))
    std_b = float(np.std(b))
    median_b = float(np.median(b))
    p10_b = float(np.percentile(b, 10))
    p25_b = float(np.percentile(b, 25))
    p75_b = float(np.percentile(b, 75))
    p90_b = float(np.percentile(b, 90))

    # Chroma distribution
    chroma_mean = float(np.mean(chroma))
    chroma_std = float(np.std(chroma))

    # Chromatic defect indicator (low chroma necrotic pixels or abnormal a* spots)
    # Healthy mango skin typically has chroma > 14 (green: a* < -10, b* > 5; or yellow: b* > 18, a* > -5).
    # Necrotic/canker/anthracnose lesions have dark brownish/black discoloration:
    # low chroma (<14) with brownish chromaticity (a* > -5.0) or low b* with non-green a*.
    # Emerald green skin (a* < -10) is healthy vegetative tissue and is not necrotic.
    necrotic_pixels = ((chroma < 14.0) & (a > -5.0)) | ((b < 10.0) & (a > -5.0))
    affected_ratio = float(np.sum(necrotic_pixels) / len(a))

    # Healthy skin indicator:
    # Accounts for BOTH emerald green Goan mangoes (a* <= -10, b* >= 5) and ripe yellow mangoes (b* >= 18, chroma >= 20)
    healthy_pixels = ((a <= -10.0) & (b >= 5.0) & (chroma >= 12.0)) | ((b >= 18.0) & (chroma >= 20.0))
    healthy_ratio = float(np.sum(healthy_pixels) / len(a))

    # Local texture variation across the fruit surface
    # Approximated by standard deviation of local gradients in the a* channel
    grad_y, grad_x = np.gradient(lab_np[..., 1])
    texture_roughness = float(np.mean(np.sqrt(np.square(grad_x) + np.square(grad_y))[fg_mask]))

    feature_vec = [
        mean_a, std_a, median_a, p10_a, p25_a, p75_a, p90_a,
        mean_b, std_b, median_b, p10_b, p25_b, p75_b, p90_b,
        chroma_mean, chroma_std,
        affected_ratio, healthy_ratio,
        texture_roughness
    ]

    if use_l:
        mean_L = float(np.mean(L))
        std_L = float(np.std(L))
        median_L = float(np.median(L))
        p10_L = float(np.percentile(L, 10))
        p90_L = float(np.percentile(L, 90))
        feature_vec.extend([mean_L, std_L, median_L, p10_L, p90_L])

    return np.array(feature_vec, dtype=np.float32)

def get_feature_names(use_l: bool = False):
    names = [
        "mean_a", "std_a", "median_a", "p10_a", "p25_a", "p75_a", "p90_a",
        "mean_b", "std_b", "median_b", "p10_b", "p25_b", "p75_b", "p90_b",
        "chroma_mean", "chroma_std",
        "affected_ratio", "healthy_ratio",
        "texture_roughness"
    ]
    if use_l:
        names.extend(["mean_L", "std_L", "median_L", "p10_L", "p90_L"])
    return names
