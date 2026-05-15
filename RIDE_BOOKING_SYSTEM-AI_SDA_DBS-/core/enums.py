from __future__ import annotations

from enum import Enum


class UserRole(str, Enum):
    rider = "rider"
    driver = "driver"
    admin = "admin"


class RideStatus(str, Enum):
    requested = "requested"
    offered = "offered"
    accepted = "accepted"
    in_progress = "in_progress"
    completed = "completed"
    cancelled = "cancelled"


class RideType(str, Enum):
    ridex = "ridex"
    ridexl = "ridexl"
    comfort = "comfort"


class PaymentStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    refunded = "refunded"
    partially_refunded = "partially_refunded"
    cancelled = "cancelled"
