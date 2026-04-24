# Platform RAS -- SMI Handler, WHEA, Error Injection

Reference for platform-level RAS: BIOS SMI RAS handler, WHEA/ACPI tables, and
error injection for debug validation.

---

## Table of Contents
- [SMI RAS Handler](#smi-ras-handler)
- [WHEA / ACPI GHES](#whea-acpi-ghes)
- [Error Injection (EINJ)](#error-injection)
- [EMCA (Enhanced MCA)](#emca)
- [CE/UE SMI Flow Trace](#ceue-smi-flow-trace)

---

## SMI RAS Handler

### Overview
The SMI RAS handler is the core BIOS component that processes hardware errors at runtime.
It runs in SMM (System Management Mode) -- a privileged execution context isolated from OS.

**Entry points:**
- `MemRasSmiHandler()` -- memory corrected/uncorrected error handler
- `RasSmiHandler()` / `ErrorSmiHandler()` -- platform RAS SMI dispatcher
- Triggered by: CE threshold SMI, CMCI overflow, OS WHEA injection, explicit SMI

### Source Locations
```
ServerRasPkg/Universal/Ras/RasHandler.c     <- main SMI entry dispatcher
ServerRasPkg/Library/MemRasLib/MemRas.c     <- memory-specific RAS actions
ServerRasPkg/Universal/Ras/MemRasSmm.c      <- memory RAS SMM registration
ServerPlatformPkg/Ras/PlatformRas.c         <- platform-level hooks
```

### SMI Handler Decision Tree

```
SMI triggered (CE threshold or manual)
    
     Read MCi_STATUS for all banks
    
     CE detected?
        Update leaky bucket counter
        Threshold exceeded?
           ADDDC capable & x4 device? -> ADDDC sparing
           Rank sparing enabled?      -> Rank sparing
           Mirror mode?               -> Check mirror status
           None of above?             -> Log EWL 0x0A (DIMM disable candidate)
        Threshold not exceeded -> Log CE, continue
    
     UE detected (non-fatal)?
        Log WHEA record
        OS page offline candidate
        Continue (if UCNA)
    
     Fatal UE (PCC=1)?
         Log critical WHEA record
         Attempt platform recovery?
         If recovery fails -> reset/shutdown
```

### Debug: SMI Handler Not Running

**Symptoms**: CE detected but no EWL logged, no ADDDC triggered despite many CEs.

1. Check if `SmiOnCorrectedMemError` is enabled
2. Look for `SMI RAS` in serial log -- if absent, SMI not registered
3. Check BIOS log for `RegisterSmiHandler` or `MemRasSmiHandler install` messages
4. Verify: no SMI lockdown (`SmiLock` bit) before RAS SMI installed

```powershell
# Find SMI handler registration
cd "$env:USERPROFILE\CodeBase\BIOSBuild\Intel"
git grep -rn "MemRasSmiHandler\|RasHandlerEntry\|SmmRegisterHandler" -- "*.c" |
  Select-Object -First 10
```

---

## WHEA / ACPI GHES

### What It Is
WHEA (Windows Hardware Error Architecture) / ACPI GHES (Generic Hardware Error Source)
is the standardized mechanism for BIOS to communicate hardware errors to the OS.

BIOS populates WHEA error records in ACPI HEST (Hardware Error Source Table) via:
- **GHES** (Generic Hardware Error Source) -- primary mechanism on modern platforms
- **BERT** (Boot Error Record Table) -- for errors captured before OS boot

### Error Record Structure
```
ACPI HEST table
 Error Source (type 9 = GHES)
     Error Status Block (CPER format)
         Record Header (severity, source ID)
         Error Section(s)
             Memory Error Section (GUID: a5bc1114-6f64-4ede-b863-3e83ed7c83b1)
                Physical address
                Memory error type (CE=5, UE=6)
                DIMM topology (node/card/module/bank/device)
             Processor Error Section (GUID: dc3ea0b0-a144-4797-b95b-53fa242b6e1d)
                 CPUID
                 MC bank context
```

### BIOS Source for WHEA
```
ServerRasPkg/Universal/Ras/Whea/
ServerRasPkg/Library/WheaLib/
ServerPlatformPkg/Acpi/AcpiTables/Hest/
```

### Debug: WHEA Record Not Appearing in OS

1. Check ACPI HEST table is installed: `acpidump | grep HEST` (Linux) or
   use HwInfo / WinATP tool (Windows)
2. Check GHES address block is non-zero in HEST
3. BIOS log: look for `WHEA` or `GHES` init messages
4. If HEST not present: check `WheaEn` setup variable = 1

---

## Error Injection

### ACPI EINJ (Error Injection)

EINJ allows OS or test tools to inject hardware errors for RAS validation.

**Supported injection types:**
| Type | Value | Description |
|------|-------|-------------|
| Memory CE | 0x04 | Correctable memory ECC error |
| Memory UE | 0x08 | Uncorrectable non-fatal memory error |
| Memory UE Fatal | 0x10 | Fatal memory error (system reset expected) |
| PCIe Error | 0x20 | PCIe AER correctable error |

**BIOS requirements:**
- `EinjEn` setup variable = 1
- ACPI EINJ table installed and points to valid trigger action region
- SMM handler registered for injection trigger

**Usage (Linux)**:
```bash
# List supported injection types
einj -t list

# Inject memory CE at specific address
einj -t 4 -a 0x1000000000

# Inject memory UE
einj -t 8 -a 0x1000000000
```

**Usage (EDAC, Linux)**:
```bash
# Trigger via sysfs
echo "0x0000000100000000" > /sys/kernel/debug/apei/einj/param1  # address
echo "0x00000000ffffffff" > /sys/kernel/debug/apei/einj/param2  # mask
echo "0x0000000000000004" > /sys/kernel/debug/apei/einj/error_inject  # CE type
```

### Debug: EINJ Not Working

1. Check ACPI EINJ table: `acpidump -n EINJ`
2. Check `EinjEn` = 1 in BIOS setup
3. Look for EINJ handler in BIOS log
4. SMM is required for EINJ execution -- check SMM lock hasn't prevented it

---

## EMCA (Enhanced MCA)

### What It Is
EMCA (Enhanced MCA) extends the standard MCi_STATUS register handling with:
- Additional context (DIMM topology, physical address in extended registers)
- Better OS/BIOS coordination
- Support for both CMCI (OS) and BIOS SMI handling in same platform

### Setup Variables
| Variable | Description |
|----------|-------------|
| `EmcaEn` | Enable Enhanced MCA (0=disabled, 1=EMCA gen 1, 2=EMCA gen 2) |
| `EmcaCmsciEn` | Enable CMCI under EMCA (OS sees CEs) |

### EMCA vs Legacy
- **Legacy**: BIOS SMI handles ALL CEs, OS sees nothing until threshold
- **EMCA gen 1**: BIOS handles, OS gets WHEA record
- **EMCA gen 2**: OS can also handle via CMCI; BIOS provides extended records

---

## CE/UE SMI Flow Trace

Complete flow trace for a typical correctable error SMI:

```
DRAM CE detected in MC
    v
MCi_STATUS written: Valid=1, UC=0, ADDRV=1, MISCV=1
    v
MC generates threshold interrupt (if count >= threshold in IA32_MC_CTL2)
    v
BIOS SMI handler triggered (or CMCI if BIOS delegated to OS)
    v
SMI RAS handler reads:
  - MCi_STATUS (bank, MSCOD, MCACOD)  
  - MCi_ADDR (physical address)
  - MCi_MISC (channel/dimm/rank topology)
    v
MemRasLib.DecodeMemError():
  - Maps physical address -> socket/channel/dimm/rank/bank/row/col
  - Determines DRAM device (for ADDDC)
    v
Update leaky bucket for this device
    v
Bucket threshold exceeded?
   Yes -> RAS mitigation (ADDDC / sparing / disable)
   No  -> Log CE in WHEA record, clear MCi_STATUS
    v
Exit SMI, OS continues
    v
OS: WHEA record available via GHES (if EmcaEn or OS-visible)
OS: EDAC driver updates error counters
OS: mcelog / mcepd records CE
OS: Consider page offline (if UE or repeated CE at same PFN)
```

### Finding the Exact BIOS Code Path

```powershell
cd "$env:USERPROFILE\CodeBase\BIOSBuild\Intel"

# Find SMI dispatch
git grep -rn "MemRasSmiHandler\|ProcessCorrectedMemError" -- "*.c" | 
  Select-Object -First 5

# Find DIMM decode function  
git grep -rn "TranslateSystemAddressToDimmInfo\|GetDimmInfoFromAddress" -- "*.c" |
  Select-Object -First 5

# Find leaky bucket logic
git grep -rn "LeakyBucket\|UpdateLeakyBucket\|CeFloodThreshold" -- "*.c" |
  Select-Object -First 5

# Find WHEA record population
git grep -rn "CreateCperRecord\|FillWhea\|WheaLogMemError" -- "*.c" |
  Select-Object -First 5
```
