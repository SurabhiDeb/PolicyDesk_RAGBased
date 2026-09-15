"""Statistics for eval scores.

Every number this project reports passes through here, which makes it the one
place a quiet bug would be most expensive.

A bare pass rate is close to meaningless. 19/20 and 190/200 are both "95%" and
they are very different claims. Every rate here carries a confidence interval
so that the sample size is impossible to ignore.
"""

import math
from dataclasses import dataclass

# z-score for a two-sided 95 percent interval
Z_95 = 1.959963984540054


@dataclass(frozen=True)
class Rate:
    """A pass rate together with the evidence behind it."""

    passed: int
    total: int
    point: float
    low: float
    high: float

    def overlaps(self, other):
        """True means a difference between the two is not evidence of anything."""
        return self.low <= other.high and other.low <= self.high

    def __str__(self):
        return (
            f"{self.point:6.1%}  ({self.passed}/{self.total}, "
            f"95% CI {self.low:.0%} to {self.high:.0%})"
        )


def wilson(passed, total, z=Z_95):
    """Wilson score interval for a proportion.

    The textbook formula returns a zero-width interval at 0/20 and 20/20,
    claiming certainty from twenty samples. Wilson stays sensible at the edges
    and at small n, which is where every eval suite lives on day one.
    """
    if total <= 0:
        raise ValueError(f"total must be positive, got {total}")
    if not 0 <= passed <= total:
        raise ValueError(f"passed must be between 0 and {total}, got {passed}")

    n = float(total)
    p = passed / n
    denominator = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denominator
    spread = (z / denominator) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return max(0.0, centre - spread), min(1.0, centre + spread)


def rate(passed, total):
    low, high = wilson(passed, total)
    return Rate(passed, total, passed / total, low, high)


def percentile(values, pct):
    """Nearest-rank percentile. Honest on tiny samples, unlike interpolation."""
    if not values:
        return None
    ordered = sorted(values)
    index = math.ceil(pct / 100 * len(ordered)) - 1
    return ordered[max(0, min(index, len(ordered) - 1))]