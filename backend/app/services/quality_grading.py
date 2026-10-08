from typing import Dict, Any, Optional

class QualityGradingEngine:
    """
    Configurable Final Quality Grading Engine.
    Combines AI Visual Quality Assessment with instrumental Manual Physical QC measurements
    (moisture content, foreign matter, broken grains, physical observations).
    """

    MOISTURE_FAQ_THRESHOLDS = {
        "Mango": {"min": 75.0, "max": 86.0, "optimum": 82.0},
        "Banana": {"min": 72.0, "max": 78.0, "optimum": 75.0},
        "Tomato": {"min": 90.0, "max": 95.0, "optimum": 93.0},
        "Paddy": {"min": 10.0, "max": 14.0, "optimum": 12.0},
        "Wheat": {"min": 10.0, "max": 12.0, "optimum": 11.0},
        "Maize": {"min": 10.0, "max": 13.5, "optimum": 12.0},
        "Bajra": {"min": 10.0, "max": 12.0, "optimum": 11.5},
        "Cotton": {"min": 6.0, "max": 8.5, "optimum": 7.5},
        "Sugarcane": {"min": 68.0, "max": 74.0, "optimum": 71.0}
    }

    FOREIGN_MATTER_LIMITS = {
        "GRADE_A": 1.0,
        "GRADE_B": 2.0,
        "GRADE_C": 3.0
    }

    @classmethod
    def calculate_final_grade(
        cls,
        crop: str,
        visual_grade: str,
        moisture_pct: float,
        foreign_matter_pct: float,
        ai_confidence: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Combines AI visual assessment with manual physical QC measurements.
        Returns:
            final_grade: 'Grade A' | 'Grade B' | 'Grade C' | 'Reject' | 'Needs Review'
            passed: bool
            penalties: list of reasons
            explanation: detailed human-readable breakdown
        """
        penalties = []
        c_clean = crop.strip()

        # 1. Evaluate Visual Assessment
        v_grade = visual_grade.strip().title()
        if "Reject" in v_grade:
            return {
                "final_grade": "Reject",
                "passed": False,
                "penalties": ["AI visual assessment rejected produce due to excessive defect/disease rate."],
                "explanation": "Produce failed visual standards; defect percentage exceeded tolerable threshold."
            }

        if "Needs Review" in v_grade:
            penalties.append("AI visual assessment flagged lot for human supervisory inspection.")

        # 2. Evaluate Instrumental Moisture Content
        moist_bounds = cls.MOISTURE_FAQ_THRESHOLDS.get(c_clean, {"min": 10.0, "max": 14.0, "optimum": 12.0})
        if moisture_pct > moist_bounds["max"]:
            penalties.append(f"Moisture ({moisture_pct}%) exceeds permissible ceiling ({moist_bounds['max']}%).")
        elif moisture_pct < moist_bounds["min"]:
            penalties.append(f"Moisture ({moisture_pct}%) below standard minimum ({moist_bounds['min']}%).")

        # 3. Evaluate Foreign Matter
        if foreign_matter_pct > cls.FOREIGN_MATTER_LIMITS["GRADE_C"]:
            penalties.append(f"Foreign matter ({foreign_matter_pct}%) exceeds Grade C ceiling (3.0%).")
        elif foreign_matter_pct > cls.FOREIGN_MATTER_LIMITS["GRADE_A"]:
            penalties.append(f"Foreign matter ({foreign_matter_pct}%) exceeds Grade A threshold (1.0%).")

        # 4. Synthesize Final Grade Decision
        if any("Foreign matter" in p and "3.0%" in p for p in penalties):
            final_grade = "Reject"
            passed = False
        elif "Needs Review" in v_grade or (ai_confidence is not None and ai_confidence < 50.0):
            final_grade = "Needs Review"
            passed = False
        elif v_grade == "Grade A" and not penalties:
            final_grade = "Grade A"
            passed = True
        elif v_grade in ["Grade A", "Grade B"] and len(penalties) <= 1:
            final_grade = "Grade B"
            passed = True
        elif v_grade in ["Grade A", "Grade B", "Grade C"] and len(penalties) <= 2:
            final_grade = "Grade C"
            passed = True
        else:
            final_grade = "Reject"
            passed = False

        explanation_parts = [
            f"Visual Inspection: {v_grade}",
            f"Physical Moisture: {moisture_pct}% (Tolerance: {moist_bounds['min']}% - {moist_bounds['max']}%)",
            f"Foreign Matter: {foreign_matter_pct}%"
        ]
        if penalties:
            explanation_parts.append(f"Observations: {'; '.join(penalties)}")

        return {
            "final_grade": final_grade,
            "passed": passed,
            "penalties": penalties,
            "explanation": " | ".join(explanation_parts)
        }


def compute_final_quality_grade(
    crop: str,
    physical_qc: Optional[Any] = None,
    ai_visual_assessment: Optional[str] = None,
    affected_percentage: float = 0.0,
    moisture_pct: Optional[float] = None,
    foreign_matter_pct: Optional[float] = None
) -> Dict[str, Any]:
    """
    Convenience wrapper to compute combined final quality grade from physical QC record and visual assessment.
    """
    moist = moisture_pct
    if moist is None and physical_qc is not None:
        moist = float(getattr(physical_qc, "moisture_content_pct", 12.0) or 12.0)
    if moist is None:
        moist = 12.0

    foreign = foreign_matter_pct
    if foreign is None and physical_qc is not None:
        foreign = float(getattr(physical_qc, "foreign_matter_pct", 1.0) or 1.0)
    if foreign is None:
        foreign = 1.0

    v_grade = ai_visual_assessment or "Grade A"
    return QualityGradingEngine.calculate_final_grade(
        crop=crop,
        visual_grade=v_grade,
        moisture_pct=moist,
        foreign_matter_pct=foreign
    )
