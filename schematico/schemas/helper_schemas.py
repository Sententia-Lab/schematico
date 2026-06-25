from enum import Enum


class CallType(str, Enum):
    DISCOVERY = "discovery"
    GENERATOR = "generator"
