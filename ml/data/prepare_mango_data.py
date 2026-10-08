import os
import json
import zipfile
import io
import shutil
import random
from collections import Counter, defaultdict
from PIL import Image
import numpy as np

MANGO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'mango'))
WORKSPACE_ROOT = os.path.abspath(os.path.join(MANGO_DIR, '..', '..'))
RAW_DIR = os.path.join(MANGO_DIR, 'raw')
EXTRACTED_DIR = os.path.join(MANGO_DIR, 'extracted')
PROCESSED_DIR = os.path.join(MANGO_DIR, 'processed')
CROPS_DIR = os.path.join(PROCESSED_DIR, 'crops')
MANIFESTS_DIR = os.path.join(MANGO_DIR, 'manifests')
SPLITS_DIR = os.path.join(MANGO_DIR, 'splits')

LABEL_MAPPING_PATH = os.path.join(MANGO_DIR, 'label_mapping.json')
DATASET_REPORT_PATH = os.path.join(MANGO_DIR, 'dataset_report.json')

LABEL_MAPPINGS = {
    "MangoDHDS": {
        "Anthracnose": {"unified": "Anthracnose", "decision": "Direct match: Colletotrichum gloeosporioides fungal anthracnose."},
        "Bacterial Canker": {"unified": "Bacterial Canker", "decision": "Direct match: Xanthomonas campestris pv. mangiferaeindicae bacterial lesions."},
        "Healthy": {"unified": "Healthy", "decision": "Direct match: Sound healthy unblemished fruit."},
        "Scab": {"unified": "Scab", "decision": "Direct match: Elsinoe mangiferae fruit scab spots."},
        "Stem End Rot": {"unified": "Stem End Rot", "decision": "Direct match: Lasiodiplodia theobromae stem-end decay."}
    },
    "MangoFruitBD": {
        "0": {"original_name": "Alternaria", "unified": "Other", "decision": "Mapped to Other: Alternaria black spot is a distinct fungal decay class."},
        "1": {"original_name": "Anthracnose", "unified": "Anthracnose", "decision": "Direct match: Anthracnose."},
        "2": {"original_name": "Healthy", "unified": "Healthy", "decision": "Direct match: Sound healthy mango."},
        "3": {"original_name": "Scab", "unified": "Scab", "decision": "Direct match: Fruit scab."}
    },
    "MangoFruitDDS": {
        "Anthracnose": {"unified": "Anthracnose", "decision": "Direct match: Anthracnose."},
        "Healthy": {"unified": "Healthy", "decision": "Direct match: Sound healthy mango."},
        "Stem end Rot": {"unified": "Stem End Rot", "decision": "Direct match: Stem end rot decay."},
        "Stem and Rot": {"unified": "Stem End Rot", "decision": "Direct match: Typo variant of Stem end Rot in dataset."},
        "Alternaria": {"unified": "Other", "decision": "Mapped to Other: Alternaria decay."},
        "Black Mould Rot": {"unified": "Other", "decision": "Mapped to Other: Aspergillus niger black mould rot."}
    }
}

def ensure_extracted():
    """Verify raw ZIPs exist and extract if not already present."""
    os.makedirs(EXTRACTED_DIR, exist_ok=True)
    os.makedirs(CROPS_DIR, exist_ok=True)
    os.makedirs(MANIFESTS_DIR, exist_ok=True)
    os.makedirs(SPLITS_DIR, exist_ok=True)

    # 1. MangoDHDS
    dhds_raw = os.path.join(RAW_DIR, 'MangoDHDS.zip')
    dhds_target = os.path.join(EXTRACTED_DIR, 'MangoDHDS')
    if os.path.exists(dhds_raw) and not os.path.exists(dhds_target):
        print("[Extract] Extracting MangoDHDS.zip...")
        os.makedirs(dhds_target, exist_ok=True)
        with zipfile.ZipFile(dhds_raw, 'r') as z:
            for n in z.namelist():
                if n.endswith('.zip'):
                    cname = os.path.splitext(os.path.basename(n))[0].replace(' ', '_')
                    t_dir = os.path.join(dhds_target, cname)
                    os.makedirs(t_dir, exist_ok=True)
                    inner_bytes = z.read(n)
                    with zipfile.ZipFile(io.BytesIO(inner_bytes), 'r') as iz:
                        iz.extractall(t_dir)

    # 2. MangoFruitDDS
    dds_raw = os.path.join(RAW_DIR, 'MangoFruitDDs.zip')
    dds_target = os.path.join(EXTRACTED_DIR, 'MangoFruitDDS')
    if os.path.exists(dds_raw) and not os.path.exists(dds_target):
        print("[Extract] Extracting MangoFruitDDs.zip...")
        with zipfile.ZipFile(dds_raw, 'r') as z:
            z.extractall(EXTRACTED_DIR)

    # 3. MangoFruitBD
    bd_raw = os.path.join(RAW_DIR, 'MangoFruitBD.zip')
    bd_target = os.path.join(EXTRACTED_DIR, 'MangoFruitBD')
    if os.path.exists(bd_raw) and not os.path.exists(bd_target):
        print("[Extract] Extracting MangoFruitBD.zip...")
        with zipfile.ZipFile(bd_raw, 'r') as z:
            z.extractall(EXTRACTED_DIR)

def process_mangodhds(manifest):
    base_dir = os.path.join(EXTRACTED_DIR, 'MangoDHDS')
    if not os.path.exists(base_dir):
        return 0

    class_folder_map = {
        'Anthracnose': 'Anthracnose',
        'Bacterial_Canker': 'Bacterial Canker',
        'Healthy': 'Healthy',
        'Scab': 'Scab',
        'Stem_End_Rot': 'Stem End Rot'
    }

    count = 0
    for folder, orig_class in class_folder_map.items():
        sub = os.path.join(base_dir, folder)
        unified = LABEL_MAPPINGS['MangoDHDS'][orig_class]['unified']
        # Locate all images inside
        for root, _, files in os.walk(sub):
            for f in files:
                if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, WORKSPACE_ROOT).replace('\\', '/')
                    sample_id = f"DHDS_{orig_class}_{f}"
                    group_id = f"DHDS_{f.split('.')[0]}"
                    manifest.append({
                        "sample_id": sample_id,
                        "image_path": rel_p,
                        "dataset_source": "MangoDHDS",
                        "original_class": orig_class,
                        "unified_class": unified,
                        "group_id": group_id,
                        "is_crop": False,
                        "bbox": None
                    })
                    count += 1
    return count

def process_mangofruitdds(manifest, excluded_records):
    base_dir = os.path.join(EXTRACTED_DIR, 'MangoFruitDDS')
    if not os.path.exists(base_dir):
        return 0

    # Note: We use SenMangoFruitDDS_original. SenMangoFruitDDS_bgremoved is excluded to prevent identical duplicate sample leakage.
    orig_dir = os.path.join(base_dir, 'SenMangoFruitDDS_original')
    bgrem_dir = os.path.join(base_dir, 'SenMangoFruitDDS_bgremoved')

    if os.path.exists(bgrem_dir):
        for root, _, files in os.walk(bgrem_dir):
            for f in files:
                if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                    excluded_records.append({
                        "file": f,
                        "dataset": "MangoFruitDDS",
                        "reason": "Excluded SenMangoFruitDDS_bgremoved: Duplicate background-removed derivative of original to prevent data leakage."
                    })

    count = 0
    if os.path.exists(orig_dir):
        for folder in os.listdir(orig_dir):
            fpath = os.path.join(orig_dir, folder)
            if not os.path.isdir(fpath):
                continue
            mapping = LABEL_MAPPINGS['MangoFruitDDS'].get(folder)
            if not mapping:
                continue
            unified = mapping['unified']
            for f in os.listdir(fpath):
                if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                    full_p = os.path.join(fpath, f)
                    rel_p = os.path.relpath(full_p, WORKSPACE_ROOT).replace('\\', '/')
                    sample_id = f"DDS_{folder}_{f}"
                    group_id = f"DDS_{f.split('.')[0]}"
                    manifest.append({
                        "sample_id": sample_id,
                        "image_path": rel_p,
                        "dataset_source": "MangoFruitDDS",
                        "original_class": folder,
                        "unified_class": unified,
                        "group_id": group_id,
                        "is_crop": False,
                        "bbox": None
                    })
                    count += 1
    return count

def process_mangofruitbd(manifest):
    base_dir = os.path.join(EXTRACTED_DIR, 'MangoFruitBD')
    if not os.path.exists(base_dir):
        return 0

    splits = ['train', 'val', 'test']
    count = 0

    for s in splits:
        img_dir = os.path.join(base_dir, 'images', s)
        lbl_dir = os.path.join(base_dir, 'labels', s)
        if not os.path.exists(img_dir) or not os.path.exists(lbl_dir):
            continue

        for lbl_file in os.listdir(lbl_dir):
            if not lbl_file.endswith('.txt'):
                continue
            base_name = os.path.splitext(lbl_file)[0]
            # Find corresponding image
            img_file = None
            for ext in ['.jpg', '.jpeg', '.png', '.JPG']:
                candidate = os.path.join(img_dir, base_name + ext)
                if os.path.exists(candidate):
                    img_file = candidate
                    break
            if not img_file:
                continue

            # Read bounding boxes
            with open(os.path.join(lbl_dir, lbl_file), 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]

            if not lines:
                continue

            try:
                with Image.open(img_file) as im:
                    im_w, im_h = im.size
                    im_rgb = im.convert('RGB')

                    for idx, line in enumerate(lines):
                        parts = line.split()
                        if len(parts) < 5:
                            continue
                        cls_id_str = parts[0]
                        mapping = LABEL_MAPPINGS['MangoFruitBD'].get(cls_id_str)
                        if not mapping:
                            continue

                        orig_class = mapping['original_name']
                        unified = mapping['unified']

                        x_c = float(parts[1]) * im_w
                        y_c = float(parts[2]) * im_h
                        box_w = float(parts[3]) * im_w
                        box_h = float(parts[4]) * im_h

                        x1 = max(0, int(x_c - box_w / 2))
                        y1 = max(0, int(y_c - box_h / 2))
                        x2 = min(im_w, int(x_c + box_w / 2))
                        y2 = min(im_h, int(y_c + box_h / 2))

                        if (x2 - x1) < 15 or (y2 - y1) < 15:
                            # Skip degenerate / zero-area crops
                            continue

                        crop_im = im_rgb.crop((x1, y1, x2, y2))
                        crop_fname = f"BD_{s}_{base_name}_box{idx}.jpg"
                        crop_path = os.path.join(CROPS_DIR, crop_fname)
                        crop_im.save(crop_path, quality=90)

                        rel_crop_p = os.path.relpath(crop_path, WORKSPACE_ROOT).replace('\\', '/')
                        sample_id = f"BD_{base_name}_{idx}"
                        # CRITICAL: group_id is the original parent image name so all boxes stay in same split!
                        group_id = f"BD_{base_name}"

                        manifest.append({
                            "sample_id": sample_id,
                            "image_path": rel_crop_p,
                            "dataset_source": "MangoFruitBD",
                            "original_class": orig_class,
                            "unified_class": unified,
                            "group_id": group_id,
                            "is_crop": True,
                            "bbox": [x1, y1, x2, y2],
                            "parent_image": os.path.relpath(img_file, WORKSPACE_ROOT).replace('\\', '/')
                        })
                        count += 1
            except Exception as e:
                print(f"[Warn] Error processing {img_file}: {e}")

    return count

def split_manifest(manifest, train_ratio=0.8, seed=42):
    """
    Split manifest into 80% TRAIN and 20% TEST strictly grouped by group_id
    with stratification by unified_class to prevent data leakage.
    """
    random.seed(seed)
    np.random.seed(seed)

    # 1. Group records by group_id
    groups = defaultdict(list)
    for rec in manifest:
        groups[rec['group_id']].append(rec)

    # 2. Assign each group a primary class (most frequent class among its items)
    group_classes = {}
    for gid, items in groups.items():
        c_counts = Counter(item['unified_class'] for item in items)
        group_classes[gid] = c_counts.most_common(1)[0][0]

    # 3. Stratified split of groups
    by_class_groups = defaultdict(list)
    for gid, cls in group_classes.items():
        by_class_groups[cls].append(gid)

    train_groups = set()
    test_groups = set()

    for cls, gids in by_class_groups.items():
        random.shuffle(gids)
        split_idx = int(len(gids) * train_ratio)
        train_groups.update(gids[:split_idx])
        test_groups.update(gids[split_idx:])

    train_records = []
    test_records = []

    for rec in manifest:
        if rec['group_id'] in train_groups:
            rec['split'] = 'train'
            train_records.append(rec)
        else:
            rec['split'] = 'test'
            test_records.append(rec)

    return train_records, test_records

def main():
    print("[1/5] Verifying and ensuring datasets are extracted...")
    ensure_extracted()

    manifest = []
    excluded_records = []

    print("[2/5] Processing MangoDHDS...")
    c_dhds = process_mangodhds(manifest)
    print(f"       -> Added {c_dhds} records from MangoDHDS.")

    print("[3/5] Processing MangoFruitDDS...")
    c_dds = process_mangofruitdds(manifest, excluded_records)
    print(f"       -> Added {c_dds} records from MangoFruitDDS.")

    print("[4/5] Processing MangoFruitBD (cropping YOLO bounding boxes)...")
    c_bd = process_mangofruitbd(manifest)
    print(f"       -> Added {c_bd} cropped mango samples from MangoFruitBD.")

    total_samples = len(manifest)
    print(f"Total unified samples gathered: {total_samples}")

    # Generate Label Mapping File
    print("[5/5] Generating mappings, reports, and leakage-safe 80/20 splits...")
    with open(LABEL_MAPPING_PATH, 'w', encoding='utf-8') as f:
        json.dump(LABEL_MAPPINGS, f, indent=2)

    # Perform group-stratified split
    train_records, test_records = split_manifest(manifest, train_ratio=0.8, seed=42)

    # Write manifests
    unified_manifest_path = os.path.join(MANIFESTS_DIR, 'unified_manifest.json')
    with open(unified_manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    train_manifest_path = os.path.join(SPLITS_DIR, 'train_manifest.json')
    with open(train_manifest_path, 'w', encoding='utf-8') as f:
        json.dump(train_records, f, indent=2)

    test_manifest_path = os.path.join(SPLITS_DIR, 'test_manifest.json')
    with open(test_manifest_path, 'w', encoding='utf-8') as f:
        json.dump(test_records, f, indent=2)

    # Generate Dataset Report
    train_counts = Counter(r['unified_class'] for r in train_records)
    test_counts = Counter(r['unified_class'] for r in test_records)
    total_counts = Counter(r['unified_class'] for r in manifest)
    source_counts = Counter(r['dataset_source'] for r in manifest)
    source_train_counts = Counter(r['dataset_source'] for r in train_records)
    source_test_counts = Counter(r['dataset_source'] for r in test_records)

    report = {
        "report_title": "BharatAgri-2 Mango Quality Dataset Preparation & Leakage-Prevention Report",
        "random_seed": 42,
        "split_ratio": "80% Train / 20% Test (Group-Stratified)",
        "leakage_prevention": {
            "method": "Group-level splitting by parent image/fruit entity",
            "rule": "Samples originating from the same photograph (e.g. MangoFruitBD multi-mango boxes) or fruit sequence share a group_id and never cross the train/test barrier.",
            "duplicate_filtering": "SenMangoFruitDDS_bgremoved excluded because it contains identical background-removed duplicates of SenMangoFruitDDS_original."
        },
        "summary": {
            "total_usable_samples": total_samples,
            "train_samples": len(train_records),
            "test_samples": len(test_records),
            "total_unique_groups": len(set(r['group_id'] for r in manifest)),
            "train_groups": len(set(r['group_id'] for r in train_records)),
            "test_groups": len(set(r['group_id'] for r in test_records)),
            "unified_classes": sorted(list(total_counts.keys()))
        },
        "class_distribution_total": dict(total_counts),
        "class_distribution_train": dict(train_counts),
        "class_distribution_test": dict(test_counts),
        "source_distribution_total": dict(source_counts),
        "source_distribution_train": dict(source_train_counts),
        "source_distribution_test": dict(source_test_counts),
        "exclusions": {
            "count": len(excluded_records),
            "reasons": [
                "SenMangoFruitDDS_bgremoved (838 images) excluded to prevent identical sample leakage across splits.",
                "Degenerate bounding boxes (<15px) filtered out during crop extraction."
            ]
        }
    }

    with open(DATASET_REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    print("\n================ DATASET REPORT SUMMARY ================")
    print(f"Total usable samples: {total_samples}")
    print(f"Train samples (80%):  {len(train_records)}")
    print(f"Test samples (20%):   {len(test_records)}")
    print("Class distribution:")
    for cls in sorted(total_counts.keys()):
        print(f"  - {cls:<18}: Total={total_counts[cls]:<5} Train={train_counts[cls]:<5} Test={test_counts[cls]:<5}")
    print("Source distribution:")
    for src, cnt in source_counts.items():
        print(f"  - {src:<18}: {cnt}")
    print(f"Label mapping saved:  {LABEL_MAPPING_PATH}")
    print(f"Dataset report saved: {DATASET_REPORT_PATH}")
    print("========================================================\n")

if __name__ == '__main__':
    main()
