import os
import sys
import json
import time
import platform
import joblib
import numpy as np
from datetime import datetime
from collections import Counter

import sklearn
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)

from ml.preprocessing.cielab_extractor import extract_mango_features, get_feature_names

MANGO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'mango'))
WORKSPACE_ROOT = os.path.abspath(os.path.join(MANGO_DIR, '..', '..'))
SPLITS_DIR = os.path.join(MANGO_DIR, 'splits')
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'mango'))
RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'results', 'mango'))

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

class DecisionFusionClassifier(BaseEstimator, ClassifierMixin):
    """
    Decision Fusion combining RBF SVM and KNN probability outputs.
    Inspired by multimodal decision fusion methodology.
    """
    def __init__(self, svm_estimator=None, knn_estimator=None, weight_svm=0.5, weight_knn=0.5):
        self.svm_estimator = svm_estimator
        self.knn_estimator = knn_estimator
        self.weight_svm = weight_svm
        self.weight_knn = weight_knn
        self.classes_ = None

    def fit(self, X, y):
        if self.svm_estimator is None:
            self.svm_estimator = SVC(kernel='rbf', C=5.0, gamma='scale', probability=True, random_state=42)
        if self.knn_estimator is None:
            self.knn_estimator = KNeighborsClassifier(n_neighbors=7, weights='distance')

        self.svm_estimator.fit(X, y)
        self.knn_estimator.fit(X, y)
        self.classes_ = self.svm_estimator.classes_
        return self

    def predict_proba(self, X):
        p_svm = self.svm_estimator.predict_proba(X)
        p_knn = self.knn_estimator.predict_proba(X)
        # Ensure class ordering aligns
        if not np.array_equal(self.svm_estimator.classes_, self.knn_estimator.classes_):
            # Remap knn classes if needed
            knn_class_map = {c: i for i, c in enumerate(self.knn_estimator.classes_)}
            p_knn_aligned = np.zeros_like(p_svm)
            for j, c in enumerate(self.classes_):
                if c in knn_class_map:
                    p_knn_aligned[:, j] = p_knn[:, knn_class_map[c]]
            p_knn = p_knn_aligned

        w_tot = self.weight_svm + self.weight_knn
        w_s = self.weight_svm / w_tot
        w_k = self.weight_knn / w_tot
        p_fused = (w_s * p_svm) + (w_k * p_knn)
        return p_fused

    def predict(self, X):
        proba = self.predict_proba(X)
        max_indices = np.argmax(proba, axis=1)
        return self.classes_[max_indices]

def load_and_extract_features(manifest_path, use_l=False, cache_name="features"):
    """
    Load manifest records and extract CIELAB features.
    Caches features to disk to make retraining fast.
    """
    cache_path = os.path.join(RESULTS_DIR, f"{cache_name}_{'lab' if use_l else 'ab'}.npz")
    if os.path.exists(cache_path):
        print(f"[Cache] Loading cached features from {cache_path}...")
        data = np.load(cache_path, allow_pickle=True)
        return data['X'], data['y'], data['sample_ids'], data['classes']

    with open(manifest_path, 'r', encoding='utf-8') as f:
        records = json.load(f)

    X_list = []
    y_list = []
    sample_ids = []
    skipped = 0

    print(f"[Extract] Extracting features for {len(records)} samples (use_l={use_l})...")
    t0 = time.time()
    for i, rec in enumerate(records):
        img_rel = rec['image_path']
        full_img_p = os.path.join(WORKSPACE_ROOT, img_rel)
        if not os.path.exists(full_img_p):
            skipped += 1
            continue

        try:
            vec = extract_mango_features(full_img_p, use_l=use_l)
            X_list.append(vec)
            y_list.append(rec['unified_class'])
            sample_ids.append(rec['sample_id'])
        except Exception as e:
            skipped += 1

        if (i + 1) % 500 == 0 or (i + 1) == len(records):
            elapsed = time.time() - t0
            print(f"  Processed {i+1}/{len(records)} in {elapsed:.1f}s (skipped: {skipped})")

    X = np.array(X_list, dtype=np.float32)
    y = np.array(y_list)
    classes = np.unique(y)

    np.savez_compressed(cache_path, X=X, y=y, sample_ids=sample_ids, classes=classes)
    print(f"[Cache] Saved features to {cache_path} (shape={X.shape}).")
    return X, y, sample_ids, classes

def train_and_evaluate_all():
    train_manifest = os.path.join(SPLITS_DIR, 'train_manifest.json')
    test_manifest = os.path.join(SPLITS_DIR, 'test_manifest.json')

    if not os.path.exists(train_manifest) or not os.path.exists(test_manifest):
        raise FileNotFoundError("Splits not found. Please run ml.data.prepare_mango_data first.")

    # 1. Load Train & Test features for a*, b* chromaticity features
    print("\n--- [Phase 1] Extracting a*, b* Chromaticity Features ---")
    X_train_ab, y_train_ab, train_ids_ab, classes_ab = load_and_extract_features(train_manifest, use_l=False, cache_name="train")
    X_test_ab, y_test_ab, test_ids_ab, _ = load_and_extract_features(test_manifest, use_l=False, cache_name="test")

    # 2. Load Train & Test features for L*, a*, b* (for the comparison)
    print("\n--- [Phase 2] Extracting L*, a*, b* Features ---")
    X_train_lab, y_train_lab, _, _ = load_and_extract_features(train_manifest, use_l=True, cache_name="train")
    X_test_lab, y_test_lab, _, _ = load_and_extract_features(test_manifest, use_l=True, cache_name="test")

    print(f"\nTraining set size: {len(X_train_ab)} samples, {X_train_ab.shape[1]} a*b* features.")
    print(f"Test set size:     {len(X_test_ab)} samples (Untouched during model tuning).")

    # Models definition
    models_to_train = {
        "Model A (RBF SVM, a*b*)": {
            "features": "a*, b*",
            "use_l": False,
            "pipeline": Pipeline([
                ('scaler', StandardScaler()),
                ('clf', SVC(kernel='rbf', C=10.0, gamma='scale', probability=True, random_state=42))
            ])
        },
        "Model B (KNN, a*b*)": {
            "features": "a*, b*",
            "use_l": False,
            "pipeline": Pipeline([
                ('scaler', StandardScaler()),
                ('clf', KNeighborsClassifier(n_neighbors=9, weights='distance'))
            ])
        },
        "Model C (SVM + KNN Fusion, a*b*)": {
            "features": "a*, b*",
            "use_l": False,
            "pipeline": Pipeline([
                ('scaler', StandardScaler()),
                ('clf', DecisionFusionClassifier(
                    svm_estimator=SVC(kernel='rbf', C=10.0, gamma='scale', probability=True, random_state=42),
                    knn_estimator=KNeighborsClassifier(n_neighbors=9, weights='distance'),
                    weight_svm=0.6,
                    weight_knn=0.4
                ))
            ])
        },
        "Model D (Optional: RBF SVM, L*a*b*)": {
            "features": "L*, a*, b*",
            "use_l": True,
            "pipeline": Pipeline([
                ('scaler', StandardScaler()),
                ('clf', SVC(kernel='rbf', C=10.0, gamma='scale', probability=True, random_state=42))
            ])
        }
    }

    comparison_results = []
    detailed_metrics = {}
    best_model_name = None
    best_macro_f1 = -1.0
    best_pipeline = None

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    for m_name, cfg in models_to_train.items():
        print(f"\nEvaluating {m_name}...")
        X_tr = X_train_lab if cfg['use_l'] else X_train_ab
        y_tr = y_train_lab if cfg['use_l'] else y_train_ab
        X_te = X_test_lab if cfg['use_l'] else X_test_ab
        y_te = y_test_lab if cfg['use_l'] else y_test_ab

        # 5-fold Cross-Validation strictly inside the 80% train set
        cv_scores = cross_val_score(cfg['pipeline'], X_tr, y_tr, cv=cv, scoring='f1_macro', n_jobs=-1)
        cv_macro_f1 = float(np.mean(cv_scores))
        print(f"  5-Fold CV Macro F1 (Train Only): {cv_macro_f1:.4f} (+/- {np.std(cv_scores):.4f})")

        # Fit on entire 80% training set
        t_fit_start = time.time()
        cfg['pipeline'].fit(X_tr, y_tr)
        fit_time = time.time() - t_fit_start

        # Evaluate once on untouched 20% test set
        y_pred = cfg['pipeline'].predict(X_te)
        acc = float(accuracy_score(y_te, y_pred))
        macro_prec = float(precision_score(y_te, y_pred, average='macro', zero_division=0))
        macro_rec = float(recall_score(y_te, y_pred, average='macro', zero_division=0))
        macro_f1 = float(f1_score(y_te, y_pred, average='macro', zero_division=0))
        weighted_f1 = float(f1_score(y_te, y_pred, average='weighted', zero_division=0))

        report_dict = classification_report(y_te, y_pred, output_dict=True, zero_division=0)
        c_matrix = confusion_matrix(y_te, y_pred, labels=sorted(list(classes_ab))).tolist()

        res_entry = {
            "model_name": m_name,
            "features": cfg['features'],
            "cv_macro_f1": round(cv_macro_f1, 4),
            "test_accuracy": round(acc, 4),
            "macro_precision": round(macro_prec, 4),
            "macro_recall": round(macro_rec, 4),
            "macro_f1": round(macro_f1, 4),
            "weighted_f1": round(weighted_f1, 4),
            "fit_time_seconds": round(fit_time, 2)
        }
        comparison_results.append(res_entry)

        detailed_metrics[m_name] = {
            "summary": res_entry,
            "classification_report": report_dict,
            "confusion_matrix": {
                "labels": sorted(list(classes_ab)),
                "matrix": c_matrix
            }
        }

        print(f"  Test Accuracy:    {acc*100:.2f}%")
        print(f"  Test Macro F1:    {macro_f1:.4f}")
        print(f"  Test Weighted F1: {weighted_f1:.4f}")

        if macro_f1 > best_macro_f1:
            best_macro_f1 = macro_f1
            best_model_name = m_name
            best_pipeline = cfg['pipeline']

    # Save comparison and detailed metrics
    comparison_file = os.path.join(RESULTS_DIR, 'model_comparison.json')
    with open(comparison_file, 'w', encoding='utf-8') as f:
        json.dump(comparison_results, f, indent=2)

    metrics_file = os.path.join(RESULTS_DIR, 'evaluation_metrics.json')
    with open(metrics_file, 'w', encoding='utf-8') as f:
        json.dump(detailed_metrics, f, indent=2)

    # Save Best Model Artifacts (mango-quality-v1)
    model_version = "mango-quality-v1"
    best_artifact_path = os.path.join(MODELS_DIR, f"{model_version}.joblib")
    joblib.dump(best_pipeline, best_artifact_path)
    print(f"\n[Artifact] Best model saved to: {best_artifact_path}")

    # Also save standard symlink / copy as mango_best_model.joblib for production runtime inference
    production_model_path = os.path.join(MODELS_DIR, "mango_best_model.joblib")
    joblib.dump(best_pipeline, production_model_path)

    # Save model metadata
    model_metadata = {
        "model_version": model_version,
        "best_model_name": best_model_name,
        "training_timestamp": datetime.now().isoformat(),
        "random_seed": 42,
        "python_version": sys.version,
        "scikit_learn_version": sklearn.__version__,
        "os_platform": platform.platform(),
        "feature_representation": "RGB -> CIELAB color space transformation",
        "feature_set": "a*, b* color metrics + lesion roughness + chroma metrics",
        "classes": sorted(list(classes_ab)),
        "split_summary": {
            "train_samples": len(X_train_ab),
            "test_samples": len(X_test_ab),
            "leakage_prevention": "Strict Group-Stratified splitting; zero group crossover between train and test."
        },
        "best_metrics": detailed_metrics[best_model_name]["summary"],
        "comparison_table": comparison_results
    }

    metadata_path = os.path.join(MODELS_DIR, "model_metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(model_metadata, f, indent=2)

    print(f"[Metadata] Model metadata saved to: {metadata_path}")

    # Print pretty comparison table
    print("\n================ MODEL COMPARISON TABLE ================")
    print(f"{'Model':<35} | {'Features':<10} | {'Accuracy':<9} | {'Macro F1':<9} | {'Weighted F1':<11}")
    print("-" * 85)
    for r in comparison_results:
        print(f"{r['model_name']:<35} | {r['features']:<10} | {r['test_accuracy']*100:>7.2f}% | {r['macro_f1']:>9.4f} | {r['weighted_f1']:>11.4f}")
    print("=" * 85)
    print(f"Selected Best Model: {best_model_name} (Macro F1 = {best_macro_f1:.4f})")

if __name__ == '__main__':
    train_and_evaluate_all()
