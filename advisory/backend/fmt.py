def inr(x: float, decimals: int = 2) -> str:
    """₹ with Indian digit grouping: ₹1,00,000.00"""
    s = f"{abs(x):.{decimals}f}"
    whole, _, frac = s.partition(".")
    if len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        head = ",".join([head[max(i - 2, 0):i] for i in range(len(head), 0, -2)][::-1])
        whole = f"{head},{tail}"
    return ("−" if x < 0 else "") + "₹" + whole + (f".{frac}" if frac else "")
