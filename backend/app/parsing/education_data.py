"""Canonical degree keywords used for rule-based education extraction.

Order matters: longer/more specific phrases are listed before the
abbreviations they'd otherwise be shadowed by, so matching can just
walk the list once (see resume_parser.py).
"""

KNOWN_DEGREES: list[str] = [
    "Bachelor of Technology",
    "Bachelor of Engineering",
    "Bachelor of Science",
    "Bachelor of Computer Applications",
    "Master of Technology",
    "Master of Engineering",
    "Master of Science",
    "Master of Computer Applications",
    "Master of Business Administration",
    "B.Tech",
    "BTech",
    "B.E.",
    "BE",
    "B.Sc",
    "BSc",
    "BCA",
    "M.Tech",
    "MTech",
    "M.E.",
    "ME",
    "M.Sc",
    "MSc",
    "MCA",
    "MBA",
    "PhD",
    "Ph.D",
]
