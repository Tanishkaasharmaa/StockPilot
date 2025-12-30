# Event Monitor Testing Guide

## Quick Test (5 minutes)

### Step 1: Test Event Monitor Standalone
```bash
python event_monitor.py
```

**What to expect:**
- ✅ Event summary (total, critical, unacknowledged)
- ✅ List of recent events
- ✅ Email notification preview (if critical events exist)
- ✅ Creates `event_log.json` file

### Step 2: Test Streamlit App
```bash
streamlit run app.py
```

**What to check:**
1. **Sidebar - Top Section:**
   - "Total Alerts" metric
   - "Critical" metric
   - Alert breakdown by type

2. **Sidebar - Top Priorities:**
   - White cards with colored left border
   - Part names clearly visible
   - Recommendations shown

3. **Sidebar - Event Monitor:**
   - "Events (24h)" metric
   - "Unacknowledged" metric
   - "Acknowledge All" button

4. **Background Monitoring:**
   - Check terminal/console for monitoring messages
   - Should see: "Event monitoring started (checking every 5 minutes)"

### Step 3: Test Event Logging
```bash
# Check if event log was created
dir event_log.json

# View the log file
type event_log.json
```

**What to expect:**
- JSON file with events array
- Each event has: timestamp, type, severity, details, acknowledged
- last_check timestamp

## Detailed Testing

### Test 1: Verify Background Monitoring

**Run:**
```bash
python -c "from event_monitor import EventMonitor; import time; m = EventMonitor(); m.start_monitoring(interval_minutes=1); print('Monitoring started...'); time.sleep(120); m.stop_monitoring()"
```

**Expected:**
- Monitoring starts
- Checks for events after 1 minute
- Logs any new events
- Stops after 2 minutes

### Test 2: Verify Event Deduplication

**Run:**
```bash
python test_event_deduplication.py
```

(Script will be created below)

**Expected:**
- First run: Logs all events
- Second run (within 24h): No duplicate events logged

### Test 3: Verify Email Notifications

**Run:**
```bash
python test_email_notifications.py
```

(Script will be created below)

**Expected:**
- Email notification generated for critical events
- Subject line with count
- Body with event details

### Test 4: Verify Event Acknowledgment

**In Streamlit app:**
1. Note the "Unacknowledged" count
2. Click "Acknowledge All" button
3. Refresh page
4. Verify "Unacknowledged" count is now 0

### Test 5: Verify Event History

**Run:**
```bash
python test_event_history.py
```

(Script will be created below)

**Expected:**
- Shows events from last 24 hours
- Can filter by severity
- Can filter by type

## Troubleshooting

### Issue: No events showing
**Solution:**
```bash
# Manually trigger event check
python -c "from event_monitor import EventMonitor; m = EventMonitor(); events = m.check_for_new_events(); print(f'Found {len(events)} events')"
```

### Issue: Monitoring not starting
**Solution:**
- Check if `event_log.json` exists and is writable
- Check terminal for error messages
- Verify database path is correct

### Issue: Events not visible in Streamlit
**Solution:**
- Refresh the page (F5)
- Check browser console for errors
- Verify `event_log.json` has recent events

## Expected Output Examples

### event_monitor.py output:
```
============================================================
EVENT MONITOR - INITIALIZATION
============================================================

Checking for new events...
[2025-12-29T19:50:00] HIGH: CRITICAL_LOW_STOCK - LCD Dashboard Display (P324): Reorder 50 units immediately

Found 1 new event(s)

============================================================
EVENT SUMMARY (Last 24 Hours)
============================================================
Total Events: 8
Critical Events: 5
Unacknowledged: 8
Last Check: 2025-12-29T19:50:00

Events by Type:
  - CRITICAL_LOW_STOCK: 4
  - DELAYED_ORDER: 2
  - BUILD_BOTTLENECK: 2

============================================================
RECENT EVENTS
============================================================

1. [⚠] [HIGH] CRITICAL_LOW_STOCK
   Time: 2025-12-29T19:50:00
   Details: LCD Dashboard Display (P324): Reorder 50 units immediately
```

### Streamlit app sidebar:
```
📊 Alert Breakdown
Critical Low Stock: 4
Delayed Order: 2
Build Bottleneck: 2

⚠️ Top Priorities
1. LCD Dashboard Display
   CRITICAL LOW STOCK
   💡 Reorder 50 units immediately

📡 Event Monitor
Events (24h): 8
Unacknowledged: 8
[Acknowledge All] button
```

## Performance Testing

### Test Monitoring Overhead
```bash
python test_monitoring_performance.py
```

**Expected:**
- Monitoring check takes < 1 second
- Memory usage stays stable
- No memory leaks over time

## Integration Testing

### Test Full Workflow
1. Start Streamlit app
2. Wait 5 minutes for first monitoring check
3. Verify new events appear in sidebar
4. Click "Acknowledge All"
5. Verify unacknowledged count goes to 0
6. Check `event_log.json` for acknowledged: true

## Automated Test Suite

Run all tests:
```bash
python run_all_tests.py
```

(Script will be created below)

**Expected:**
- ✅ Event logging works
- ✅ Deduplication works
- ✅ Email generation works
- ✅ Acknowledgment works
- ✅ Background monitoring works
