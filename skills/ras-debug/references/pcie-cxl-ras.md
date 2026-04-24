# PCIe / CXL RAS -- AER, DPC, CXL Error Handling

Reference for PCIe and CXL RAS features on DMR/Oak Stream.

---

## Table of Contents
- [PCIe AER Overview](#pcie-aer-overview)
- [DPC (Downstream Port Containment)](#dpc)
- [PCIe AER Error Flow in BIOS](#pcie-aer-error-flow)
- [CXL RAS](#cxl-ras)
- [PythonSV -- PCIe/CXL Error Debug](#pythonsv-pciecxl)

---

## PCIe AER Overview

PCIe AER (Advanced Error Reporting) is the PCIe-standard mechanism for reporting
hardware errors (correctable and uncorrectable) from PCIe devices and bridges.

### AER Error Categories

| Category | Type | Description |
|----------|------|-------------|
| **Correctable** | CE | Receiver errors, bad TLP, LCRC error, replay timeout |
| **Uncorrectable Non-Fatal** | NFE | Completion timeout, CA status, unexpected completion |
| **Uncorrectable Fatal** | FE | Data link layer protocol error, surprise down, poisoned TLP |

### AER Register Set (per port)
- `PCI_ERR_UNCOR_STATUS` -- uncorrectable error status (write-1-to-clear)
- `PCI_ERR_COR_STATUS` -- correctable error status
- `PCI_ERR_UNCOR_MASK` -- mask bits for uncorrectable errors
- `PCI_ERR_COR_MASK` -- mask bits for correctable errors
- `PCI_ERR_UNCOR_SEVER` -- severity (NFE vs FE)

### BIOS AER Setup
Key variables:
| Variable | Description |
|----------|-------------|
| `AerEn` | Enable AER (1=enabled, default) |
| `PcieRasMode` | Platform RAS mode for PCIe |
| `DpcEn` | Enable DPC (0=disabled, 1=enabled on FE, 2=enabled on FE+NFE) |

BIOS programs AER registers during PCI enumeration via:
- `PcieSetupAer()` in `ServerPlatformPkg/Pci/`
- Sets masks, severities, ECRC policies

---

## DPC

### What It Is
DPC (Downstream Port Containment) isolates a PCIe port that encounters a fatal error,
preventing the error from corrupting the rest of the fabric. When DPC triggers:
1. The port is taken offline (link disabled)
2. All outstanding transactions are invalidated
3. BIOS (or OS via DPC driver) can then attempt port recovery

### DPC Trigger Events
- **Fatal AER error** (FE): DPC triggers immediately
- **Non-fatal AER** (NFE) if `DpcEn=2`: DPC also triggers
- **RP PIO** (Root Port Programmed I/O error): DPC may trigger depending on policy

### DPC and TOR Timeout Correlation
DPC + CCF TOR timeout is a common failure pattern:
```
PCIe device generates uncorrectable error
    -> Root port AER status set
    -> DPC triggers: link disabled
    -> Outstanding CCF requests to this device time out
    -> CCF TOR timeout MCA: MSCOD 0x4000 MCACOD 0x110A
```
When debugging CCF TOR timeout, always check PCIe AER status first.

### PythonSV -- Check DPC Status

```python
import namednodes

# Check DPC status on root ports
for socket in namednodes.sv.sockets:
    # IO tile contains PCIe root ports
    try:
        io = socket.io0
        # Root port enumeration varies by platform; search for dpc registers
        matches = namednodes.sv.search("dpc_status", getobj=True)
        for match in matches:
            val = int(match.read())
            if val != 0:
                print(f"DPC status at {match.target_info.path}: 0x{val:X}")
    except:
        pass
```

---

## PCIe AER Error Flow

### In BIOS (Pre-OS, DXE phase)
```
PCI enumeration -> BIOS programs AER registers
    v
Training complete -> PCIe devices powered on
    v
AER SMI handler registered (if AerSmiEn=1)
    v
Runtime: AER error detected -> AER SMI fires
    -> BIOS reads AER status registers
    -> Logs WHEA PCIe error record
    -> Clears AER status
    -> If fatal: DPC triggered -> port isolation
```

### Source Locations
```
ServerPlatformPkg/Pci/PciRasHook.c     <- PCIe RAS hooks
ServerRasPkg/Universal/Ras/PcieRas.c   <- PCIe AER SMI handler
ServerPlatformPkg/Pci/PcieAer.c        <- AER register programming
```

---

## CXL RAS

### CXL Error Types

CXL extends PCIe RAS with additional protocols. Error types depend on CXL mode:

| Mode | Errors |
|------|--------|
| CXL.io | Same as PCIe AER (correctable/uncorrectable) |
| CXL.cache | Cache protocol errors, coherency violations |
| CXL.mem | Memory errors (CE/UE) from CXL memory devices |

### CXL.mem Error Flow
```
CXL memory device detects ECC error
    -> Reports via CXL.mem protocol (DVSEC registers)
    -> Root port captures CXL error event
    -> BIOS CXL error handler:
        - Reads CXL error records from device
        - Maps to WHEA memory error section
        - For CE: treat same as DRAM CE (leaky bucket, ADDDC if supported)
        - For UE: escalate to OS for page offline
```

### Key CXL Registers (DMR)
Located under root port / RASIP (Bank 10):
- `CXL_RAS_UNCOR_STATUS` -- uncorrectable CXL errors
- `CXL_RAS_COR_STATUS` -- correctable CXL errors
- `CXL_RAS_CAP_CONTROL` -- enable/disable CXL RAS capability

### BIOS Variables for CXL
| Variable | Description |
|----------|-------------|
| `CxlEn` | CXL protocol enable |
| `CxlRasEn` | CXL RAS error handling |
| `CxlMemCeThreshold` | CE threshold for CXL memory devices |

### Debug: CXL Error Not Being Reported

1. Verify CXL link is up: check DVSEC link status register
2. Check `CxlRasEn` setup variable
3. Check RASIP bank (Bank 10) MCi_STATUS in PythonSV
4. Look for CXL-specific WHEA records in OS event log

```python
import namednodes

# Check RASIP bank (Bank 10) -- CXL/PCIe RAS IP
for socket in namednodes.sv.sockets:
    try:
        # RASIP typically in root tile IO
        matches = socket.search("rasip", getobj=True)
        for m in matches[:3]:
            print(f"RASIP at: {m.target_info.path}")
            m.show()
    except:
        pass
```

---

## PythonSV -- PCIe/CXL Error Debug

### Check PCIe AER Status on All Root Ports

```python
import namednodes

print("=== PCIe AER Status ===")
for socket in namednodes.sv.sockets:
    # Search for AER uncorrectable status registers
    aer_regs = socket.search("aer_uncorr_err_status", getobj=True)
    for reg in aer_regs:
        val = int(reg.read())
        if val != 0:
            print(f"{reg.target_info.path}: AER_UNCORR=0x{val:X}")
            reg.show()

    # Correctable errors
    aer_cor = socket.search("aer_corr_err_status", getobj=True)
    for reg in aer_cor:
        val = int(reg.read())
        if val != 0:
            print(f"{reg.target_info.path}: AER_CORR=0x{val:X}")
```

### Correlate CCF TOR Timeout with PCIe

```python
import namednodes
from pysvtools import server_ip_debug
import json

print("=== Step 1: Check CCF MCA Status ===")
try:
    ccf_errors = server_ip_debug.ccf.errors.get_mca_status()
    print(json.dumps(ccf_errors, indent=2, default=str))
except Exception as e:
    print(f"CCF check: {e}")

print("\n=== Step 2: Check PCIe AER ===")
for socket in namednodes.sv.sockets:
    for reg in socket.search("aer_uncorr_err_status", getobj=True):
        val = int(reg.read())
        if val:
            print(f"AER error at {reg.target_info.path}: 0x{val:X}")
            
print("\n=== Step 3: Check DPC ===")
for socket in namednodes.sv.sockets:
    for reg in socket.search("dpc_status", getobj=True):
        val = int(reg.read())
        if val:
            print(f"DPC triggered at {reg.target_info.path}: 0x{val:X}")
```
