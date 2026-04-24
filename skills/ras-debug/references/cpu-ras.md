# CPU / Uncore RAS -- DMR / Oak Stream

Reference for CPU-side RAS features: MCA architecture, IERR/MCERR signaling,
corrected error flows, and uncore error handling.

---

## Table of Contents
- [MCA Architecture Overview](#mca-architecture-overview)
- [Corrected Error Flow (CE / CMCI)](#corrected-error-flow)
- [Uncorrected Error Flow (UC / IERR)](#uncorrected-error-flow)
- [IERR / MCERR Signaling](#ierr-mcerr)
- [Bank-Specific Decode Guide](#bank-specific-decode-guide)
- [PythonSV -- MCA Debug Scripts](#pythonsv-mca-debug)

---

## MCA Architecture Overview

DMR implements the standard Intel MCA (Machine Check Architecture) with extended
capabilities. Each IP has one or more MC banks that record error status.

### Bank Assignment (DMR)

| Bank | IP | Location | Notes |
|------|----|----------|-------|
| 0 | IFU | Core | Instruction fetch errors |
| 1 | DCU | Core | Data cache unit errors |
| 2 | DTLB | Core | Data TLB errors |
| 3 | MLC | Module | Mid-level cache (L2) errors |
| 4 | Punit (CBB) | CBB | Power management errors |
| 5 | NCU | CBB | Non-coherent unit errors |
| 6 | CCF | Uncore | Cache coherence fabric (merged bank) |
| 7 | D2D (CBB) | CBB | Die-to-die link errors |
| 10 | RASIP | Root | CXL/PCIe RAS IP errors |
| 11 | Punit (IMH) | IMH | IMH power management |
| 12 | HA/MVF | IMH | Home Agent / Miss Vector Filter |
| 13 | HSF | IMH | High-speed fabric |
| 14 | SCA/IOCA | IMH | SCA/IO caching agent |
| 15 | D2D (IMH) | IMH | IMH die-to-die link |
| 16 | MSE | IMH | Memory sub-engine |
| 17 | IOCache | IMH | IO cache |
| 18 | UXI | IMH | UXI (universal cross-point interconnect) |
| 19-26 | MCCHAN0-7 | Memory | Memory channel controllers |

### MCi_STATUS Register Layout (64-bit)

```
Bit 63     = Valid (MCA bank contains a logged error)
Bit 62     = Overflow (multiple errors; first may be lost)
Bit 61     = UC (Uncorrected -- 1) / Corrected (0)
Bit 60     = EN (enabled by MCG_CTL)
Bit 59     = MISCV (MCi_MISC valid)
Bit 58     = ADDRV (MCi_ADDR valid -- address of error)
Bit 57     = PCC (Processor Context Corrupted -- system must reset)
Bits 56:32 = Reserved / vendor-specific (DMR extensions)
Bits 31:16 = MSCOD (Model-Specific error CODe)
Bits 15:0  = MCACOD (MCA error CODe -- architecture-defined categories)
```

### MCACOD Categories (bits 15:0)

| Value | Error Category |
|-------|---------------|
| 0x0001 | No Error (status invalid) |
| 0x000X | Internal error |
| 0x04XX | Memory hierarchy error (cache levels) |
| 0x08XX | Bus/interconnect error |
| 0x0080 | Memory Error -- Generic (correctable) |
| 0x0090 | Memory Error -- ECC CE |
| 0x0400 | Internal timer (watchdog) |
| 0x110A | Generic error (TOR timeout) |

---

## Corrected Error Flow

When a corrected error (CE) occurs in any IP:

```
1. Hardware detects CE -> logs MCi_STATUS (Valid=1, UC=0)
2. MCi_STATUS.MISCV -> MCi_MISC has additional info (dimm address etc.)
3. MCi_STATUS.ADDRV -> MCi_ADDR has physical address

CE Signaling options (configured by BIOS in BIOS_MCG_CTL):
  Option A: CMCI (Corrected Machine Check Interrupt) -> OS handles
  Option B: SMI -> BIOS RAS handler runs

SMI RAS handler (if BIOS-triggered):
  -> Reads MCi_STATUS, MCi_MISC, MCi_ADDR
  -> Decodes DIMM topology (socket/channel/DIMM/rank)
  -> Updates leaky bucket counter
  -> If threshold exceeded: triggers ADDDC/sparing/disable
  -> Logs EWL entry
  -> Clears MCi_STATUS (writes 0 to clear)

CMCI path (OS-handled):
  -> OS reads MCi_STATUS
  -> Generates WHEA/ACPI GHES record
  -> mcelog / mce-inject track CE count
  -> Linux EDAC driver updates per-DIMM counters
```

### Key BIOS Variables for CE Handling
| Variable | Effect |
|----------|--------|
| `SmiOnCorrectedMemError` | Route CE to BIOS SMI (1) or CMCI (0) |
| `CorrectedMemErrThreshold` | CMCI threshold before OS notified |
| `EmcaEn` | EMCA (Enhanced MCA) mode enables extended WHEA records |

---

## Uncorrected Error Flow

When an uncorrected error (UE) occurs:

```
1. Hardware detects UE -> logs MCi_STATUS (Valid=1, UC=1)

Non-fatal UE (PCC=0, UCNA):
  -> BIOS SMI or OS MCE handler reads status
  -> Error is logged but system continues
  -> May trigger page offlining

Fatal UE (PCC=1):
  -> CPU signals MCERR# (internal) or IERR# (platform)
  -> System halts or generates MCE
  -> BIOS may attempt memory/platform recovery
  -> If recovery fails -> cold reset or shutdown
```

---

## IERR / MCERR

### What They Are
- **MCERR**: Internal CPU signal -- indicates uncorrectable error within the processor
- **IERR**: Platform-visible signal -- indicates machine check error (subset of MCERR)

### IERR Debug Flow
1. Check BIOS log for `IERR` or `MCERR` string
2. Check PCH/BMC for IERR pin status
3. In PythonSV (if system can be brought up): read all MC bank statuses

```python
import namednodes
from pysvtools import server_ip_debug

# Quick IERR check -- read all MC banks
for socket in namednodes.sv.sockets:
    # Core banks
    for cbb in socket.cbbs:
        for compute in cbb.computes:
            for module in compute.modules:
                for bank in range(4):  # IFU, DCU, DTLB, MLC
                    try:
                        status = module.getbypath(f"mca_bank{bank}.mc_status").read()
                        if int(status) & (1 << 63):  # Valid bit
                            print(f"Bank {bank} at {module.target_info.path}: "
                                  f"0x{int(status):016X}")
                    except:
                        pass
```

4. Invoke `mca-log-analyzer` with the MCi_STATUS values
5. If source trace needed: invoke `bios-source-analysis` with IERR context

### MCERR vs IERR Escalation
```
CE -> leaky bucket overflow -> ADDDC/sparing (no MCERR)
CE -> leaky bucket overflow -> threshold -> DIMM disable -> system degraded
UE (UCNA) -> OS WHEA record -> page offline (no MCERR)
UE (PCC=0) -> MCE handler -> may or may not IERR based on platform policy
UE (PCC=1) -> MCERR -> IERR -> system halt / reset
```

---

## Bank-Specific Decode Guide

### MCCHAN Banks (19-26) -- Memory Errors

Most common in RAS debug. MCCHAN banks record memory subsystem errors.

**Common MSCOD values for MCCHAN:**

| MSCOD | Name | Description |
|-------|------|-------------|
| 0x0001 | RD_ECC_ERR | Read ECC error (typical CE/UE) |
| 0x0002 | WR_ECC_ERR | Write ECC error |
| 0x0004 | PATROL_ERR | Error found during patrol scrub |
| 0x0008 | DEMAND_ERR | Error on demand read (user access) |
| 0x0010 | ADDDC_ERR | Error during ADDDC sparing |
| 0x0080 | GENERIC_CE | Generic correctable error |

**MCACOD for memory:**
- 0x0090 = ECC correctable error
- 0x0091 = ECC uncorrectable error
- 0x0080 = Generic memory error

### CCF Bank (6) -- Cache Coherence Fabric

CCF errors often indicate TOR (Tracker Outstanding Request) timeouts or LLC errors.

**Common patterns:**
- MSCOD 0x4000 + MCACOD 0x110A = TOR timeout (most common CCF error)
  -> Root cause is usually a downstream IP not responding (PCIe hang, memory hang)
- MSCOD 0x0001 + MCACOD 0x0005 = Internal parity error

**TOR timeout debug flow:**
1. Decode the CCF MCi_STATUS with `mca-log-analyzer`
2. Check which requestor is hanging (MSCOD TOR_TIMEOUT_ERROR encodes requester)
3. Check downstream IPs: PCIe link status, memory MC status
4. Look for HIOP/SCA/MCCHAN errors that explain the timeout

### MLC Bank (3) -- Mid-Level Cache

MLC 3-strike errors (MSCOD 0xE101) indicate a transaction was retried 3 times without
success. Usually a symptom, not root cause.

Debug: trace which downstream IP the MLC was waiting on.

---

## PythonSV MCA Debug

### Full MCA Dump (recommended starting point)

```python
import namednodes
from pysvtools import server_ip_debug

# Method 1: Use server_ip_debug (preferred)
import json
all_attrs = [a for a in dir(server_ip_debug) 
             if not a.startswith('_') and not callable(getattr(server_ip_debug, a, None))]
errors = {}
for ip in all_attrs:
    try:
        obj = getattr(server_ip_debug, ip)
        if hasattr(obj, 'errors') and hasattr(obj.errors, 'get_mca_status'):
            result = obj.errors.get_mca_status()
            if result:
                errors[ip] = result
    except Exception as e:
        pass
print(json.dumps(errors, indent=2, default=str))
```

### Read MCCHAN Status Directly

```python
import namednodes

for socket in namednodes.sv.sockets:
    for imh in socket.imhs:
        for mc_idx, mc in enumerate(imh.memss.mcs):
            for subch_idx, subch in enumerate(mc.subchs):
                try:
                    status = subch.mcdata.mc_status.read()
                    if int(status) & (1 << 63):  # Valid bit set
                        print(f"Socket {socket.target_info.instance} "
                              f"IMH{imh.target_info.instance} "
                              f"MC{mc_idx} SubCh{subch_idx}: "
                              f"MCi_STATUS=0x{int(status):016X}")
                        # Decode fields
                        uc = (int(status) >> 61) & 1
                        pcc = (int(status) >> 57) & 1
                        mscod = (int(status) >> 16) & 0xFFFF
                        mcacod = int(status) & 0xFFFF
                        print(f"  UC={uc} PCC={pcc} MSCOD=0x{mscod:04X} "
                              f"MCACOD=0x{mcacod:04X}")
                except:
                    pass
```

### Check if Any MCA Valid Bits Are Set (Quick Health Check)

```python
import namednodes

any_error = False
for socket in namednodes.sv.sockets:
    for imh in socket.imhs:
        for mc in imh.memss.mcs:
            for subch in mc.subchs:
                try:
                    status = int(subch.mcdata.mc_status.read())
                    if status & (1 << 63):
                        print(f"ERROR: {subch.target_info.path} = 0x{status:016X}")
                        any_error = True
                except:
                    pass
if not any_error:
    print("No MCCHAN MCA errors found")
```
