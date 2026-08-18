MILLIMETERS_PER_CENTIMETER = 10.0
DEFAULT_SNOW_TO_LIQUID_RATIO = 10.0


def snowfall_cm_from_swe_mm(
    snow_water_equivalent_mm: float,
    snow_to_liquid_ratio: float = DEFAULT_SNOW_TO_LIQUID_RATIO,
) -> float:
    """Estimate new-snow depth from liquid water equivalent."""
    return (
        snow_water_equivalent_mm
        * snow_to_liquid_ratio
        / MILLIMETERS_PER_CENTIMETER
    )
