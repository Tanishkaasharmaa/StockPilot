# Accuracy Verification Summary

## Ground Truth (Verified ✅)
```
S1 V1: 31 units (bottleneck: Lock Washer)
S2 V2: 20 units (bottleneck: Advanced LED Headlight)  
S3 V1: 31 units (bottleneck: Lock Washer)
Total: 82 units
```

## Agent Performance (❌ FAILING)
- **S1 V1**: Returns "not enough information" instead of 31
- **S2 V2**: Returns 120 instead of 20 (500% error!)
- **S3 V1**: Returns 180 or 80 (inconsistent!) instead of 31

## Root Cause
The `calculate_build_capacity` tool in `agent.py` is likely working correctly (verification script uses the same logic), but the **LLM is not using the tool results properly**.

## Recommended Fixes

### Option 1: Test Tool Output
Run `python test_tool_directly.py` to see what the tool actually returns. If the tool returns correct values, the LLM is hallucinating.

### Option 2: Add Logging
Add print statements in `agent.py` to see:
- What the tool returns
- What the LLM sees
- What the LLM outputs

### Option 3: Simplify System Prompt
The current prompt might be too complex. Try a simpler version that emphasizes using tool results verbatim.

### Option 4: Try Different LLM
Test with a different Ollama model (e.g., `llama3.1` or `mistral`) to see if it's model-specific.

## How to Prove Accuracy Going Forward

1. **Always run verification script first**: `python verify_build_capacity.py`
2. **Compare agent output**: Should match exactly
3. **Test multiple times**: Results must be consistent
4. **Document discrepancies**: Track when/why the agent fails

## Files Created for Testing
- `verify_build_capacity.py` - Manual calculation (WORKS ✅)
- `test_tool_directly.py` - Test tool without LLM
- `ACCURACY_REPORT.md` - Detailed analysis
- `inspect_db.py` - Database inspection
