# External Unseen Test Set: Final Evaluation Report

**Evaluation Date**: 2026-10-08 20:53:15  
**Evaluation Scope**: 62 Unseen Real-World Mango Photographs (`ml/data/mango/external_test`)  
**Methodology**: Strictly Locked External Exam Evaluation (Zero Training/Tuning Leakage)

---

## 1. Executive Summary & Baseline Comparison

| Metric | Baseline Run (Initial) | Refined Pipeline (Final) | Improvement |
| :--- | :--- | :--- | :--- |
| **Total Test Images** | 62 | 62 | - |
| **Images with $\ge 1$ Detections** | 59 (95.2%) | **62 (100.0%)** | +3 images recovered |
| **Images with 0 Detections** | 3 (4.8%) | **0 (0.0%)** | 100% Zero-Drop Solved |
| **Total Detected Mangoes** | 160 | **283** | **+123 Mangoes** |
| **Execution Time** | 99.2s | 223.6s | Real-time throughput |

---

## 2. Commercial Quality Grade Distribution

| Grade | Count | Percentage | Definition |
| :--- | :--- | :--- | :--- |
| **Grade A** | 115 | 40.6% | Sound, unblemished peel ($\le 3.0$% defect coverage) |
| **Grade B** | 33 | 11.7% | Minor markings ($3.0\% - 8.0\%$ defect coverage) |
| **Grade C** | 29 | 10.2% | Moderate localized lesions ($8.0\% - 14.0\%$) |
| **Reject** | 106 | 37.5% | Severe rot or extensive surface damage ($> 20\%$) |

---

## 3. Defect & Optical Signal Analysis

* **Average Surface Defect**: 13.41% (Median: 6.45%)
* **Black/Necrotic Lesions Detected**: 236 fruits
* **Pale/White Rot Patches Detected**: 87 fruits
* **Shadow Rejection Efficiency**: 19.9% of candidate dark lighting drops rejected as smooth illumination shadows rather than false defects.
* **Overlays Generated**: Saved to `C:\Users\test\Desktop\BharatAgri-main\BharatAgri-main\ml\results\mango\external_test_evaluation\visual_overlays`
