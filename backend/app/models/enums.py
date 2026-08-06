from enum import StrEnum


class Provider(StrEnum):
    ITAKA = "itaka"
    TUI = "tui"
    RAINBOW = "rainbow"
    WAKACJE_PL = "wakacje_pl"


class MealType(StrEnum):
    ALL_INCLUSIVE = "all_inclusive"
    FULL_BOARD = "full_board"
    HALF_BOARD = "half_board"
    BED_AND_BREAKFAST = "bed_and_breakfast"
    SELF_CATERING = "self_catering"


class TransportType(StrEnum):
    FLIGHT = "flight"
    SELF_TRANSPORT = "self_transport"
    BUS = "bus"
    TRAIN = "train"
    CRUISE = "cruise"
    UNKNOWN = "unknown"
    OWN = "self_transport"  # Backwards compatibility alias


class AlertType(StrEnum):
    NEW_MATCH = "new_match"
    PRICE_DROP = "price_drop"
    LOWEST_PRICE = "lowest_price"
    HIGH_SCORE = "high_score"
    REAPPEARED = "reappeared"
