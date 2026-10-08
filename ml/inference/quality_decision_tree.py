"""
Decision-Tree Quality Decision Layer for Mango Quality Inspection.
Combines multi-task computer vision feature extraction with transparent,
rule-calibrated decision logic adhering to agricultural quality grading standards
(Codex Alimentarius Standard 184 / AGMARK Mango Grading Standards).

Maps structured visual evidence to:
- Health Status: Healthy, Defective, Uncertain
- Defect Severity: None, Slight, Moderate, Severe
- 6-Tier Quality Grade: Excellent, Very Good, Good, Slightly Defective, Defective, Reject
- Commercial Lot Grade: Grade A, Grade B, Grade C, Reject
- Estimated Total-Surface Severity Range: [min%, max%]
- Grounded Decision Path: Natural-language rule explainability
"""

from typing import Dict, Any, List, Tuple


class MangoQualityDecisionLayer:
    """
    Hierarchical, rule-calibrated Decision Tree layer for agricultural mango grading.
    Evaluates multi-task vision outputs:
    - Task B: Ripeness maturity
    - Task C: Pathogen/lesion predictions
    - Geometry: Visible defect surface percentage, lesion cluster count, texture roughness, color uniformity.
    """

    def __init__(self,
                 max_excellent_defect_pct: float = 1.0,
                 max_very_good_defect_pct: float = 3.0,
                 max_good_defect_pct: float = 8.0,
                 max_slightly_defective_defect_pct: float = 14.0,
                 max_defective_defect_pct: float = 20.0,
                 pathogen_reject_threshold: float = 65.0):
        self.max_excellent_defect_pct = max_excellent_defect_pct
        self.max_very_good_defect_pct = max_very_good_defect_pct
        self.max_good_defect_pct = max_good_defect_pct
        self.max_slightly_defective_defect_pct = max_slightly_defective_defect_pct
        self.max_defective_defect_pct = max_defective_defect_pct
        self.pathogen_reject_threshold = pathogen_reject_threshold

    def evaluate_mango(self,
                       ripeness: str,
                       ripeness_conf: float,
                       defect_class: str,
                       defect_conf: float,
                       visible_defect_pct: float,
                       defect_boxes: List[List[int]],
                       texture_roughness: float = 0.0,
                       chroma_std: float = 0.0) -> Dict[str, Any]:
        """
        Execute decision tree traversal over extracted visual features.
        """
        defect_count = len(defect_boxes)
        decision_path = []

        # 1. Estimate 3D Total-Surface Defect Severity Range:
        # A single 2D camera view observes ~40-50% of the 3D fruit surface.
        # Compute explicit bounded uncertainty interval:
        if visible_defect_pct == 0.0:
            est_min_surface = 0.0
            est_max_surface = 2.5  # conservative upper bound for unseen hemisphere
        else:
            est_min_surface = round(visible_defect_pct * 0.45, 1)
            est_max_surface = round(min(100.0, visible_defect_pct * 1.55), 1)

        # 2. Pathogen / Fungal decay vs Superficial Blemish
        is_pathogen = defect_class in ["Anthracnose", "Stem End Rot", "Bacterial Canker"]
        is_fungal_decay = defect_class in ["Anthracnose", "Stem End Rot"]

        # Branch 1: Severe active fungal rot
        if is_fungal_decay and defect_conf >= self.pathogen_reject_threshold and visible_defect_pct >= 8.0:
            health_status = "Defective"
            defect_severity = "Severe"
            quality_grade = "Reject"
            comm_grade = "Reject"
            decision_path.append(f"Severe active {defect_class} rot detected ({defect_conf:.1f}% conf).")
            decision_path.append(f"Necrotic lesion coverage ({visible_defect_pct}%) warrants lot rejection.")

        # Branch 2: Moderate progressive fungal decay (3.0% - 8.0%)
        elif is_fungal_decay and defect_conf >= self.pathogen_reject_threshold and visible_defect_pct >= 3.0:
            health_status = "Defective"
            defect_severity = "Moderate"
            quality_grade = "Defective"
            comm_grade = "Grade C"
            decision_path.append(f"Moderate {defect_class} pathogen lesions detected ({defect_conf:.1f}% conf).")
            decision_path.append("Produce requires immediate distribution / fast-track processing.")

        # Branch 3: Extensive physical or scab damage (> 20%)
        elif visible_defect_pct >= self.max_defective_defect_pct:
            health_status = "Defective"
            defect_severity = "Severe"
            quality_grade = "Reject"
            comm_grade = "Reject"
            decision_path.append(f"Extensive visible surface damage ({visible_defect_pct}% >= {self.max_defective_defect_pct}%).")

        # Branch 4: Noticeable defect (14% - 20%)
        elif visible_defect_pct > self.max_slightly_defective_defect_pct:
            health_status = "Defective"
            defect_severity = "Moderate"
            quality_grade = "Defective"
            comm_grade = "Grade C"
            decision_path.append(f"Noticeable surface defect ({visible_defect_pct}% surface coverage).")

        # Branch 5: Noticeable superficial blemish (8.0% - 14%)
        elif visible_defect_pct > self.max_good_defect_pct:
            health_status = "Defective" if is_pathogen and defect_conf >= 60.0 else "Healthy"
            defect_severity = "Moderate" if is_pathogen else "Slight"
            quality_grade = "Defective" if is_pathogen else "Slightly Defective"
            comm_grade = "Grade C" if is_pathogen else "Grade B"
            decision_path.append(f"Surface markings covering {visible_defect_pct}% of fruit surface.")
            if is_pathogen:
                decision_path.append(f"Associated with {defect_class} pathogen spots ({defect_conf:.1f}% conf).")

        # Branch 6: Commercial Grade B (3.0% - 8.0%)
        elif visible_defect_pct > self.max_very_good_defect_pct:
            if is_pathogen and defect_conf >= 65.0 and visible_defect_pct >= 5.5:
                health_status = "Defective"
                defect_severity = "Moderate"
                quality_grade = "Slightly Defective"
                comm_grade = "Grade B"
                decision_path.append(f"Localized {defect_class} lesions detected ({visible_defect_pct}% area, {defect_count} spots).")
            else:
                health_status = "Healthy"
                defect_severity = "Slight"
                quality_grade = "Good"
                comm_grade = "Grade B"
                decision_path.append(f"Minor superficial markings ({visible_defect_pct}% area); sound marketable fruit (AGMARK Grade B).")

        # Branch 7: Grade A Sound Fruit (1.0% - 3.0%)
        elif visible_defect_pct > self.max_excellent_defect_pct:
            health_status = "Healthy"
            defect_severity = "None"
            quality_grade = "Very Good"
            comm_grade = "Grade A"
            decision_path.append(f"Clean fruit peel with negligible superficial markings ({visible_defect_pct}% area <= 3.0%; AGMARK Grade A).")

        # Branch 8: Grade A Premium Unblemished (<= 1.0%)
        else:
            health_status = "Healthy"
            defect_severity = "None"
            quality_grade = "Excellent"
            comm_grade = "Grade A"
            decision_path.append(f"Sound, unblemished premium peel (<= {self.max_excellent_defect_pct}% markings; Extra Class Grade A).")

        # Branch 9: Maturity context
        if ripeness == "Not Ripe" and health_status == "Healthy":
            decision_path.append("Pre-climacteric green mature fruit; sound condition for transport and ripening.")
        elif ripeness == "Overripe":
            if quality_grade in ["Excellent", "Very Good"]:
                quality_grade = "Good"
                comm_grade = "Grade B"
                decision_path.append("Quality demoted due to senescent over-ripeness.")
            elif quality_grade == "Good":
                quality_grade = "Slightly Defective"
                comm_grade = "Grade C"
                decision_path.append("Quality demoted due to senescent softening.")

        # Compute combined grade confidence
        if health_status == "Healthy":
            grade_conf = round(min(98.0, max(75.0, 95.0 - visible_defect_pct * 3.0)), 1)
        elif health_status == "Defective":
            grade_conf = round(min(98.0, max(70.0, defect_conf * 0.6 + min(30.0, visible_defect_pct * 2.0))), 1)
        else:
            grade_conf = 65.0

        return {
            "health_status": health_status,
            "defect_severity": defect_severity,
            "quality_grade": quality_grade,
            "commercial_grade": comm_grade,
            "grade_confidence": grade_conf,
            "decision_path": decision_path,
            "visible_defect_pct": visible_defect_pct,
            "estimated_total_surface_severity": {
                "min_pct": est_min_surface,
                "max_pct": est_max_surface,
                "range_str": f"{est_min_surface}% - {est_max_surface}%"
            },
            "grounded_rationale": " ".join(decision_path)
        }
