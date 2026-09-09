"""Factorized difficulty configuration for v4 attribute-filtering items."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from itertools import product
from math import ceil, comb
from typing import Any, ClassVar


class DifficultyConfigError(ValueError):
    """Raised when a v4 difficulty configuration is invalid."""


@dataclass(frozen=True)
class DifficultyConfig:
    """Three independent generation factors used by the v4 generator."""

    constraint_load: str
    distractor_similarity: str
    information_load: str

    CONSTRAINT_LOADS: ClassVar[dict[str, int]] = {
        "CL1": 3,
        "CL2": 5,
        "CL3": 7,
    }
    DISTRACTOR_SIMILARITIES: ClassVar[tuple[str, ...]] = (
        "DS1_far",
        "DS2_medium",
        "DS3_near",
    )
    INFORMATION_LOADS: ClassVar[tuple[str, ...]] = (
        "IL1_low",
        "IL2_high",
    )

    def __post_init__(self) -> None:
        """Reject unknown factor labels immediately."""
        if self.constraint_load not in self.CONSTRAINT_LOADS:
            raise DifficultyConfigError(f"Unknown constraint_load: {self.constraint_load}")
        if self.distractor_similarity not in self.DISTRACTOR_SIMILARITIES:
            raise DifficultyConfigError(
                f"Unknown distractor_similarity: {self.distractor_similarity}"
            )
        if self.information_load not in self.INFORMATION_LOADS:
            raise DifficultyConfigError(f"Unknown information_load: {self.information_load}")

    @property
    def num_constraints(self) -> int:
        """Return the constraint count controlled by ``constraint_load``."""
        return self.CONSTRAINT_LOADS[self.constraint_load]

    @property
    def cell_id(self) -> str:
        """Return a stable identifier for the full factorial cell."""
        return f"{self.constraint_load}__{self.distractor_similarity}__{self.information_load}"

    def to_dict(self) -> dict[str, object]:
        """Serialize the factor configuration for an item."""
        return {
            "constraint_load": self.constraint_load,
            "num_constraints": self.num_constraints,
            "distractor_similarity": self.distractor_similarity,
            "information_load": self.information_load,
        }

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "DifficultyConfig":
        """Build and validate a configuration from serialized item data."""
        config = cls(
            constraint_load=str(payload.get("constraint_load", "")),
            distractor_similarity=str(payload.get("distractor_similarity", "")),
            information_load=str(payload.get("information_load", "")),
        )
        raw_num_constraints = payload.get("num_constraints")
        if not isinstance(raw_num_constraints, int) or isinstance(raw_num_constraints, bool):
            raise DifficultyConfigError("difficulty_factors.num_constraints must be an integer")
        if raw_num_constraints != config.num_constraints:
            raise DifficultyConfigError(
                f"{config.constraint_load} requires {config.num_constraints} constraints, "
                f"got {raw_num_constraints}"
            )
        return config


def all_difficulty_configs() -> tuple[DifficultyConfig, ...]:
    """Return all 18 cells in stable CL, DS, IL order."""
    return tuple(
        DifficultyConfig(constraint_load, distractor_similarity, information_load)
        for constraint_load, distractor_similarity, information_load in product(
            DifficultyConfig.CONSTRAINT_LOADS,
            DifficultyConfig.DISTRACTOR_SIMILARITIES,
            DifficultyConfig.INFORMATION_LOADS,
        )
    )


def far_violation_threshold(num_constraints: int) -> int:
    """Return the v4.1 DS1 threshold, defined as ``ceil(k / 2)``."""
    if num_constraints < 1:
        raise DifficultyConfigError("num_constraints must be positive")
    return ceil(num_constraints / 2)


def far_signature_capacity(num_constraints: int) -> int:
    """Count distinct nonempty signatures that meet the DS1 threshold."""
    threshold = far_violation_threshold(num_constraints)
    return sum(comb(num_constraints, size) for size in range(threshold, num_constraints + 1))


def validate_distractor_signatures(
    config: DifficultyConfig,
    wrong_signatures: Sequence[Sequence[str]],
) -> tuple[str, ...]:
    """Validate that three wrong-option signatures implement the requested DS level."""
    if len(wrong_signatures) != 3:
        raise DifficultyConfigError(
            f"Expected three distractor signatures, got {len(wrong_signatures)}"
        )
    counts = sorted(len(signature) for signature in wrong_signatures)
    if any(count < 1 for count in counts):
        raise DifficultyConfigError("Every distractor must violate at least one constraint")

    if config.distractor_similarity == "DS1_far":
        threshold = far_violation_threshold(config.num_constraints)
        if any(count < threshold for count in counts):
            raise DifficultyConfigError(
                f"DS1_far distractors must each violate at least {threshold} constraints "
                f"for k={config.num_constraints}, got {counts}"
            )
        unique_count = len({tuple(signature) for signature in wrong_signatures})
        capacity = far_signature_capacity(config.num_constraints)
        if unique_count == 1 and capacity >= 3:
            raise DifficultyConfigError(
                "DS1_far produced three identical signatures even though distinct signatures are feasible"
            )
        if unique_count < 3 and capacity < 3:
            return (
                f"Only {capacity} distinct DS1_far signatures are feasible for "
                f"k={config.num_constraints}",
            )
        return ()
    if config.distractor_similarity == "DS2_medium":
        if counts[0] != 1 or counts[1] < 2:
            raise DifficultyConfigError(
                "DS2_medium requires exactly one one-constraint near miss and two "
                f"multi-constraint distractors, got {counts}"
            )
        return ()
    if counts != [1, 1, 1]:
        raise DifficultyConfigError(
            f"DS3_near distractors must each violate exactly one constraint, got {counts}"
        )
    return ()
