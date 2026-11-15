"""Months are kept as one whole number: year x 12 + (month - 1). 2026-10 is 2026 * 12 + 9."""
NAMES = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
FULL = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

def mi(label):
    """'2026-10' -> month number."""
    y, m = str(label).strip()[:7].split('-')
    return int(y) * 12 + int(m) - 1

def ml(i):
    """month number -> '2026-10'."""
    return f'{i // 12}-{i % 12 + 1:02d}'

def ym(y, m):
    """year, month (1-12) -> month number."""
    return y * 12 + m - 1

def year(i): return i // 12
def mon(i): return i % 12 + 1          # calendar month 1-12
