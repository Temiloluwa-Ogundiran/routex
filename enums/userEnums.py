from enum import StrEnum

class UserRole(StrEnum):
    ADMIN = 'admin'
    OWNER = 'owner'
    DEVELOPER = 'developer'
    OPERATIONS = 'operations'
    
    @classmethod
    def is_valid(cls, value: str) -> bool:
        return value in cls._value2member_map_