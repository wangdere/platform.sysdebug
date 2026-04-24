---
name: ras-debug
description: >
  Debug Intel DMR/Oak Stream platform RAS (Reliability, Availability, Serviceability)
  features end-to-end. Use when the user describes any memory or system error handling
  behavior -- patrol scrub not running, ADDDC/SDDC not engaging, rank sparing not
  triggering, memory mirroring issues, CE/UE threshold behavior, DDR5 ECS not enabled,
  leaky bucket counting, on-demand scrub, WHEA/CMCI events -- or asks "why is BIOS doing
  X with errors", "RAS not kicking in", "too many correctable errors", "scrub interval
  wrong", "is ADDDC supported here". Also use when MCA or EWL errors are already decoded
  and you need to understand what RAS action BIOS should take. Covers DMR and Oak Stream.
  Proactively invoke even if the user just says "memory errors" or "CE flooding" without
  explicitly saying "RAS".
---

# RAS Debug -- Intel DMR / Oak Stream

End-to-end debug guide for Intel platform RAS features. Covers the full stack from
hardware error detection through BIOS handling to OS/WHEA notification.

## How to Use This Skill

1. **Identify the RAS feature** involved using the classification table below
2. **Load the relevant reference** from `references/` for deep feature knowledge
3. **Follow the feature-specific debug workflow**
4. **Invoke supporting skills** for decode and source tracing

---

## Step 1 -- Classify the Problem

Match the symptom to a RAS feature/domain:

| Symptom | RAS Feature | Reference |
|---------|-------------|-----------|
| "Patrol scrub not running", scrub interval not visible in PythonSV | Patrol Scrub | memory-ras.md S.Patrol-Scrub |
| "ADDDC not engaging", sparing did not kick in after CE threshold | ADDDC / Rank Sparing | memory-ras.md S.ADDDC |
| "SDDC not working", x4 ECC error not corrected | SDDC | memory-ras.md S.SDDC |
| "Memory mirroring failed", failover did not happen | Memory Mirroring | memory-ras.md S.Mirroring |
| "DDR5 ECS not enabled", ECS scrub counter stuck | DDR5 ECS | memory-ras.md S.ECS |
| "On-demand scrub triggered unexpectedly" | On-Demand Scrub | memory-ras.md S.ODS |
| "CE threshold exceeded", leaky bucket fired | CE Threshold / Leaky Bucket | memory-ras.md S.Leaky-Bucket |
| "Rank sparing completed but OS saw UE", spare rank failed | Rank Sparing | memory-ras.md S.Sparing |
| MCi_STATUS = MCCHAN bank, CE/UE memory error | Memory MCA | cpu-ras.md S.MCA-Memory |
| MCi_STATUS = CCF/MLC/IFU, core/uncore error | CPU/Uncore MCA | cpu-ras.md S.MCA-CPU |
| "IERR asserted", "MCERR", system hangs | IERR/MCERR Flow | cpu-ras.md S.IERR |
| PCIe AER errors, DPC triggered | PCIe AER/DPC | pcie-cxl-ras.md S.AER |
| CXL error, CXL.mem corrected/uncorrected | CXL RAS | pcie-cxl-ras.md S.CXL |
| WHEA record logged but no action taken | WHEA/SMI Handler | platform-ras.md S.WHEA |
| SMI triggered but RAS action did not complete | SMI RAS Handler | platform-ras.md S.SMI |
| "PPR failed", post-package repair not writing | PPR | memory-ras.md S.PPR |
| NVDIMM error, ADR flow | NVDIMM/ADR | memory-ras.md S.NVDIMM |

If the symptom matches multiple features, list all and investigate the most likely first.

---

## Step 2 -- Verify Feature Configuration

Before investigating hardware behavior, confirm the feature is **enabled and configured
correctly in BIOS setup**. Most RAS bugs are misconfigurations.

### BIOS Setup Variable Check

```powershell
cd "$env:USERPROFILE\CodeBase\BIOSBuild\Intel"
git grep -rn "PatrolScrubDis\|PatrolScrub " -- "*.c" "*.h" | Select-Object -First 10
git grep -rn "AdddcSupport\|AddDcPolicy" -- "*.c" "*.h" | Select-Object -First 10
```

Key setup variables to check:

| Feature | Setup Variable | Default |
|---------|---------------|---------|
| Patrol Scrub | `PatrolScrub` | Enabled (1) |
| Patrol Scrub Interval | `PatrolScrubInterval` | 24h |
| ADDDC Sparing | `AdddcSupport` | Enabled |
| Rank Sparing | `RankSparing` | Disabled by default |
| Memory Mirroring | `MemoryMode` | 0 = Independent |
| DDR5 ECS | `Ddr5EcsMode` | Enabled |
| On-Demand Scrub | `OnDemandScrubControl` | Enabled |
| CE Threshold | `CeFloodThreshold` | platform-specific |
| SMI on corrected error | `SmiOnCorrectedMemError` | Enabled |

### PythonSV -- Check Live RAS Config

```python
import namednodes

# Check patrol scrub status (MC register)
for socket in namednodes.sv.sockets:
    for imh in socket.imhs:
        for mc in imh.memss.mcs:
            scrub = mc.mcmain.patrol_scrub_status.read()
            print(f"{mc.target_info.path}: patrol_scrub_status=0x{int(scrub):X}")
```

---

## Step 3 -- Decode Any Error Codes Present

### EWL / RC Fatal codes in BIOS log

Invoke `bios-log-analyzer` skill for full decode:

```bash
python3 ~/.agents/skills/bios-log-analyzer/scripts/decode_ewl.py --log <path/to/serial.log>
```

### MCA errors in PythonSV / dmesg

Invoke `mca-log-analyzer` skill:

```bash
python3 ~/.agents/skills/mca-log-analyzer/scripts/main.py analyze-log <path/to/log>
```

### EWL -> RAS Feature Mapping

Key EWL major codes that map to specific RAS features:

| EWL Major | Name | RAS Feature |
|-----------|------|-------------|
| 0x03 | WARN_MEMORY_SPARING | Rank / Bank Sparing |
| 0x07 | WARN_PATROL_SCRUB_FAILURE | Patrol Scrub |
| 0x08 | WARN_ADDDC_SPARING | ADDDC |
| 0x0A | WARN_USER_DIMM_DISABLE | CE threshold -> DIMM disable |
| 0x15 | WARN_MEMORY_PPR | Post Package Repair |
| 0x16 | WARN_SPARE_RANK_NOT_POPULATED | Rank Sparing config |
| 0x1C | WARN_PATROL_SCRUB_DISABLE | Patrol scrub disabled reason |
| 0x20 | WARN_MIRROR_SCRUB_FAILURE | Mirroring + Patrol Scrub |
| 0x27 | WARN_SDDC_PLUS_ONE | SDDC +1 engaged |

---

## Step 4 -- Feature-Specific Debug Workflow

### Patrol Scrub

**Goal:** Confirm scrub is running, verify interval, check if errors were detected.

1. Check BIOS log for `PatrolScrub:` or `Patrol Scrub` init messages
2. Check EWL 0x07 / 0x1C -- indicates why scrub was disabled
3. In PythonSV, read `patrol_scrub_address` register -- should be incrementing:

```python
import namednodes, time
path = namednodes.sv.socket0.imh0.memss.mc0
a1 = int(path.mcmain.patrol_scrub_address.read())
time.sleep(5)
a2 = int(path.mcmain.patrol_scrub_address.read())
print(f"Scrub advancing: {a1 != a2} ({hex(a1)} -> {hex(a2)})")
```

4. If scrub is not advancing: check `scrub_pause` bit, memory bandwidth pressure
5. Check `scrub_interval` register matches BIOS setup value

Read `references/memory-ras.md` S.Patrol-Scrub for full register map and decode.

### ADDDC Sparing

**Goal:** Determine why ADDDC did not engage on a hard CE.

1. Find the triggering CE: MCA bank 19-26 (MCCHAN), MCACOD typically 0x0080
2. Check EWL 0x08 in BIOS log -- logged when ADDDC completes or fails
3. Verify `AdddcSupport` policy enabled AND DIMM is x4 (ADDDC requires x4 DQ DRAMs)
4. Check `adddc_sparing_status` register post-ADDDC:

```python
import namednodes
s = namednodes.sv.socket0.imh0.memss.mc0.adddc_sparing_status.read()
s.show()   # fields: valid, bank_failed, rank_failed, device_failed
```

5. If ADDDC valid=0: either not triggered (threshold not met) or failed (check EWL 0x08 minor)

Read `references/memory-ras.md` S.ADDDC for threshold config and failure codes.

### CE Threshold / Leaky Bucket

**Goal:** Understand why (or why not) a correctable error threshold fired.

1. BIOS uses "leaky bucket" algorithm: CEs increment a counter; counter decays over time
2. Threshold values: BIOS setup `CeFloodThreshold` (default: 4 CEs in time window)
3. Check `leaky_bucket_*` registers via PythonSV
4. When threshold fires: BIOS logs EWL 0x0A, considers rank/DIMM disable
5. Look for `WARN_USER_DIMM_DISABLE` (0x0A) / `WARN_DIMM_DISABLE_*` minor codes

### Memory Mirroring

**Goal:** Verify primary/secondary channel sync and failover behavior.

1. Check `MemoryMode` setup: 1=Mirror Full, 2=Mirror Partial, 3=Mirror Address Range
2. Look for EWL 0x20 (mirror scrub failure) -- indicates mirror copy diverged
3. PythonSV: check `mirror_status` register on both channels for sync status
4. Failover test: inject error via EINJ (ACPI error injection) and verify OS only sees one UE

### DDR5 ECS

**Goal:** Confirm DDR5 DRAM-internal ECS is enabled and reporting.

1. ECS is DRAM-side feature (not BIOS-controlled scrub) -- enabled via MR (Mode Register)
2. Check BIOS log for `ECS Mode:` messages during DDR5 training
3. Check `ddr5_ecs_*` registers -- BIOS reads ECS counters periodically
4. ECS errors report as CE in normal MCA flow -- not a separate EWL code

---

## Step 5 -- Cross-Layer Correlation

When you have errors at multiple levels, correlate them:

```
DDR5 ECS CE
  -> DRAM reports internal CE to DIMM SPD status
  -> MC detects CE -> MCi_STATUS (MCCHAN bank 19-26)
  -> MCA handler: correctable? -> log CMCI / SMI
  -> BIOS SMI RAS handler: check threshold -> ADDDC? Rank sparing? Log EWL
  -> OS WHEA record logged (ACPI GHES or CMCI)
  -> If threshold exceeded -> OS page offlining (MCE daemon / mcelog)
```

Key correlation points:
1. **Same device but different error banks**: MCi_STATUS MSCOD device index should
   match EWL topology (Socket/Channel/DIMM/Rank/Device)
2. **EWL fires but OS does not see UE**: correct -- ADDDC/sparing corrected before OS
3. **OS sees UE but no EWL**: check if BIOS SMI handler ran (look for `SMI RAS` in log)

---

## Step 6 -- Source Trace

Once the problem is identified (wrong threshold, feature not engaging, wrong MC register),
invoke `bios-source-analysis` with the specific error string or function name.

Key BIOS source locations for RAS:

```
ServerRasPkg/Library/MemRasLib/         <- Memory RAS policy + action handlers
ServerRasPkg/Universal/Ras/             <- SMI RAS handler
ServerSiliconPkg/Mem/MemRas/            <- MC register programming
ServerSiliconPkg/Mem/MemDecodeGenDdr.c  <- Memory decode (common RC fatal source)
ServerPlatformPkg/Ras/                  <- Platform-level RAS integration
```

```powershell
cd "$env:USERPROFILE\CodeBase\BIOSBuild\Intel"
# Find patrol scrub init
git grep -rn "PatrolScrubInit\|InitPatrolScrub" -- "*.c" | Select-Object -First 10
# Find ADDDC handler
git grep -rn "AdddcSparing\|HandleAdddc" -- "*.c" | Select-Object -First 10
# Find SMI RAS entry
git grep -rn "MemRasSmiHandler\|RasSmiHandler" -- "*.c" | Select-Object -First 10
```

---

## Step 7 -- Look Up HAS/PAS Spec

For register field definitions and expected behavior, invoke `intel-specs`.

Key HAS sections:
- DMR RAS HAS S.6.x -- Memory RAS features
- DMR RAS HAS S.7.x -- CPU/MCA architecture
- DMR RAS HAS S.8.x -- Platform RAS (SMI, WHEA)
- Oak Stream RAS PAS -- Platform-specific additions

---

## Output Format

After completing the debug:

```
### RAS Debug Summary
Feature: <patrol scrub / ADDDC / etc.>
Platform: DMR / Oak Stream
Issue: <one-line description>

### Findings
| # | Layer | Evidence | Confidence |
|---|-------|----------|------------|
| 1 | BIOS config | PatrolScrubDis=1 in setup | Confirmed |
| 2 | HW register | patrol_scrub_address not advancing | Confirmed |

### Root Cause
<1-2 sentences>

### Next Steps
1. <fix or investigation step>
2. <fix or investigation step>

### Skills Invoked
- bios-log-analyzer: <findings>
- mca-log-analyzer: <findings>
- bios-source-analysis: <findings>
```

---

## Reference Files

| File | Contents | When to Read |
|------|----------|--------------|
| `references/memory-ras.md` | Patrol scrub, ADDDC, SDDC, sparing, mirroring, ECS, PPR, leaky bucket -- register maps, EWL codes, PythonSV scripts | Any memory RAS feature debug |
| `references/cpu-ras.md` | MCA hierarchy, IERR/MCERR flow, corrected error signaling (CMCI/CSMI), UC vs CE handling | CPU/uncore errors, MCA decode follow-up |
| `references/pcie-cxl-ras.md` | PCIe AER, DPC, CXL error handling, CXL.mem CE/UE flow | PCIe or CXL errors |
| `references/platform-ras.md` | SMI RAS handler, WHEA ACPI tables, error injection (EINJ), ACPI GHES | SMI/WHEA/OS-level questions |

---

## Quick Skill Routing

| Need | Invoke |
|------|--------|
| Decode EWL/RC Fatal/IPSD from serial log | `bios-log-analyzer` |
| Decode MCi_STATUS / PythonSV MCA output | `mca-log-analyzer` |
| Trace error to BIOS source file | `bios-source-analysis` |
| Write PythonSV debug script | `pythonsv-scripting` |
| Look up RAS HAS register spec | `intel-specs` |
| Full HSDES ticket investigation | `hsdes-full-investigation` |
| Write a BIOS fix patch | `bios-patch-author` |
