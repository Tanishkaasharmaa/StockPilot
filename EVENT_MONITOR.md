# Event Monitor - Complete Documentation

## Overview
The Event Monitor is a comprehensive system that continuously monitors your supply chain, logs all events, and sends notifications for critical issues.

## Features

### 1. Continuous Background Monitoring ✅
- **Auto-starts** when the Streamlit app launches
- **Checks every 5 minutes** for new events
- **Runs in background thread** - doesn't block the UI
- **Automatic logging** of all detected issues

### 2. Event Logging & History ✅
- **Persistent storage** in `event_log.json`
- **Timestamps** for every event
- **Event types**: Low Stock, Delayed Orders, Bottlenecks, Blocked Parts
- **Severity levels**: HIGH, MEDIUM, LOW
- **Acknowledgment tracking** - mark events as reviewed

### 3. Email Notifications ✅
- **Auto-generates** email text for critical events
- **Batches notifications** - one email for multiple critical issues
- **Professional formatting** with subject and body
- **Ready for SMTP integration** (currently prints to console)

### 4. Smart Deduplication ✅
- **Prevents spam** - won't log the same alert twice in 24 hours
- **Tracks recent history** - only new events trigger notifications
- **Efficient storage** - old events can be archived

## Components

### EventMonitor Class
Located in `event_monitor.py`

```python
from event_monitor import EventMonitor

# Initialize
monitor = EventMonitor()

# Check for new events
new_events = monitor.check_for_new_events()

# Get recent events (last 24 hours)
recent = monitor.get_recent_events(hours=24)

# Get unacknowledged events
unack = monitor.get_unacknowledged_events()

# Acknowledge an event
monitor.acknowledge_event(event_index=0)

# Acknowledge all events
monitor.acknowledge_all()

# Start continuous monitoring
monitor.start_monitoring(interval_minutes=5)

# Stop monitoring
monitor.stop_monitoring()

# Get summary statistics
summary = monitor.get_event_summary()
```

## Integration with Streamlit

The app now includes:

1. **Auto-Start Monitoring**:
   ```python
   st.session_state.event_monitor = EventMonitor()
   st.session_state.event_monitor.start_monitoring(interval_minutes=5)
   ```

2. **Event Monitor Widget** (in sidebar):
   - Shows total events in last 24 hours
   - Shows unacknowledged event count
   - "Acknowledge All" button to mark events as reviewed

3. **Real-Time Updates**:
   - Dashboard refreshes automatically
   - New events appear immediately
   - Background monitoring continues even when UI is idle

## Event Log Format

Events are stored in `event_log.json`:

```json
{
  "events": [
    {
      "timestamp": "2025-12-29T19:45:00",
      "type": "CRITICAL_LOW_STOCK",
      "severity": "HIGH",
      "details": "LCD Dashboard Display (P324): Reorder 50 units immediately",
      "action_taken": null,
      "acknowledged": false
    }
  ],
  "last_check": "2025-12-29T19:50:00"
}
```

## Email Notification Format

When critical events occur, the system generates:

**Subject:**
```
🚨 Hugo Alert: 3 Critical Issue(s) Detected
```

**Body:**
```
Hugo Event Monitor Alert
========================

3 critical issue(s) require immediate attention:

1. [HIGH] CRITICAL_LOW_STOCK
   Time: 2025-12-29T19:45:00
   Details: LCD Dashboard Display (P324): Reorder 50 units immediately

2. [HIGH] DELAYED_ORDER
   Time: 2025-12-29T19:46:00
   Details: S1 V1 Motor (P300): Contact supplier SUP-001 for updated ETA

3. [HIGH] BLOCKED_PART
   Time: 2025-12-29T19:47:00
   Details: S2 V2 Motor (P312): Use successor part P304 instead

Please log into the Hugo dashboard for more details and recommended actions.

---
This is an automated alert from Hugo Event Monitor.
```

## Testing

### Standalone Test:
```bash
python event_monitor.py
```

Output:
- Event summary (last 24 hours)
- Recent events list
- Email notification preview (if critical events exist)

### In Streamlit App:
```bash
streamlit run app.py
```

Check sidebar for:
- Event Monitor widget
- Event counts
- Acknowledge button

## Monitoring Workflow

1. **Background Thread** checks for new events every 5 minutes
2. **ReactiveIntelligence** scans database for alerts
3. **EventMonitor** compares with recent history
4. **New events** are logged to `event_log.json`
5. **Critical events** trigger email notification generation
6. **Notification** is printed to console (ready for SMTP)
7. **Dashboard** updates automatically on next refresh

## Event Lifecycle

```
1. Issue Detected → 2. Event Logged → 3. Notification Sent → 4. User Acknowledges
```

- **Detected**: ReactiveIntelligence finds an alert
- **Logged**: EventMonitor saves to event_log.json
- **Notification**: Email text generated for critical events
- **Acknowledged**: User marks as reviewed in dashboard

## Configuration

### Change Monitoring Interval:
```python
# In app.py, line 51
st.session_state.event_monitor.start_monitoring(interval_minutes=10)  # Check every 10 min
```

### Change Event Retention:
```python
# Get events from last 48 hours instead of 24
recent = monitor.get_recent_events(hours=48)
```

### Add SMTP Email Sending:
```python
# In event_monitor.py, add to start_monitoring():
if notification:
    import smtplib
    from email.mime.text import MIMEText
    
    msg = MIMEText(notification['body'])
    msg['Subject'] = notification['subject']
    msg['From'] = 'hugo@voltway.com'
    msg['To'] = 'ops@voltway.com'
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login('your_email', 'your_password')
        server.send_message(msg)
```

## Benefits

1. **24/7 Monitoring**: Never miss a critical issue
2. **Automatic Logging**: Complete audit trail of all events
3. **Proactive Alerts**: Know about problems before they escalate
4. **Reduced Manual Work**: No need to constantly check dashboards
5. **Email Notifications**: Get alerted even when not using the app
6. **Smart Deduplication**: Avoid alert fatigue from repeated notifications

## Files Created

- `event_monitor.py` - Core monitoring logic
- `event_log.json` - Event history (auto-created)
- `app.py` - Updated with event monitor integration
- `EVENT_MONITOR.md` - This documentation

## Next Steps

To fully activate email notifications:
1. Set up SMTP credentials
2. Add email sending code (see Configuration section)
3. Configure recipient list
4. Test with a critical event

The system is now **fully operational** with continuous monitoring, logging, and notification generation!
