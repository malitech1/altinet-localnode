from __future__ import annotations

from enum import StrEnum


class AccessLevel(StrEnum):
    RESIDENT_OWNER = "resident_owner"
    RESIDENT_ADMIN = "resident_admin"
    RESIDENT_STANDARD = "resident_standard"
    GUEST_FAMILY = "guest_family"
    GUEST_FRIEND = "guest_friend"
    GUEST_VISITOR = "guest_visitor"
    SERVICE_PERSON = "service_person"
    CHILD = "child"
    PET = "pet"
    UNKNOWN = "unknown"
    RESTRICTED = "restricted"
    BLOCKED = "blocked"
    INTRUDER = "intruder"


class AccessCategory(StrEnum):
    RESIDENT = "resident"
    GUEST = "guest"
    SERVICE = "service"
    DEPENDENT = "dependent"
    ANIMAL = "animal"
    UNKNOWN = "unknown"
    THREAT = "threat"


def get_access_category(access_level: AccessLevel) -> AccessCategory:
    mapping = {
        AccessLevel.RESIDENT_OWNER: AccessCategory.RESIDENT,
        AccessLevel.RESIDENT_ADMIN: AccessCategory.RESIDENT,
        AccessLevel.RESIDENT_STANDARD: AccessCategory.RESIDENT,
        AccessLevel.GUEST_FAMILY: AccessCategory.GUEST,
        AccessLevel.GUEST_FRIEND: AccessCategory.GUEST,
        AccessLevel.GUEST_VISITOR: AccessCategory.GUEST,
        AccessLevel.SERVICE_PERSON: AccessCategory.SERVICE,
        AccessLevel.CHILD: AccessCategory.DEPENDENT,
        AccessLevel.PET: AccessCategory.ANIMAL,
        AccessLevel.UNKNOWN: AccessCategory.UNKNOWN,
        AccessLevel.RESTRICTED: AccessCategory.THREAT,
        AccessLevel.BLOCKED: AccessCategory.THREAT,
        AccessLevel.INTRUDER: AccessCategory.THREAT,
    }
    return mapping[access_level]
