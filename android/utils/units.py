"""Unit conversion helpers."""

MM_PER_INCH = 25.4
CM_PER_INCH = 2.54


def to_mm(value: float, unit: str) -> float:
    """Convert a value from the given unit to millimetres."""
    if unit == "mm":
        return value
    if unit == "cm":
        return value * 10.0
    if unit == "inch":
        return value * MM_PER_INCH
    raise ValueError(f"Unknown unit: {unit!r}")


def from_mm(value: float, unit: str) -> float:
    """Convert a value from millimetres to the given unit."""
    if unit == "mm":
        return value
    if unit == "cm":
        return value / 10.0
    if unit == "inch":
        return value / MM_PER_INCH
    raise ValueError(f"Unknown unit: {unit!r}")


def format_value(value_mm: float, unit: str, decimals: int = 1) -> str:
    """Return a formatted string with the unit label."""
    converted = from_mm(value_mm, unit)
    return f"{converted:.{decimals}f} {unit}"
