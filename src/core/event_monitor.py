"""
Event Monitor - Continuous background monitoring with logging and notifications
"""
import sqlite3
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import time
import threading

# Internal Imports (Updated to absolute from src root)
from core.reactive_intelligence import ReactiveIntelligence

class EventMonitor:
    def __init__(self, db_path=None, log_path=None):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        self.db_path = db_path or os.path.join(base_dir, 'data', 'hugo.db')
        self.log_path = log_path or os.path.join(base_dir, 'data', 'event_log.json')
        self.reactive_intel = ReactiveIntelligence(self.db_path)
        self.event_history = self._load_event_history()
        self._ensure_event_ids()
        self.monitoring = False
        self.monitor_thread = None
        
    def _load_event_history(self):
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path, 'r') as f: return json.load(f)
            except: return {'events': [], 'last_check': None}
        return {'events': [], 'last_check': None}
    
    def _save_event_history(self):
        try:
            os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
            with open(self.log_path, 'w') as f: json.dump(self.event_history, f, indent=2)
        except Exception as e: print(f"Error saving: {e}")
    
    def log_event(self, event_type, severity, details, action_taken=None):
        event = {'event_id': f"EVT-{int(time.time() * 1000)}", 'timestamp': datetime.now().isoformat(), 'type': event_type, 'severity': severity, 'details': details, 'action_taken': action_taken, 'acknowledged': False}
        self.event_history['events'].append(event)
        self.event_history['last_check'] = datetime.now().isoformat()
        self._save_event_history()
        return event
    
    def check_for_new_events(self):
        alerts = self.reactive_intel.get_critical_alerts()
        new_events = []
        for alert in alerts:
            if self._is_new_alert(alert):
                event = self.log_event(alert['type'], alert['severity'], f"{alert['part_name']}: {alert['recommendation']}")
                new_events.append(event)
        return new_events
    
    def _is_new_alert(self, alert):
        cutoff = datetime.now() - timedelta(hours=24)
        for event in self.event_history['events']:
            if datetime.fromisoformat(event['timestamp']) > cutoff and event['type'] == alert['type'] and alert['part_id'] in event['details']:
                return False
        return True
    
    def get_unacknowledged_events(self):
        return [e for e in self.event_history['events'] if not e.get('acknowledged', False)]
    
    def acknowledge_event(self, event_id):
        for event in self.event_history['events']:
            if event.get('event_id') == event_id:
                event['acknowledged'] = True
                self._save_event_history()
                return True
        return False
        
    def _ensure_event_ids(self):
        for i, event in enumerate(self.event_history['events']):
            if 'event_id' not in event: event['event_id'] = f"EVT-OLD-{i}"

    def start_monitoring(self, interval_minutes=5):
        if self.monitoring: return
        self.monitoring = True
        def monitor_loop():
            while self.monitoring:
                try:
                    self.check_for_new_events()
                    time.sleep(interval_minutes * 60)
                except Exception as e:
                    print(f"Monitor error: {e}")
                    time.sleep(60)
        self.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        self.monitoring = False

    def get_event_summary(self):
        cutoff = datetime.now() - timedelta(hours=24)
        recent = [e for e in self.event_history['events'] if datetime.fromisoformat(e['timestamp']) > cutoff]
        return {
            'total_events_24h': len(recent),
            'critical_events_24h': sum(1 for e in recent if e['severity'] == 'HIGH'),
            'unacknowledged': len(self.get_unacknowledged_events()),
            'last_check': self.event_history.get('last_check', 'Never')
        }
