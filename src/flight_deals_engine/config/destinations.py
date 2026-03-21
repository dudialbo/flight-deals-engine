from typing import NamedTuple

class DestinationConfig(NamedTuple):
    code: str
    name: str

HOT_DEALS_DESTINATIONS = [
    DestinationConfig("LON", "London"),
    DestinationConfig("PAR", "Paris"),
    DestinationConfig("ATH", "Athens"),
    DestinationConfig("ROM", "Rome"),
    DestinationConfig("MAD", "Madrid"),
    DestinationConfig("BCN", "Barcelona"),
    DestinationConfig("RHO", "Rhodes"),
    DestinationConfig("HER", "Crete"),
]
