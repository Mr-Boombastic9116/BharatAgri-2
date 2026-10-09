import os
import sys
import json
import time
from PIL import Image
import numpy as np

# Ensure workspace root in path
sys.path.insert(0, os.path.abspath('.'))

from ml.inference.mango_quality_scanner import get_mango_quality_scanner

def run_baseline():
    ext_dir = os.path.abspath('ml/data/mango/external_test')
    out_dir = os.path.abspath('ml/results/mango/external_test_baseline')
    vis_dir = os.path.join(out_dir, 'visual_overlays')
    os.makedirs(vis_dir, exist_ok=True)

    scanner = get_mango_quality_scanner()
    files = sorted([f for f in os.listdir(ext_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))])
    
    print(f"Starting baseline run on {len(files)} external unseen test images...", flush=True)
    
    results = []
    total_detected_mangoes = 0
    images_with_detections = 0
    images_failed = 0
    defect_percentages = []
    grade_distribution = {}
    
    t_start = time.time()
    
    for idx, fname in enumerate(files, 1):
        fpath = os.path.join(ext_dir, fname)
        item_res = {
            "filename": fname,
            "status": "success",
            "detected_count": 0,
            "mangoes": [],
            "error": None
        }
        
        t0 = time.time()
        try:
            im = Image.open(fpath).convert('RGB')
            # Normalize excessive dimension > 1280 to prevent O(N*W*H) hanging on 16MP mobile photos
            w, h = im.size
            if max(w, h) > 1280:
                scale = 1280.0 / max(w, h)
                im = im.resize((int(w * scale), int(h * scale)), Image.Resampling.BILINEAR)

            res = scanner.inspect_lot_image(im, inspection_code=f"BASE-{idx:03d}")
            count = res.get("mangoes_detected", 0)
            item_res["detected_count"] = count
            total_detected_mangoes += count
            
            if count > 0:
                images_with_detections += 1
                
            for m_idx, det in enumerate(res.get("detections", [])):
                g = det.get("commercial_grade", det.get("quality_grade", "Unknown"))
                grade_distribution[g] = grade_distribution.get(g, 0) + 1
                pct = det.get("visible_defect_pct", 0.0)
                defect_percentages.append(pct)
                
                item_res["mangoes"].append({
                    "mango_index": m_idx + 1,
                    "bbox": det.get("box"),
                    "area": det.get("area"),
                    "defect_percentage": pct,
                    "defect_type": det.get("defect_type"),
                    "health_status": det.get("health_status"),
                    "ripeness": det.get("ripeness"),
                    "grade": g,
                    "confidence": det.get("confidence")
                })
                
            annotated_bytes = res.get("annotated_image_bytes")
            if annotated_bytes:
                vis_path = os.path.join(vis_dir, f"{os.path.splitext(fname)[0]}_overlay.jpg")
                with open(vis_path, 'wb') as vf:
                    vf.write(annotated_bytes)
                item_res["overlay_path"] = vis_path
                
            dur = round(time.time() - t0, 2)
            print(f"  [{idx:02d}/{len(files)}] {fname} -> {count} mango(es) in {dur}s", flush=True)
                
        except Exception as e:
            dur = round(time.time() - t0, 2)
            images_failed += 1
            item_res["status"] = "error"
            item_res["error"] = str(e)
            print(f"  [{idx:02d}/{len(files)}] {fname} -> ERROR ({dur}s): {e}", flush=True)
            results.append(item_res)
            continue
            
        results.append(item_res)
        
    total_time = round(time.time() - t_start, 2)
    summary = {
        "experiment_name": "BASELINE_EXTERNAL_UNSEEN_TEST_RUN",
        "total_test_images": len(files),
        "total_execution_time_seconds": total_time,
        "successful_process_images": len(files) - images_failed,
        "failed_process_images": images_failed,
        "images_with_detections": images_with_detections,
        "images_zero_detections": (len(files) - images_failed) - images_with_detections,
        "total_detected_mangoes": total_detected_mangoes,
        "average_mangoes_per_detected_image": round(total_detected_mangoes / max(1, images_with_detections), 2),
        "grade_distribution": grade_distribution,
        "average_defect_pct": round(float(np.mean(defect_percentages)), 2) if defect_percentages else 0.0,
        "median_defect_pct": round(float(np.median(defect_percentages)), 2) if defect_percentages else 0.0,
        "max_defect_pct": round(float(np.max(defect_percentages)), 2) if defect_percentages else 0.0,
        "results": results
    }
    
    rep_path = os.path.join(out_dir, "baseline_run_report.json")
    with open(rep_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
        
    print("\n================ BASELINE SUMMARY ================", flush=True)
    print(f"Total images: {len(files)}", flush=True)
    print(f"Execution time: {total_time}s", flush=True)
    print(f"Successfully processed: {len(files) - images_failed}", flush=True)
    print(f"Images with >=1 detected mango: {images_with_detections}", flush=True)
    print(f"Images with 0 detected mangoes: {(len(files) - images_failed) - images_with_detections}", flush=True)
    print(f"Total detected mangoes: {total_detected_mangoes}", flush=True)
    print(f"Grade distribution: {grade_distribution}", flush=True)
    print(f"Report saved to: {rep_path}", flush=True)
    print(f"Visual overlays saved to: {vis_dir}", flush=True)
    print("==================================================", flush=True)

if __name__ == '__main__':
    run_baseline()
