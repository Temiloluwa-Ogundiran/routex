from enum import StrEnum

class TokenMode(StrEnum):
    LIVE = 'live'
    TEST = 'test'
    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls._value2member_map_
class TokenType(StrEnum):
    PUBLIC = 'pk'
    SECRET =  'sk'
    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls._value2member_map_