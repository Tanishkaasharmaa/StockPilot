"""
Reactive Intelligence Module for Hugo
Proactively identifies issues and provides recommendations
"""
import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta

class ReactiveIntelligence:
    def __init__(self, db_path=None):
        if db_path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            self.db_path = os.path.join(base_dir, 'data', 'hugo.db')
        else:
            self.db_path = db_path
    
    def get_critical_alerts(self):
        """Get all critical alerts that need immediate attention"""
        alerts = []
        
        # 1. Critical Low Stock
        low_stock = self._check_low_stock()
        if low_stock:
            alerts.extend(low_stock)
        
        # 2. Delayed Orders
        delayed_orders = self._check_delayed_orders()
        if delayed_orders:
            alerts.extend(delayed_orders)
        
        # 3. Build Capacity Bottlenecks
        bottlenecks = self._check_build_bottlenecks()
        if bottlenecks:
            alerts.extend(bottlenecks)
        
        # 4. Blocked Parts
        blocked = self._check_blocked_parts()
        if blocked:
            alerts.extend(blocked)
        
        return alerts
    
    def _check_low_stock(self):
        """Check for parts below minimum stock level"""
        conn = sqlite3.connect(self.db_path)
        query = """
        SELECT 
            s.part_id,
            s.part_name,
            s.quantity_available,
            d.min_stock_level,
            d.reorder_quantity,
            m.used_in_models
        FROM stock_levels s
        JOIN dispatch_parameters d ON s.part_id = d.part_id
        JOIN material_master m ON s.part_id = m.part_id
        WHERE s.quantity_available < d.min_stock_level
        ORDER BY (s.quantity_available - d.min_stock_level) ASC
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        alerts = []
        for _, row in df.iterrows():
            shortage = row['min_stock_level'] - row['quantity_available']
            alerts.append({
                'type': 'CRITICAL_LOW_STOCK',
                'severity': 'HIGH' if shortage > row['min_stock_level'] * 0.5 else 'MEDIUM',
                'part_id': row['part_id'],
                'part_name': row['part_name'],
                'current_stock': row['quantity_available'],
                'min_stock': row['min_stock_level'],
                'shortage': shortage,
                'affected_models': row['used_in_models'],
                'recommendation': f"Reorder {row['reorder_quantity']} units immediately"
            })
        
        return alerts
    
    def _check_delayed_orders(self):
        """Check for orders past their expected delivery date"""
        conn = sqlite3.connect(self.db_path)
        query = """
        SELECT 
            o.order_id,
            o.part_id,
            m.part_name,
            o.quantity_ordered,
            o.expected_delivery_date,
            o.supplier_id,
            o.status
        FROM material_orders o
        JOIN material_master m ON o.part_id = m.part_id
        WHERE o.status != 'delivered' 
        AND o.expected_delivery_date < date('now')
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        alerts = []
        for _, row in df.iterrows():
            alerts.append({
                'type': 'DELAYED_ORDER',
                'severity': 'HIGH',
                'order_id': row['order_id'],
                'part_id': row['part_id'],
                'part_name': row['part_name'],
                'quantity': row['quantity_ordered'],
                'expected_date': row['expected_delivery_date'],
                'supplier': row['supplier_id'],
                'recommendation': f"Contact supplier {row['supplier_id']} for updated ETA"
            })
        
        return alerts
    
    def _check_build_bottlenecks(self):
        """Identify parts that are bottlenecks for multiple models"""
        conn = sqlite3.connect(self.db_path)
        
        # Find parts used in multiple models with low stock
        query = """
        SELECT 
            s.part_id,
            s.part_name,
            s.quantity_available,
            m.used_in_models,
            d.min_stock_level
        FROM stock_levels s
        JOIN material_master m ON s.part_id = m.part_id
        JOIN dispatch_parameters d ON s.part_id = d.part_id
        WHERE m.used_in_models LIKE '%,%'
        AND s.quantity_available < 50
        ORDER BY s.quantity_available ASC
        LIMIT 5
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        alerts = []
        for _, row in df.iterrows():
            model_count = len(row['used_in_models'].split(';'))
            alerts.append({
                'type': 'BUILD_BOTTLENECK',
                'severity': 'MEDIUM',
                'part_id': row['part_id'],
                'part_name': row['part_name'],
                'current_stock': row['quantity_available'],
                'affected_models': row['used_in_models'],
                'model_count': model_count,
                'recommendation': f"This part affects {model_count} models. Consider increasing safety stock."
            })
        
        return alerts
    
    def _check_blocked_parts(self):
        """Check for blocked parts that might affect production"""
        conn = sqlite3.connect(self.db_path)
        query = """
        SELECT 
            part_id,
            part_name,
            blocked_parts,
            successor_parts,
            comment,
            used_in_models
        FROM material_master
        WHERE blocked_parts IS NOT NULL AND blocked_parts != ''
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        alerts = []
        for _, row in df.iterrows():
            alerts.append({
                'type': 'BLOCKED_PART',
                'severity': 'HIGH',
                'part_id': row['part_id'],
                'part_name': row['part_name'],
                'reason': row['comment'],
                'affected_models': row['used_in_models'],
                'successor': row['successor_parts'],
                'recommendation': f"Use successor part {row['successor_parts']} instead" if row['successor_parts'] else "Find alternative supplier"
            })
        
        return alerts
    
    def generate_daily_briefing(self):
        """Generate a daily briefing with key insights"""
        alerts = self.get_critical_alerts()
        
        briefing = {
            'total_alerts': len(alerts),
            'critical_count': sum(1 for a in alerts if a['severity'] == 'HIGH'),
            'alerts_by_type': {},
            'top_priorities': []
        }
        
        # Group by type
        for alert in alerts:
            alert_type = alert['type']
            if alert_type not in briefing['alerts_by_type']:
                briefing['alerts_by_type'][alert_type] = 0
            briefing['alerts_by_type'][alert_type] += 1
        
        # Get top 5 priorities (HIGH severity first)
        sorted_alerts = sorted(alerts, key=lambda x: (x['severity'] != 'HIGH', x['type']))
        briefing['top_priorities'] = sorted_alerts[:5]
        
        return briefing
    
    def get_recommendations(self):
        """Get proactive recommendations"""
        recommendations = []
        
        alerts = self.get_critical_alerts()
        
        # Recommendation 1: Reorder suggestions
        low_stock_alerts = [a for a in alerts if a['type'] == 'CRITICAL_LOW_STOCK']
        if low_stock_alerts:
            parts_to_reorder = [f"{a['part_name']} ({a['part_id']})" for a in low_stock_alerts[:3]]
            recommendations.append({
                'category': 'PROCUREMENT',
                'priority': 'HIGH',
                'action': 'Immediate Reorder Required',
                'details': f"Reorder the following parts: {', '.join(parts_to_reorder)}"
            })
        
        # Recommendation 2: Supplier follow-up
        delayed_alerts = [a for a in alerts if a['type'] == 'DELAYED_ORDER']
        if delayed_alerts:
            suppliers = list(set([a['supplier'] for a in delayed_alerts]))
            recommendations.append({
                'category': 'SUPPLIER_MANAGEMENT',
                'priority': 'HIGH',
                'action': 'Follow up on delayed orders',
                'details': f"Contact suppliers: {', '.join(suppliers)}"
            })
        
        # Recommendation 3: Production planning
        bottleneck_alerts = [a for a in alerts if a['type'] == 'BUILD_BOTTLENECK']
        if bottleneck_alerts:
            recommendations.append({
                'category': 'PRODUCTION',
                'priority': 'MEDIUM',
                'action': 'Adjust production schedule',
                'details': f"{len(bottleneck_alerts)} shared parts are running low, affecting multiple models"
            })
        
        return recommendations

    def get_risk_analysis(self):
        """Analyze supply chain risks and return a risk score for each part"""
        conn = sqlite3.connect(self.db_path)
        
        # Get data for risk calculation
        query = """
        SELECT 
            m.part_id,
            m.part_name,
            s.quantity_available,
            d.min_stock_level,
            sup.reliability_rating,
            sup.lead_time_days,
            m.used_in_models
        FROM material_master m
        JOIN stock_levels s ON m.part_id = s.part_id
        LEFT JOIN dispatch_parameters d ON m.part_id = d.part_id
        LEFT JOIN (
            SELECT part_id, MIN(lead_time_days) as lead_time_days, MAX(reliability_rating) as reliability_rating
            FROM suppliers
            GROUP BY part_id
        ) sup ON m.part_id = sup.part_id
        """
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        risks = []
        for _, row in df.iterrows():
            # 1. Stock Risk (40 points)
            stock_ratio = row['quantity_available'] / max(row['min_stock_level'], 1)
            stock_risk = max(0, min(40, (1 - stock_ratio) * 40))
            if row['quantity_available'] == 0: stock_risk = 40
            
            # 2. Reliability Risk (20 points)
            reliability = row['reliability_rating'] if pd.notnull(row['reliability_rating']) else 3.0
            reliability_risk = max(0, min(20, (5 - reliability) * 4))
            
            # 3. Lead Time Risk (20 points)
            lead_time = row['lead_time_days'] if pd.notnull(row['lead_time_days']) else 14
            lead_time_risk = max(0, min(20, (lead_time / 30) * 20))
            
            # 4. Model Impact (20 points)
            models = row['used_in_models'].split(';') if row['used_in_models'] else []
            model_risk = min(20, len(models) * 7)
            
            total_risk = stock_risk + reliability_risk + lead_time_risk + model_risk
            
            risks.append({
                'part_id': row['part_id'],
                'part_name': row['part_name'],
                'risk_score': round(total_risk, 1),
                'risk_level': 'CRITICAL' if total_risk > 80 else 'HIGH' if total_risk > 60 else 'MEDIUM' if total_risk > 40 else 'LOW',
                'factors': {
                    'stock': round(stock_risk, 1),
                    'reliability': round(reliability_risk, 1),
                    'lead_time': round(lead_time_risk, 1),
                    'impact': round(model_risk, 1)
                }
            })
            
        return sorted(risks, key=lambda x: x['risk_score'], reverse=True)

if __name__ == "__main__":
    ri = ReactiveIntelligence()
    
    print("=" * 60)
    print("REACTIVE INTELLIGENCE - DAILY BRIEFING")
    print("=" * 60)
    
    briefing = ri.generate_daily_briefing()
    
    print(f"\nTotal Alerts: {briefing['total_alerts']}")
    print(f"Critical Alerts: {briefing['critical_count']}")
    
    print("\nAlerts by Type:")
    for alert_type, count in briefing['alerts_by_type'].items():
        print(f"  - {alert_type}: {count}")
    
    print("\nTop 5 Priorities:")
    for i, alert in enumerate(briefing['top_priorities'], 1):
        print(f"\n{i}. [{alert['severity']}] {alert['type']}")
        print(f"   Part: {alert['part_name']} ({alert['part_id']})")
        print(f"   Recommendation: {alert['recommendation']}")
    
    print("\n" + "=" * 60)
    print("PROACTIVE RECOMMENDATIONS")
    print("=" * 60)
    
    recommendations = ri.get_recommendations()
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. [{rec['priority']}] {rec['category']}")
        print(f"   Action: {rec['action']}")
        print(f"   Details: {rec['details']}")
