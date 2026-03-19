"""
Convert a number to words in Indian numbering system (for invoice amounts).
Supports up to 99,99,99,999 (99 crore+).
"""

_ones = [
    "", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
    "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
    "Seventeen", "Eighteen", "Nineteen",
]
_tens = [
    "", "", "Twenty", "Thirty", "Forty", "Fifty",
    "Sixty", "Seventy", "Eighty", "Ninety",
]


def _two_digits(n):
    if n < 20:
        return _ones[n]
    return (_tens[n // 10] + " " + _ones[n % 10]).strip()


def _three_digits(n):
    if n == 0:
        return ""
    h = n // 100
    rest = n % 100
    parts = []
    if h:
        parts.append(_ones[h] + " Hundred")
    if rest:
        parts.append(_two_digits(rest))
    return " ".join(parts)


def number_to_words(amount):
    """
    Convert a numeric amount to Indian English words.
    Example: 4793.00 → 'Four Thousand Seven Hundred Ninety Three Rupees Only'
    """
    if amount is None or amount == 0:
        return "Zero Rupees Only"

    amount = round(float(amount), 2)
    rupees = int(amount)
    paise = int(round((amount - rupees) * 100))

    if rupees == 0 and paise == 0:
        return "Zero Rupees Only"

    parts = []

    # Crores
    if rupees >= 10000000:
        crore = rupees // 10000000
        parts.append(_two_digits(crore) + " Crore")
        rupees %= 10000000

    # Lakhs
    if rupees >= 100000:
        lakh = rupees // 100000
        parts.append(_two_digits(lakh) + " Lakh")
        rupees %= 100000

    # Thousands
    if rupees >= 1000:
        thou = rupees // 1000
        parts.append(_two_digits(thou) + " Thousand")
        rupees %= 1000

    # Hundreds and below
    if rupees > 0:
        parts.append(_three_digits(rupees))

    result = " ".join(parts) + " Rupees"

    if paise > 0:
        result += " and " + _two_digits(paise) + " Paise"

    result += " Only"
    return "Rs. " + result
