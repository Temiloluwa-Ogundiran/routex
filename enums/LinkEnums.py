from enum import StrEnum

class AmountType(StrEnum):
    STATIC = "static"
    DYNAMIC = "dynamic"


class LinkType(StrEnum):
    ONE_TIME = "one_time"       # single use
    SUBGROUP = "subgroup"       # limited multiple uses
    RECURRING = "recurring"     # unlimited uses

class LinkMode(StrEnum):
    LIVE = 'live'
    TEST = 'test'