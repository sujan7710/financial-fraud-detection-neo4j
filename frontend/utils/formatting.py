from typing import Union, Optional

def format_inr(amount: Optional[Union[int, float]], decimals: int = 2, prefix: str = "₹") -> str:
    """
    Format a monetary value according to Indian numbering system (Lakhs and Crores).
    Examples:
        format_inr(1000) -> '₹1,000.00'
        format_inr(100000, decimals=0) -> '₹1,00,000'
        format_inr(1547950) -> '₹15,47,950.00'
        format_inr(10000000, decimals=0) -> '₹1,00,00,000'
    """
    if amount is None:
        return f"{prefix}0.00" if decimals > 0 else f"{prefix}0"

    try:
        amount_num = float(amount)
    except (ValueError, TypeError):
        return f"{prefix}0.00" if decimals > 0 else f"{prefix}0"

    is_negative = amount_num < 0
    amount_abs = abs(amount_num)

    if decimals > 0:
        val_str = f"{amount_abs:.{decimals}f}"
        int_part, dec_part = val_str.split(".")
    else:
        int_part = str(int(round(amount_abs)))
        dec_part = ""

    # Indian numbering: last 3 digits, then pairs of 2 digits
    if len(int_part) <= 3:
        formatted_int = int_part
    else:
        last3 = int_part[-3:]
        remaining = int_part[:-3]
        pairs = []
        while len(remaining) > 2:
            pairs.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            pairs.insert(0, remaining)
        formatted_int = ",".join(pairs) + "," + last3

    sign = "-" if is_negative else ""
    if decimals > 0:
        return f"{sign}{prefix}{formatted_int}.{dec_part}"
    return f"{sign}{prefix}{formatted_int}"


def sanitize_currency_display(text: Optional[str]) -> str:
    """
    Utility to replace legacy dollar symbols with rupee symbols in narrative text.
    Ensures that any API string returning '$' is converted to '₹'.
    """
    if not text:
        return ""
    return text.replace("$", "₹")
