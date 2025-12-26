from enum import Enum

class State(str, Enum):
    Discover = "Discover"
    Validate = "Validate"
    Sync = "Sync"
    Arm = "Arm"
    Deliver = "Deliver"
    Cooldown = "Cooldown"
    PostCheckAudit = "PostCheckAudit"
