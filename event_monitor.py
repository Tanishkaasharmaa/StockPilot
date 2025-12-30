"""
Event Monitor - Continuous background monitoring with logging and notifications
"""
import sqlite3
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from reactive_intelligence import ReactiveIntelligence
import time
import threading

class EventMonitor:
    def __init__(self, db_path='d:/Hugo/hugo.db', log_path='d:/Hugo/event_log.json'):
        self.db_path = db_path
        self.log_path = log_path
        self.reactive_intel = ReactiveIntelligence(db_path)
        self.event_history = self._load_event_history()
        self._ensure_event_ids() # Migration for old logs
        self.monitoring = False
        self.monitor_thread = None
        
    def _load_event_history(self):
        """Load event history from JSON file"""
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, 'r') as f:
                    return json.load(f)
            except:
                return {'events': [], 'last_check': None}
        return {'events': [], 'last_check': None}
    
    def _save_event_history(self):
        """Save event history to JSON file"""
        try:
            with open(self.log_path, 'w') as f:
                json.dump(self.event_history, f, indent=2)
        except Exception as e:
            print(f"Error saving event history: {e}")
    
    def log_event(self, event_type, severity, details, action_taken=None):
        """Log an event to the history"""
        event = {
            'event_id': f"EVT-{int(time.time() * 1000)}",
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'severity': severity,
            'details': details,
            'action_taken': action_taken,
            'acknowledged': False
        }
        
        self.event_history['events'].append(event)
        self.event_history['last_check'] = datetime.now().isoformat()
        self._save_event_history()
        
        # Print to console for visibility
        print(f"[{event['timestamp']}] {severity}: {event_type} - {details}")
        
        return event
    
    def check_for_new_events(self):
        """Check for new events and log them"""
        alerts = self.reactive_intel.get_critical_alerts()
        new_events = []
        
        for alert in alerts:
            # Check if this alert is new (not in recent history)
            is_new = self._is_new_alert(alert)
            
            if is_new:
                event = self.log_event(
                    event_type=alert['type'],
                    severity=alert['severity'],
                    details=f"{alert['part_name']} ({alert['part_id']}): {alert['recommendation']}"
                )
                new_events.append(event)
        
        return new_events
    
    def _is_new_alert(self, alert):
        """Check if an alert is new (not logged in last 24 hours)"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        for event in self.event_history['events']:
            event_time = datetime.fromisoformat(event['timestamp'])
            
            # Check if same type and part within last 24 hours
            if (event_time > cutoff_time and 
                event['type'] == alert['type'] and 
                alert['part_id'] in event['details']):
                return False
        
        return True
    
    def get_recent_events(self, hours=24):
        """Get events from the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent = []
        
        for event in self.event_history['events']:
            event_time = datetime.fromisoformat(event['timestamp'])
            if event_time > cutoff_time:
                recent.append(event)
        
        return sorted(recent, key=lambda x: x['timestamp'], reverse=True)
    
    def get_unacknowledged_events(self):
        """Get events that haven't been acknowledged"""
        return [e for e in self.event_history['events'] if not e.get('acknowledged', False)]
    
    def acknowledge_event(self, event_id):
        """Mark an event as acknowledged by its ID"""
        for event in self.event_history['events']:
            if event.get('event_id') == event_id:
                event['acknowledged'] = True
                self._save_event_history()
                return True
        return False
        
    def _ensure_event_ids(self):
        """Ensure all existing events have an ID (migration)"""
        modified = False
        for i, event in enumerate(self.event_history['events']):
            if 'event_id' not in event:
                event['event_id'] = f"EVT-OLD-{i}"
                modified = True
        if modified:
            self._save_event_history()

    def get_unacknowledged_summary(self):
        """Returns a natural language summary of unacknowledged events for the agent"""
        unack = self.get_unacknowledged_events()
        if not unack:
            return "All operations are currently stable with no unacknowledged alerts."
            
        summary = f"There are {len(unack)} unacknowledged alerts. "
        critical = [e for e in unack if e['severity'] == 'HIGH']
        if critical:
            summary += f"{len(critical)} are CRITICAL. Top issues: "
            top_issues = [e['details'].split(':')[0] for e in critical[:2]]
            summary += ", ".join(top_issues) + "."
        else:
            summary += "Issues involve: "
            top_issues = [e['details'].split(':')[0] for e in unack[:2]]
            summary += ", ".join(top_issues) + "."
            
        return summary
    
    def acknowledge_all(self):
        """Mark all events as acknowledged"""
        for event in self.event_history['events']:
            event['acknowledged'] = True
        self._save_event_history()
    
    def generate_email_notification(self, events):
        """Generate email notification text for critical events"""
        if not events:
            return None
        
        critical_events = [e for e in events if e['severity'] == 'HIGH']
        
        if not critical_events:
            return None
        
        subject = f"🚨 Hugo Alert: {len(critical_events)} Critical Issue(s) Detected"
        
        body = f"""
Hugo Event Monitor Alert
========================

{len(critical_events)} critical issue(s) require immediate attention:

"""
        for i, event in enumerate(critical_events, 1):
            body += f"{i}. [{event['severity']}] {event['type']}\n"
            body += f"   Time: {event['timestamp']}\n"
            body += f"   Details: {event['details']}\n\n"
        
        body += """
Please log into the Hugo dashboard for more details and recommended actions.

---
This is an automated alert from Hugo Event Monitor.
"""
        
        return {'subject': subject, 'body': body}
    
    def start_monitoring(self, interval_minutes=5):
        """Start continuous background monitoring"""
        if self.monitoring:
            print("Monitoring already running")
            return
        
        self.monitoring = True
        
        def monitor_loop():
            print(f"Event monitoring started (checking every {interval_minutes} minutes)")
            
            while self.monitoring:
                try:
                    # Check for new events
                    new_events = self.check_for_new_events()
                    
                    if new_events:
                        print(f"Found {len(new_events)} new event(s)")
                        
                        # Generate email notification if there are critical events
                        notification = self.generate_email_notification(new_events)
                        if notification:
                            print(f"\n📧 EMAIL NOTIFICATION:\n{notification['subject']}\n{notification['body']}")
                    
                    # Wait for next check
                    time.sleep(interval_minutes * 60)
                    
                except Exception as e:
                    print(f"Error in monitoring loop: {e}")
                    time.sleep(60)  # Wait 1 minute before retrying
        
        # Start monitoring in background thread
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        print("Event monitoring stopped")
    
    def get_event_summary(self):
        """Get summary statistics of events"""
        recent_events = self.get_recent_events(hours=24)
        
        summary = {
            'total_events_24h': len(recent_events),
            'critical_events_24h': sum(1 for e in recent_events if e['severity'] == 'HIGH'),
            'unacknowledged': len(self.get_unacknowledged_events()),
            'events_by_type': {},
            'last_check': self.event_history.get('last_check', 'Never')
        }
        
        for event in recent_events:
            event_type = event['type']
            if event_type not in summary['events_by_type']:
                summary['events_by_type'][event_type] = 0
            summary['events_by_type'][event_type] += 1
        
        return summary

if __name__ == "__main__":
    print("=" * 60)
    print("EVENT MONITOR - INITIALIZATION")
    print("=" * 60)
    
    monitor = EventMonitor()
    
    # Check for new events
    print("\nChecking for new events...")
    new_events = monitor.check_for_new_events()
    
    print(f"\nFound {len(new_events)} new event(s)")
    
    # Show event summary
    print("\n" + "=" * 60)
    print("EVENT SUMMARY (Last 24 Hours)")
    print("=" * 60)
    
    summary = monitor.get_event_summary()
    print(f"Total Events: {summary['total_events_24h']}")
    print(f"Critical Events: {summary['critical_events_24h']}")
    print(f"Unacknowledged: {summary['unacknowledged']}")
    print(f"Last Check: {summary['last_check']}")
    
    print("\nEvents by Type:")
    for event_type, count in summary['events_by_type'].items():
        print(f"  - {event_type}: {count}")
    
    # Show recent events
    print("\n" + "=" * 60)
    print("RECENT EVENTS")
    print("=" * 60)
    
    recent = monitor.get_recent_events(hours=24)
    for i, event in enumerate(recent[:5], 1):
        ack_status = "✓" if event.get('acknowledged') else "⚠"
        print(f"\n{i}. [{ack_status}] [{event['severity']}] {event['type']}")
        print(f"   Time: {event['timestamp']}")
        print(f"   Details: {event['details']}")
    
    # Test email notification
    if new_events:
        print("\n" + "=" * 60)
        print("EMAIL NOTIFICATION PREVIEW")
        print("=" * 60)
        
        notification = monitor.generate_email_notification(new_events)
        if notification:
            print(f"\nSubject: {notification['subject']}")
            print(f"\n{notification['body']}")
    
    print("\n" + "=" * 60)
    print("To start continuous monitoring, use:")
    print("  monitor.start_monitoring(interval_minutes=5)")
    print("=" * 60)
