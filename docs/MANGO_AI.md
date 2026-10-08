# Mango AI Quality Inspection Architecture

BharatAgri-2 introduces an experimentally validated, multi-mango AI quality inspection system designed for procurement-centre intake. It operates strictly on **Mango** lots, utilizing an interpretable computer vision pipeline inspired by CIELAB color-space research.

---

## 1. Real-World Sampling Workflow

In real-world agricultural operations at BharatAgri procurement centres:
1. A farmer delivers an arriving lot of mangoes (in sacks or crates).
2. The QC officer draws representative samples (e.g., 5 to 15 mangoes sampled from random sacks).
3. The sampled mangoes are arranged on an intake inspection tray.
4. **A single photograph capturing all sampled mangoes is uploaded or captured via device camera.**
5. The AI system segments each individual fruit, extracts colorimetric features, classifies defects per fruit, and aggregates the results into a lot-level assessment.

---

## 2. End-to-End Technical Pipeline

```text
Input Photograph (Multiple Mangoes)
       │
       ▼
1. Image Validation & Preprocessing
   ├── Dimension, format, and aspect ratio validation
   └── Normalization and contrast checks
       │
       ▼
2. Multi-Mango Detection & Segmentation (MangoDetector)
   ├── OpenCV HSV + Otsu thresholding + Morphological filtering
   ├── Contour isolation and aspect-ratio/area filtering
   ├── Crops individual mango bounding boxes [x, y, w, h]
   └── Draws visual bounding boxes and defect labels on annotated output image
       │
       ▼
3. CIELAB Color Feature Extraction (CIELABFeatureExtractor)
   ├── sRGB → Linear RGB (gamma expansion)
   ├── Linear RGB → CIE 1931 XYZ (D65 standard illuminant reference)
   ├── XYZ → CIELAB (L*, a*, b*)
   └── Feature Engineering (14-D vector):
       • mean_a, mean_b, std_a, std_b
       • median_a, median_b
       • p10_a, p90_a, p10_b, p90_b
       • defect_pixel_ratio (spots where b* deviates into necrotic/anthracnose range)
       • healthy_pixel_ratio
       • (Optionally L* statistics: mean_L, std_L for Model D)
       │
       ▼
4. Machine Learning Inference (MangoQualityScanner)
   ├── Pretrained Scikit-Learn RBF SVM / KNN / Fusion model
   └── Evaluates each individual mango crop into one of 6 unified classes:
       [Healthy, Anthracnose, Bacterial Canker, Scab, Stem End Rot, Other]
       │
       ▼
5. Lot-Level Aggregation & Grading (compute_final_quality_grade)
   ├── Aggregates sample counts: Total detected, count per defect, affected percentage
   ├── Prototype Visual Assessment:
       • affected <= 5% and healthy_pct >= 95%  --> Grade A (Visual)
       • affected <= 15% and healthy_pct >= 85% --> Grade B (Visual)
       • affected <= 30%                        --> Grade C (Visual)
       • affected > 30%                         --> Reject (Visual)
   └── Fuses with Physical QC (Moisture % and Foreign Matter %):
       • Actual measured physical metrics cannot be overridden by AI
       • Produces Final Combined Procurement Grade: Grade A, Grade B, Grade C, or REJECT
```

---

## 3. Dataset Preparation & Leakage Prevention

Raw datasets extracted from local ZIP archives:
- `ml/data/mango/raw/MangoFruitBD.zip`
- `ml/data/mango/raw/MangoDHDS.zip`
- `ml/data/mango/raw/MangoFruitDDS.zip`

### Usable Sample Summary:
- **Total usable samples**: 4,488
- **Train split (80%)**: 3,568 samples (2,916 parent groups)
- **Test split (20%)**: 920 samples (732 parent groups)
- **Random seed**: 42

### Leakage-Safe Group Splitting:
Individual images originating from the same photograph (e.g. multi-mango box annotations from MangoFruitBD) or fruit sequences share a unique `group_id`. Stratified group splitting ensures that **no fruit or photograph cross-contaminates both the train and test sets**. The test set of 920 samples remained completely untouched throughout all cross-validation and hyperparameter tuning.

---

## 4. Model Comparison & Experimental Results

All four architectures were trained with 5-fold cross-validation on the 3,568 training samples and evaluated on the untouched 920 test samples:

| Model Architecture | Feature Representation | CV Macro F1 | Test Accuracy | Macro Precision | Macro Recall | Macro F1 | Weighted F1 | Fit Time |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Model A (RBF SVM)** | a\*, b\* | 0.7394 | 78.15% | 0.7476 | 0.7278 | 0.7360 | 0.7790 | 1.42s |
| **Model B (KNN, k=5)** | a\*, b\* | 0.7014 | 72.93% | 0.6890 | 0.6813 | 0.6844 | 0.7272 | 0.01s |
| **Model C (SVM+KNN Fusion)** | a\*, b\* | 0.7399 | 78.37% | 0.7580 | 0.7390 | 0.7475 | 0.7815 | 1.39s |
| **Model D (RBF SVM with L\*)** | L\*, a\*, b\* | **0.7753** | **81.09%** | **0.7877** | **0.7680** | **0.7745** | **0.8084** | 1.41s |

### Scientific Finding on L\*a\*b\* Representation:
While the Hibiscus leaf research paper argued for dropping the L\* (lightness) channel to gain lighting invariance, our empirical evaluation on mango fruit demonstrates that **retaining L\* improves test accuracy from 78.15% to 81.09% (and Macro F1 from 0.7360 to 0.7745)**. This is because necrotic fungal decay and sunburn on mango skin produce significant luminance attenuation (darkening) that provides critical discriminative signal beyond chromaticity (a\*, b\*) alone.

---

## 5. Storage and Security
- Inspection images are saved to disk under `uploads/mango_inspections/{appointment_id}_{timestamp}.jpg`.
- Bounding box annotations and class probabilities are stored in MySQL relational tables: `ai_quality_inspections` and `ai_inspection_detections`.
- File paths are not directly exposed to unauthenticated users; access requires procurement-centre employee authorization.
