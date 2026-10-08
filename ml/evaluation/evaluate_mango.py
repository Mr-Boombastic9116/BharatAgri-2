import os
import sys
import json
import joblib
import numpy as np
from collections import Counter
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score

MANGO_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'mango'))
WORKSPACE_ROOT = os.path.abspath(os.path.join(MANGO_DIR, '..', '..'))
SPLITS_DIR = os.path.join(MANGO_DIR, 'splits')
MODELS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'models', 'mango'))
RESULTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'results', 'mango'))

def run_evaluation():
    print("=" * 70)
    print(" BharatAgri-2 Mango AI Model Independent Evaluation")
    print("=" * 70)

    model_path = os.path.join(MODELS_DIR, "mango_best_model.joblib")
    if not os.path.exists(model_path):
        print(f"[Error] Model artifact not found at {model_path}. Run ml.training.train_mango first.")
        return

    meta_path = os.path.join(MODELS_DIR, "model_metadata.json")
    if os.path.exists(meta_path):
        with open(meta_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
        print(f"Model Version: {metadata.get('model_version')}")
        print(f"Model Name:    {metadata.get('best_model_name')}")
        print(f"Trained On:    {metadata.get('training_timestamp')}")

    model = joblib.load(model_path)
    scaler = model.named_steps.get('scaler') if hasattr(model, 'named_steps') else None
    expected_feats = scaler.n_features_in_ if scaler and hasattr(scaler, 'n_features_in_') else 19

    # Load appropriate test cache
    test_cache = os.path.join(RESULTS_DIR, "test_lab.npz" if expected_feats == 24 else "test_ab.npz")
    if not os.path.exists(test_cache):
        print(f"[Error] Test feature cache {test_cache} not found.")
        return

    data = np.load(test_cache, allow_pickle=True)
    X_test = data['X']
    y_test = data['y']
    sample_ids = data['sample_ids']
    classes = data['classes']
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test) if hasattr(model, 'predict_proba') else None

    acc = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average='macro', zero_division=0)
    weighted_f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)

    print(f"\nEvaluation on untouched 20% Test Set ({len(y_test)} samples):")
    print(f"  Accuracy:    {acc*100:.2f}%")
    print(f"  Macro F1:    {macro_f1:.4f}")
    print(f"  Weighted F1: {weighted_f1:.4f}")

    print("\nDetailed Per-Class Performance:")
    clf_rep = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    print(f"{'Class':<20} | {'Precision':<10} | {'Recall':<10} | {'F1-Score':<10} | {'Support':<8}")
    print("-" * 65)
    for c in sorted(list(classes)):
        c_stats = clf_rep.get(c, {})
        print(f"{c:<20} | {c_stats.get('precision', 0.0):>9.4f}  | {c_stats.get('recall', 0.0):>9.4f}  | {c_stats.get('f1-score', 0.0):>9.4f}  | {int(c_stats.get('support', 0)):>7}")
    print("-" * 65)

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=sorted(list(classes)))
    print("\nConfusion Matrix (Rows=True, Cols=Predicted):")
    header = " " * 20 + " | " + " | ".join(f"{c[:4]:<4}" for c in sorted(list(classes)))
    print(header)
    for i, c in enumerate(sorted(list(classes))):
        row_str = " | ".join(f"{cm[i][j]:>4}" for j in range(len(classes)))
        print(f"{c:<20} | {row_str}")

    # Identify failure cases
    failure_cases = []
    for idx, (true_label, pred_label, s_id) in enumerate(zip(y_test, y_pred, sample_ids)):
        if true_label != pred_label:
            conf = float(np.max(y_proba[idx])) if y_proba is not None else 0.0
            failure_cases.append({
                "sample_id": str(s_id),
                "true_class": str(true_label),
                "predicted_class": str(pred_label),
                "confidence": round(conf, 4)
            })

    print(f"\nTotal Misclassified Samples: {len(failure_cases)} / {len(y_test)} ({len(failure_cases)/len(y_test)*100:.2f}%)")
    print("Sample Failure Cases (Top 5):")
    for fc in failure_cases[:5]:
        print(f"  - {fc['sample_id']}: True={fc['true_class']}, Pred={fc['predicted_class']} (Confidence: {fc['confidence']*100:.1f}%)")

    # Save detailed evaluation report to results
    eval_output_path = os.path.join(RESULTS_DIR, "independent_evaluation_report.json")
    out_dict = {
        "evaluation_timestamp": str(np.datetime64('now')),
        "test_sample_count": len(y_test),
        "overall_metrics": {
            "accuracy": round(acc, 4),
            "macro_f1": round(macro_f1, 4),
            "weighted_f1": round(weighted_f1, 4)
        },
        "per_class_metrics": clf_rep,
        "confusion_matrix": {
            "classes": sorted(list(classes)),
            "matrix": cm.tolist()
        },
        "failure_cases_count": len(failure_cases),
        "sample_failure_cases": failure_cases[:20]
    }
    with open(eval_output_path, 'w', encoding='utf-8') as f:
        json.dump(out_dict, f, indent=2)

    print(f"\nSaved detailed evaluation report to {eval_output_path}")

if __name__ == '__main__':
    run_evaluation()
