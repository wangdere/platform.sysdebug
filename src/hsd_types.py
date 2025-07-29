from checker import base_checker
from typing import List, Dict, Tuple, Optional
from enum import Enum     

class SightingFieldEnum(str, Enum):
    status = "status"
    status_reason = "status_reason"
    suspect_area = "suspect_area"
    ingredient = "ingredient"
    exposure = "exposure"


class DebugStage(str, Enum):
    PreSighting = "Pre-sighting"
    Assigned = "Assigned"
    Transferred = "Transferred"
    Root_Caused = "RootCaused"
    Impl_AwaitIngredientRelease = "Impl_AwaitingIngredientRelease"
    Impl_AwaitingVerify = "Impl_AwaitingVerify"
    Verified = "Verified"
    Closed = "Closed"
    Rejected = "Rejected"



class SuspectAreaEnum(str, Enum):
    Silicon = "silicon"
    SystemBoards = "system_boards"
    DRAM = "hardware.component.dram"
    IODevice = "io_device"
    BIOS = "bios"
    BMC_FW = "bmc_fw"
    CPLD = "cpld_fw"
    PFR_CPLD = "pfr"
    OS = "operating_system"
    Simics = "platform.simics"
    DIMM = "DDR5 DIMM"
    DocErrata = "documentation"
    Script = "script"
    Tool = "tool"
    TCD  = "test_content"


class PlatfExposureEnum(str, Enum):
    Critical = "1-critical"
    High = "2-high"
    Medium = "3-medium"
    Low = "4-low"


class PlatfPriority(str, Enum):
    ShowStopper= "p1-showstopper"
    High = "p2-high"
    Medium = "p3-medium"
    Low = "p4-low"

class PlatfStatus(str, Enum):
    open = "open"
    complete = "complete" 
    rejected = "rejected"
    implemented =  "implemented"
    future = "future"
    verified = "verified"
     

class PlatfStatusReason(str, Enum):
    assigned = "open.assigned"
    awaiting_3rd_party = "open.awaiting_3rd_party"
    awaiting_customer = "open.awaiting_customer"
    awaiting_development = "open.awaiting_development"
    awaiting_submitter = "open.awaiting_submitter"
    clone = "open.clone"
    code_review = "open.code_review" 
    development = "open.development"
    new = "open.new"
    promoted= "open.promoted"
    re_open = "open.re-open"
    retest = "open.retest"
    root_caused = "open.root_caused"
    transferred = "open.transferred"
    verify_failed = "open.verify_failed"
    await_user_verify = "implemented.await_user_verify"
    awaiting_ingredient_release  = "implemented.awaiting_ingredient_release"
    awaiting_integration =  "implemented.awaiting_integration"
