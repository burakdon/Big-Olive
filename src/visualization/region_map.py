"""Region classification for FAOSTAT/IOC olive countries.

Used purely for coloring in visualizations — not a rigorous geopolitical
taxonomy, just a way to group countries so the bubble/bar charts read
clearly (Western Mediterranean vs Eastern Med/Middle East vs North
Africa vs Rest of World).
"""

REGION_MAP = {
    # Western Mediterranean (Iberia + France + Italy + islands)
    "Spain": "Western Mediterranean",
    "France": "Western Mediterranean",
    "Italy": "Western Mediterranean",
    "Portugal": "Western Mediterranean",
    "Malta": "Western Mediterranean",

    # Eastern Mediterranean / Balkans
    "Greece": "Eastern Mediterranean",
    "Türkiye": "Eastern Mediterranean",
    "Cyprus": "Eastern Mediterranean",
    "Albania": "Eastern Mediterranean",
    "Croatia": "Eastern Mediterranean",
    "Bosnia and Herzegovina": "Eastern Mediterranean",
    "Montenegro": "Eastern Mediterranean",
    "North Macedonia": "Eastern Mediterranean",
    "Slovenia": "Eastern Mediterranean",
    "Serbia and Montenegro": "Eastern Mediterranean",
    "Yugoslav SFR": "Eastern Mediterranean",
    "Bulgaria": "Eastern Mediterranean",
    "Romania": "Eastern Mediterranean",

    # North Africa
    "Morocco": "North Africa",
    "Algeria": "North Africa",
    "Tunisia": "North Africa",
    "Libya": "North Africa",
    "Egypt": "North Africa",

    # Middle East
    "Lebanon": "Middle East",
    "Syrian Arab Republic": "Middle East",
    "Israel": "Middle East",
    "Palestine": "Middle East",
    "Jordan": "Middle East",
    "Iraq": "Middle East",
    "Iran (Islamic Republic of)": "Middle East",
    "Saudi Arabia": "Middle East",
    "Kuwait": "Middle East",
    "Azerbaijan": "Middle East",
}

DEFAULT_REGION = "Rest of World"


def assign_region(country: str) -> str:
    return REGION_MAP.get(country, DEFAULT_REGION)
