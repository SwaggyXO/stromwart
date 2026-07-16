from dataclasses import dataclass
from math import log


@dataclass(frozen=True)
class DriftResult:
    metric: str
    score: float
    threshold: float
    drifted: bool


class DriftService:
    def population_stability_index(
        self,
        baseline: list[float],
        observed: list[float],
        bins: int = 10,
        threshold: float = 0.2,
    ) -> DriftResult:
        if len(baseline) < bins or len(observed) < bins:
            return DriftResult("psi", 0.0, threshold, False)

        low, high = min(baseline), max(baseline)
        if low == high:
            return DriftResult("psi", 0.0, threshold, False)

        width = (high - low) / bins
        score = 0.0

        for index in range(bins):
            left = low + index * width
            right = high if index == bins - 1 else left + width
            expected = self._fraction(baseline, left, right, index == bins - 1)
            actual = self._fraction(observed, left, right, index == bins - 1)
            expected = max(expected, 0.0001)
            actual = max(actual, 0.0001)
            score += (actual - expected) * log(actual / expected)

        return DriftResult("psi", score, threshold, score >= threshold)

    @staticmethod
    def _fraction(
        values: list[float],
        left: float,
        right: float,
        inclusive: bool,
    ) -> float:
        count = sum(
            left <= value <= right if inclusive else left <= value < right
            for value in values
        )
        return count / len(values)
