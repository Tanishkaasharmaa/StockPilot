# Build Capacity Accuracy Report

## Summary of Issue
User reported inconsistent results from the agent:
- **Query 1**: S2 V2 = 120, S3 V1 = 180 (Total: 300)
- **Query 2**: S2 V2 = 120, S3 V1 = 80 (Total: 200)  
- **S1 V1**: "Not enough information"

## Ground Truth (Verified)

**Correct Build Capacities:**
- **S1 V1: 31 units** (bottleneck: Lock Washer P338 with 31 stock)
- **S2 V2: 20 units** (bottleneck: Advanced LED Headlight P332 with 20 stock)
- **S3 V1: 31 units** (bottleneck: Lock Washer P338 with 31 stock)
- **Total: 82 units**

Each model requires **14 parts total**:
- 4 model-specific parts (motor, battery, controller, frame)
- 5 version-specific shared parts (dashboard, wheel, brake, headlight, charger)
- 5 universal shared parts (power cable, seat, fender, hex nut, lock washer)

## Agent Results vs Ground Truth

| Model | Ground Truth | Agent Result (Query 1) | Agent Result (Query 2) | Accuracy |
|-------|--------------|------------------------|------------------------|----------|
| S1 V1 | **31 units** | "Not enough info" | "Not enough info" | ❌ FAILED |
| S2 V2 | **20 units** | 120 units | 120 units | ❌ 500% ERROR |
| S3 V1 | **31 units** | 180 units | 80 units | ❌ INCONSISTENT |

## Root Cause Analysis

The agent's `calculate_build_capacity` tool is **not working correctly**. The verification script proves the database and logic are sound, so the issue is likely:

1. **Tool not being called properly** by the LLM
2. **Tool results being ignored** by the LLM (hallucination)
3. **Tool returning incorrect data** to the LLM

## Next Steps to Fix

1. **Test the tool directly** - Call `calculate_build_capacity("S1 V1")` in Python
2. **Check agent logs** - See what the tool actually returns
3. **Verify LLM is using tool results** - Not hallucinating numbers

## How to Prove Accuracy

✅ **Verification script works correctly**: `python verify_build_capacity.py`
- Shows all 14 parts per model
- Correctly identifies bottlenecks
- Consistent results every time

❌ **Agent gives incorrect results**:
- Need to debug why the agent isn't using the tool correctly
- LLM may be making up numbers instead of using tool output

