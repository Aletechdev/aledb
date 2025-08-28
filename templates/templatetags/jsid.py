import re
from django import template

register = template.Library()

# Allowed: A–Z a–z 0–9 _
# 1) Replace any non-allowed char with "_"
# 2) If the first char is a digit, prepend "_"
_invalid = re.compile(r'[^A-Za-z0-9_]+')

@register.filter(name="jsident")
def jsident(value: str) -> str:
    """
    Sanitize arbitrary strings into valid JavaScript identifiers:
    - Non [A-Za-z0-9_] -> "_"
    - If starts with a digit, prefix with "_"
    """
    if value is None:
        return "_"
    s = str(value)
    s = _invalid.sub('_', s)
    if s and s[0].isdigit():
        s = '_' + s
    # Avoid empty identifiers
    return s or "_"
