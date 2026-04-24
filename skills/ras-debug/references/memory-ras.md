# Memory RAS Features -- DMR / Oak Stream

Deep-dive reference for memory RAS features. Each section covers: what it is,
how BIOS programs it, key registers, EWL codes, and PythonSV scripts.

---

## Table of Contents

- [Patrol Scrub](#patrol-scrub)
- [ADDDC (Adaptive Double Device Data Correction)](#adddc)
- [SDDC / SDDC+1](#sddc)
- [Rank Sparing](#rank-sparing)
- [Memory Mirroring](#memory-mirroring)
- [DDR5 ECS (Error Check Scrub)](#ddr5-ecs)
- [On-Demand Scrub](#on-demand-scrub)
- [Leaky Bucket / CE Threshold](#leaky-bucket)
- [Post Package Repair (PPR)](#ppr)
- [NVDIMM / ADR](#nvdimm-adr)

---

## Patrol Scrub

### What It Is
Background patrol scrub continuously reads all of DRAM to detect correctable errors
(CEs) before they accumulate into uncorrectable errors (UEs). The MC scrub engine walks
through all memory at a configurable rate, triggering CE correction in place.

### BIOS Programming Flow
1. **PEI/MRC phase**: MRC calculates scrub interval based on DRAM size and clock
2. **Post-MRC (DXE)**: `InitPatrolScrub()` programs MC registers
3. **SMI handler**: On CE detection, SMI can pause/resume scrub

Key setup variables:
```
PatrolScrub           = 1 (enabled) / 0 (disabled)
PatrolScrubInterval   = 0 (24h default) / 1-100 (custom hours)
PatrolScrubDuration   = time to complete one full pass (calculated from DRAM size)
```

### Key Registers (DMR)

| Register | Location | Description |
|----------|----------|-------------|
| `patrol_scrub_status` | `imhN.memss.mcX.mcmain` | Bit 0: scrub enable, Bit 1: scrub active |
| `patrol_scrub_address` | `imhN.memss.mcX.mcmain` | Current scrub address (increments during scrub) |
| `patrol_scrub_interval` | `imhN.memss.mcX.mcmain` | Configured scrub rate |
| `scrub_rank_mask` | `imhN.memss.mcX.mcmain` | Which ranks are being scrubbed |

### PythonSV -- Verify Patrol Scrub is Running

```python
import namednodes, time

results = []
for socket in namednodes.sv.sockets:
    for imh in socket.imhs:
        for mc in imh.memss.mcs:
            status = mc.mcmain.patrol_scrub_status
            addr_reg = mc.mcmain.patrol_scrub_address
            
            enabled = int(status.enable.read())
            active = int(status.active.read()) if hasattr(status, 'active') else -1
            addr1 = int(addr_reg.read())
            time.sleep(2)
            addr2 = int(addr_reg.read())
            
            results.append({
                "path": mc.target_info.path,
                "enabled": enabled,
                "active": active,
                "addr_advancing": addr1 != addr2,
                "addr": f"0x{addr1:X} -> 0x{addr2:X}"
            })

for r in results:
    print(f"{r['path']}: enabled={r['enabled']} active={r['active']} "
          f"advancing={r['addr_advancing']} ({r['addr']})")
```

### EWL Codes
| Major | Minor | Meaning |
|-------|-------|---------|
| 0x07 | Various | Patrol scrub failure during scrub pass |
| 0x1C | 0x01 | Patrol scrub disabled -- bandwidth constraint |
| 0x1C | 0x02 | Patrol scrub disabled -- BIOS policy |
| 0x1C | 0x03 | Patrol scrub disabled -- memory error during scrub |
| 0x20 | Various | Mirror scrub failure (patrol scrub on mirrored memory) |

### Debug Checklist
- [ ] `PatrolScrub` setup variable = 1?
- [ ] No EWL 0x1C in BIOS log?
- [ ] `patrol_scrub_status.enable` = 1 in PythonSV?
- [ ] `patrol_scrub_address` advancing over time?
- [ ] No `scrub_pause` bit set?
- [ ] Memory bandwidth not saturated (check DRAM utilization)?

---

## ADDDC

### What It Is
ADDDC (Adaptive Double Device Data Correction) is an advanced ECC mode for x4 DRAM
devices. When a correctable error (CE) is detected on a specific DRAM device, ADDDC
"spares" that device by redistributing its data across remaining devices with extended
ECC coverage. The system continues running without downtime.

**Key requirement**: x4 DQ width DRAMs only. DDR5 x8 devices do NOT support ADDDC.

### BIOS Programming Flow
1. **MRC phase**: Detects if DIMMs support ADDDC (x4 DRAM width check)
2. **Policy**: `AdddcSupport` = 1 enables ADDDC
3. **ADDDC Trigger**: CE detected -> SMI fires -> RAS handler evaluates threshold ->
   if threshold met, `AdddcSparingHandler()` called -> hardware performs sparing

### Key Registers (DMR)

| Register | Location | Description |
|----------|----------|-------------|
| `adddc_status` | `imhN.memss.mcX` | Bit 0: ADDDC enabled, Bit 4: sparing complete |
| `adddc_sparing_status` | `imhN.memss.mcX` | Valid/bank/rank/device of spared region |
| `adddc_err_count` | `imhN.memss.mcX.subchY` | CE counter per sub-channel |

### ADDDC Trigger Condition
Default: 4 CEs on the same DRAM device within a 24h window (leaky bucket).
When triggered:
1. Hardware remaps the failing device's ECC coverage
2. BIOS logs EWL 0x08 with the device location
3. ADDDC sparing complete -- system continues
4. If a SECOND device fails on same rank -> UE (ADDDC can only cover 1 device per rank)

### PythonSV -- Check ADDDC State

```python
import namednodes

for socket in namednodes.sv.sockets:
    for imh in socket.imhs:
        for mc in imh.memss.mcs:
            try:
                status = mc.adddc_status.read()
                sparing = mc.adddc_sparing_status.read()
                print(f"{mc.target_info.path}:")
                print(f"  adddc_status=0x{int(status):X}")
                print(f"  adddc_sparing_status=0x{int(sparing):X}")
                mc.adddc_sparing_status.show()
            except AttributeError:
                pass
```

### EWL Codes
| Major | Minor | Meaning |
|-------|-------|---------|
| 0x08 | 0x01 | ADDDC sparing completed successfully |
| 0x08 | 0x02 | ADDDC sparing failed -- device already used |
| 0x08 | 0x03 | ADDDC sparing failed -- no spare available |
| 0x08 | 0x04 | ADDDC reverse operation (undo sparing) |

### Common Issues
- **ADDDC not triggering**: x8 DRAM width? Check DIMM SPD byte 13 for device width.
- **ADDDC threshold not meeting**: Check leaky bucket count vs threshold setting.
- **ADDDC completed but errors continue**: Second device failed on same rank -> escalates to UE.

---

## SDDC

### What It Is
SDDC (Single Device Data Correction) is standard DDR5 x4 ECC -- the memory controller
corrects a full x4 DRAM device failure using extra ECC bits. This is the baseline ECC
mode; ADDDC builds on top of SDDC.

SDDC+1: After one DRAM device fails (SDDC correcting it), SDDC+1 mode kicks in to
provide an additional level of protection for a subsequent single-bit error.

### EWL Code
| Major | Minor | Meaning |
|-------|-------|---------|
| 0x27 | 0x01 | SDDC+1 mode engaged (one device already failed) |
| 0x27 | 0x02 | SDDC+1 mode -- degraded protection warning |

---

## Rank Sparing

### What It Is
When CE threshold is exceeded on a physical rank, BIOS can copy all data from the
failing rank to a pre-configured spare rank, then redirect memory accesses to the spare.
The DIMM must be populated with a spare rank (typically 1 spare rank per DIMM).

### BIOS Programming Flow
1. **BIOS setup**: `RankSparing` = 1 (usually disabled by default)
2. **MRC phase**: Programs spare rank and marks it unavailable for data
3. **SMI handler**: CE threshold exceeded -> `RankSparingHandler()` -> data copy -> swap

### EWL Codes
| Major | Minor | Meaning |
|-------|-------|---------|
| 0x03 | 0x01 | Rank sparing completed successfully |
| 0x03 | 0x02 | Rank sparing failed -- copy error |
| 0x03 | 0x03 | Rank sparing failed -- no spare available |
| 0x16 | 0x01 | Spare rank not populated |

### Debug Checklist
- [ ] `RankSparing` = 1 in BIOS setup?
- [ ] DIMM has spare rank? Check memory topology report in BIOS log.
- [ ] CE threshold configured correctly?
- [ ] Check EWL 0x03 in log after error injection.

---

## Memory Mirroring

### What It Is
Memory mirroring duplicates writes to two memory channels. On a UE, the MC automatically
switches to the mirror copy. Unlike sparing (which requires a copy operation), mirroring
provides instant failover.

Modes (DMR):
- **Full mirroring**: All memory mirrored (50% capacity)
- **Partial mirroring**: First N GB mirrored, rest independent
- **Address-range mirroring**: Specific NUMA regions mirrored

### BIOS Programming Flow
1. Setup: `MemoryMode` = 1/2/3 for mirror variants
2. MRC programs channel pair as primary/secondary
3. DXE: ACPI SRAT table updated to reflect reduced capacity

### Key Registers
| Register | Description |
|----------|-------------|
| `mirror_status` | Primary/secondary sync status, failover bit |
| `mirror_err_status` | CE/UE on primary, failover triggered |

### EWL Codes
| Major | Minor | Meaning |
|-------|-------|---------|
| 0x20 | 0x01 | Mirror scrub error -- primary CE detected |
| 0x20 | 0x02 | Mirror failover -- UE on primary, switching to secondary |
| 0x20 | 0x03 | Mirror secondary also has error (degraded) |

---

## DDR5 ECS

### What It Is
DDR5 ECS (Error Check Scrub) is a DRAM-internal feature (JESD79-5B S.4.x). The DRAM
device itself periodically scrubs its cells and reports accumulated errors via a counter
in Mode Register (MR) space. Unlike patrol scrub (which is MC-initiated), ECS runs
inside the DRAM chip.

**ECS is DDR5 only** -- DDR4 does not have ECS.

### BIOS Programming Flow
1. **MRC phase**: Reads DRAM JEDEC support bits -> enables ECS via MR write
2. **ECS modes**:
   - `Mode 0`: Count-Stop-on-Zero (stops when counter reaches 0)
   - `Mode 1`: Count-Down (wraps, reports periodically)
3. **BIOS reads ECS counters** periodically and adjusts CE thresholds

Setup variable: `Ddr5EcsMode` = 0 (disabled) / 1 (Mode 0) / 2 (Mode 1)

### ECS Debug
- Check BIOS log for `ECS Mode` messages during DDR5 init
- Check DRAM MR48 (ECS configuration) via MR read command
- ECS errors surface as normal CEs in MCi_STATUS -- no separate ECS EWL code

---

## On-Demand Scrub

### What It Is
When a CE is detected, BIOS can trigger an on-demand scrub of the surrounding memory
region to check for additional CEs before declaring corrected. This is faster than
waiting for patrol scrub to reach the region.

### BIOS Flow
1. CE detected via SMI
2. `OnDemandScrubHandler()` computes address range (typically 64MB around CE)
3. Programs MC to scrub range immediately
4. Collects results, adjusts CE count

Setup: `OnDemandScrubControl` = 1 (enabled, default)

### Debug
- Look for `On-demand scrub` message in BIOS serial log after CE
- If on-demand scrub seems to generate MORE errors: bandwidth pressure or
  scrub triggering on a bad DIMM -- check the specific DIMM topology

---

## Leaky Bucket

### What It Is
The leaky bucket algorithm prevents a noisy but recoverable DIMM from triggering
unnecessary RAS actions. CEs increment a counter, which decays over time. Only if CEs
arrive faster than the decay rate (threshold exceeded) does BIOS take action.

### Algorithm (simplified)
```
bucket_count += 1 per CE
bucket_count -= 1 per decay_interval (e.g., every 5 minutes)
if bucket_count >= threshold:
    -> trigger ADDDC / rank sparing / DIMM disable action
```

### BIOS Variables
| Variable | Description |
|----------|-------------|
| `CeFloodThreshold` | Max bucket count before action (default: 4-8, platform-specific) |
| `DecayInterval` | Time between bucket decrements |
| `CorrectedErrorThreshold` | Alternative per-DIMM threshold |

### EWL Codes
| Major | Minor | Meaning |
|-------|-------|---------|
| 0x0A | various | DIMM disable -- CE threshold exceeded |
| 0x0A | 0x05 | POP (Populated Odd Placement) violation -- also triggers disable |

### Debug
- Check `leaky_bucket_count_*` PythonSV registers
- If threshold firing too quickly: check `CeFloodThreshold` value
- If threshold never fires despite many CEs: bucket may be decaying too fast,
  or CEs are on different devices/ranks (each has its own bucket)

---

## PPR

### What It Is
PPR (Post Package Repair) is a DRAM-level repair feature (JEDEC). When a specific
row fails repeatedly, BIOS can issue a PPR command to the DRAM to map out the bad row
permanently using on-die redundant rows. Works while system is offline (during next boot).

Types:
- **sPPR (Soft PPR)**: Temporary, volatile repair -- lost on power cycle
- **hPPR (Hard PPR)**: Permanent DRAM repair stored in DRAM fuse

### BIOS Flow
1. CE/UE on specific row -> SMI handler records row address
2. Next cold boot: MRC executes PPR sequence for flagged rows
3. BIOS logs EWL 0x15 with result

### EWL Codes
| Major | Minor | Meaning |
|-------|-------|---------|
| 0x15 | 0x01 | sPPR completed successfully |
| 0x15 | 0x02 | hPPR completed successfully |
| 0x15 | 0x03 | PPR failed -- DRAM doesn't support or max repairs exceeded |
| 0x15 | 0x04 | PPR skipped -- same row already repaired |

---

## NVDIMM / ADR

### What It Is
NVDIMM (Non-Volatile DIMM) and ADR (Asynchronous DRAM Refresh) work together to
preserve memory contents on sudden power loss. ADR puts the memory controller into
self-refresh mode and powers the DIMMs from an energy storage reserve.

### BIOS Flow
1. ADR trigger: Power loss -> GPIO -> PCH ADR mechanism
2. BIOS ADR handler: Programs MC for self-refresh, disables writes
3. On recovery: BIOS reads NVDIMM status, restores or reports data loss

### EWL / Debug
- Look for `ADR` messages in BIOS log
- Check NVDIMM Health Status via BIOS log or `nvdimm_health_status` register
- ADR failures appear as UE on NVDIMM region after power restoration
