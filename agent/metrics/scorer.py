"""
CodeSage Performance Scorer

Implements the Composite Weighted Score (CWS) methodology
on a 1–10,000 scale for evaluating agent performance.

Score Formula:
    CWS = (Accuracy × 0.30) + (Depth × 0.25) + (Actionability × 0.20)
          + (Safety × 0.15) + (Speed × 0.10)

Each dimension is scored 0–2,000; maximum total is 10,000.
"""

from __future__ import annotations

import time
from dataclasses import dataclass


WEIGHTS = {
    "accuracy": 0.30,
    "depth": 0.25,
    "actionability": 0.20,
    "safety": 0.15,
    "speed": 0.10,
}

DIMENSION_MAX = 2_000
TOTAL_MAX = 10_000
DEVELOPER_BASELINE_SECONDS = 1_200  # 20 minutes — senior dev baseline


@dataclass
class DimensionScore:
    """Score for a single evaluation dimension."""
    raw: float          # 0.0–1.0
    score: int          # 0–2,000
    notes: str = ""


@dataclass
class EvaluationResult:
    """Full evaluation result for a single agent run."""
    accuracy: DimensionScore
    depth: DimensionScore
    actionability: DimensionScore
    safety: DimensionScore
    speed: DimensionScore
    composite: int      # 0–10,000 (the CWS)
    grade: str          # S/A/B/C/D

    def to_dict(self) -> dict:
        return {
            "composite_score": self.composite,
            "grade": self.grade,
            "max_possible": TOTAL_MAX,
            "dimensions": {
                "accuracy":      {"raw": self.accuracy.raw,      "score": self.accuracy.score},
                "depth":         {"raw": self.depth.raw,         "score": self.depth.score},
                "actionability": {"raw": self.actionability.raw, "score": self.actionability.score},
                "safety":        {"raw": self.safety.raw,        "score": self.safety.score},
                "speed":         {"raw": self.speed.raw,         "score": self.speed.score},
            },
        }


class PerformanceScorer:
    """
    Evaluates a CodeSage run against expert ground truth.

    Usage:
        scorer = PerformanceScorer(ground_truth=expert_issues)
        result = scorer.evaluate(
            found_issues=agent_issues,
            patches_applied=84,
            patches_total=100,
            elapsed_seconds=120,
        )
        print(result.composite)  # e.g. 8805
    """

    def __init__(self, ground_truth: list[dict]):
        """
        Args:
            ground_truth: Expert-labeled list of issues. Each dict must have
                          'severity', 'category', 'file', and optionally 'line'.
        """
        self.ground_truth = ground_truth
        self._security_issues = [
            i for i in ground_truth if i.get("category") == "SECURITY"
        ]

    def evaluate(
        self,
        found_issues: list[dict],
        patches_applied: int,
        patches_total: int,
        elapsed_seconds: float,
        cross_file_found: int = 0,
        cross_file_total: int = 1,
    ) -> EvaluationResult:
        """
        Compute the full CWS for an agent run.

        Args:
            found_issues: Issues the agent reported.
            patches_applied: Number of suggested code patches that applied cleanly.
            patches_total: Total number of patches suggested.
            elapsed_seconds: Wall-clock time of the agent run.
            cross_file_found: Cross-file issues the agent correctly identified.
            cross_file_total: Total cross-file issues in ground truth.
        """
        accuracy = self._score_accuracy(found_issues)
        depth = self._score_depth(found_issues, cross_file_found, cross_file_total)
        actionability = self._score_actionability(patches_applied, patches_total)
        safety = self._score_safety(found_issues)
        speed = self._score_speed(elapsed_seconds)

        composite = int(
            accuracy.score * WEIGHTS["accuracy"]
            + depth.score * WEIGHTS["depth"]
            + actionability.score * WEIGHTS["actionability"]
            + safety.score * WEIGHTS["safety"]
            + speed.score * WEIGHTS["speed"]
        )

        return EvaluationResult(
            accuracy=accuracy,
            depth=depth,
            actionability=actionability,
            safety=safety,
            speed=speed,
            composite=composite,
            grade=self._letter_grade(composite),
        )

    # ── Dimension Scorers ────────────────────────────────────────────────────

    def _score_accuracy(self, found: list[dict]) -> DimensionScore:
        """
        Precision × Recall F1 of found issues vs. ground truth.
        Matched on (category, file) pair. Severity mismatch = partial credit.
        """
        if not self.ground_truth:
            return DimensionScore(raw=1.0, score=DIMENSION_MAX, notes="No ground truth to compare")

        matched = 0
        for gt in self.ground_truth:
            for found_issue in found:
                if (
                    found_issue.get("category") == gt.get("category")
                    and self._paths_match(found_issue.get("file", ""), gt.get("file", ""))
                ):
                    matched += 1
                    break

        recall = matched / len(self.ground_truth)
        precision = matched / len(found) if found else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        return DimensionScore(
            raw=f1,
            score=int(f1 * DIMENSION_MAX),
            notes=f"Matched {matched}/{len(self.ground_truth)} ground truth issues",
        )

    def _score_depth(self, found: list[dict], cross_file_found: int, cross_file_total: int) -> DimensionScore:
        """
        Measures cross-file understanding: did the agent find issues that
        span multiple files, not just surface-level single-file issues?
        """
        if cross_file_total == 0:
            return DimensionScore(raw=1.0, score=DIMENSION_MAX, notes="No cross-file issues in test")
        raw = cross_file_found / cross_file_total
        return DimensionScore(
            raw=raw,
            score=int(raw * DIMENSION_MAX),
            notes=f"Cross-file issues: {cross_file_found}/{cross_file_total}",
        )

    def _score_actionability(self, applied: int, total: int) -> DimensionScore:
        """Percentage of suggested patches that apply cleanly."""
        if total == 0:
            return DimensionScore(raw=0.0, score=0, notes="No patches generated")
        raw = applied / total
        return DimensionScore(
            raw=raw,
            score=int(raw * DIMENSION_MAX),
            notes=f"Patches applied cleanly: {applied}/{total}",
        )

    def _score_safety(self, found: list[dict]) -> DimensionScore:
        """
        Security recall: what fraction of expert-labeled security issues did
        the agent catch? False negatives on security = very costly.
        """
        if not self._security_issues:
            return DimensionScore(raw=1.0, score=DIMENSION_MAX, notes="No security issues in ground truth")

        found_security = [i for i in found if i.get("category") == "SECURITY"]
        matched = 0
        for gt_sec in self._security_issues:
            for f in found_security:
                if self._paths_match(f.get("file", ""), gt_sec.get("file", "")):
                    matched += 1
                    break

        raw = matched / len(self._security_issues)
        return DimensionScore(
            raw=raw,
            score=int(raw * DIMENSION_MAX),
            notes=f"Security recall: {matched}/{len(self._security_issues)}",
        )

    def _score_speed(self, elapsed_seconds: float) -> DimensionScore:
        """
        Speed relative to a senior developer baseline (20 min = 1,200 sec).
        Agent must be at least 5× faster to score full marks.
        Penalizes proportionally for slower runs.
        """
        speedup = DEVELOPER_BASELINE_SECONDS / max(elapsed_seconds, 1)
        # Full marks at 5× speedup, 0 at 1× (same as developer)
        raw = min(speedup / 5.0, 1.0)
        return DimensionScore(
            raw=raw,
            score=int(raw * DIMENSION_MAX),
            notes=f"Elapsed: {elapsed_seconds:.1f}s (baseline: {DEVELOPER_BASELINE_SECONDS}s), speedup: {speedup:.1f}×",
        )

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _paths_match(a: str, b: str) -> bool:
        """Fuzzy path match: either path ends with the other's filename."""
        return Path(a).name == Path(b).name if a and b else False

    @staticmethod
    def _letter_grade(score: int) -> str:
        if score >= 9_000:
            return "S"
        if score >= 7_500:
            return "A"
        if score >= 6_000:
            return "B"
        if score >= 4_000:
            return "C"
        return "D"


from pathlib import Path
