"""
Advanced log monitoring and alerting system
Provides real-time log analysis, alerting, and dashboard capabilities
"""

import json
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum

from ..config.settings import settings
from ..database.connection import db_manager
from ..utils.enhanced_logging import log_analyzer, enhanced_monitoring_logger


class AlertLevel(Enum):
    """Alert severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class LogAlert:
    """Log alert definition"""
    id: str
    name: str
    description: str
    level: AlertLevel
    condition: str  # SQL condition
    threshold: int
    time_window_minutes: int
    last_triggered: Optional[str] = None
    trigger_count: int = 0
    is_active: bool = True
    notification_channels: List[str] = None
    
    def __post_init__(self):
        if self.notification_channels is None:
            self.notification_channels = []


@dataclass
class AlertEvent:
    """Alert event instance"""
    alert_id: str
    alert_name: str
    level: AlertLevel
    message: str
    details: Dict[str, Any]
    timestamp: str
    count: int = 1


class LogMonitor:
    """Real-time log monitoring system"""
    
    def __init__(self):
        self.db_path = settings.shared_dir / 'enhanced_logs.sqlite'
        self.alerts_db_path = settings.shared_dir / 'log_alerts.sqlite'
        self._alerts = {}
        self._running = False
        self._monitor_thread = None
        self._alert_handlers = {}
        self._setup_alerts_db()
        self._load_default_alerts()
    
    def _setup_alerts_db(self):
        """Setup alerts database"""
        try:
            create_sql = """
            CREATE TABLE IF NOT EXISTS log_alerts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                level TEXT NOT NULL,
                condition_sql TEXT NOT NULL,
                threshold INTEGER NOT NULL,
                time_window_minutes INTEGER NOT NULL,
                last_triggered TEXT,
                trigger_count INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                notification_channels TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            
            CREATE TABLE IF NOT EXISTS alert_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                alert_id TEXT NOT NULL,
                alert_name TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                details TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                count INTEGER DEFAULT 1,
                acknowledged BOOLEAN DEFAULT 0,
                acknowledged_by TEXT,
                acknowledged_at TEXT
            );
            
            CREATE INDEX IF NOT EXISTS idx_alert_events_timestamp ON alert_events(timestamp);
            CREATE INDEX IF NOT EXISTS idx_alert_events_level ON alert_events(level);
            CREATE INDEX IF NOT EXISTS idx_alert_events_acknowledged ON alert_events(acknowledged);
            """
            
            db_manager.execute_script(self.alerts_db_path, create_sql)
            
        except Exception as e:
            enhanced_monitoring_logger.error(f"Failed to setup alerts database: {e}")
    
    def _load_default_alerts(self):
        """Load default alert configurations"""
        default_alerts = [
            LogAlert(
                id="high_error_rate",
                name="High Error Rate",
                description="Too many errors in short time period",
                level=AlertLevel.HIGH,
                condition="level IN ('ERROR', 'CRITICAL')",
                threshold=10,
                time_window_minutes=5,
                notification_channels=["console"]
            ),
            LogAlert(
                id="critical_exceptions",
                name="Critical Exceptions",
                description="Critical level exceptions detected",
                level=AlertLevel.CRITICAL,
                condition="level = 'CRITICAL'",
                threshold=1,
                time_window_minutes=1,
                notification_channels=["console", "file"]
            ),
            LogAlert(
                id="database_errors",
                name="Database Connection Issues",
                description="Database connection or query failures",
                level=AlertLevel.HIGH,
                condition="logger_name LIKE '%database%' AND level = 'ERROR'",
                threshold=5,
                time_window_minutes=10,
                notification_channels=["console"]
            ),
            LogAlert(
                id="auth_failures",
                name="Authentication Failures",
                description="Multiple authentication failures",
                level=AlertLevel.MEDIUM,
                condition="logger_name LIKE '%auth%' AND level = 'ERROR'",
                threshold=3,
                time_window_minutes=15,
                notification_channels=["console"]
            ),
            LogAlert(
                id="performance_degradation",
                name="Performance Degradation",
                description="Operations taking longer than usual",
                level=AlertLevel.MEDIUM,
                condition="JSON_EXTRACT(extra_data, '$.duration_ms') > 5000",
                threshold=5,
                time_window_minutes=10,
                notification_channels=["console"]
            ),
            LogAlert(
                id="repeated_pattern",
                name="Repeated Error Pattern",
                description="Same error pattern occurring frequently",
                level=AlertLevel.LOW,
                condition="1=1",  # Special handling in code
                threshold=20,
                time_window_minutes=60,
                notification_channels=["console"]
            )
        ]
        
        for alert in default_alerts:
            self._alerts[alert.id] = alert
            self._save_alert(alert)
    
    def _save_alert(self, alert: LogAlert):
        """Save alert configuration to database"""
        try:
            insert_sql = """
            INSERT OR REPLACE INTO log_alerts (
                id, name, description, level, condition_sql, threshold,
                time_window_minutes, last_triggered, trigger_count, is_active,
                notification_channels, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            now = datetime.now().isoformat()
            params = (
                alert.id, alert.name, alert.description, alert.level.value,
                alert.condition, alert.threshold, alert.time_window_minutes,
                alert.last_triggered, alert.trigger_count, alert.is_active,
                json.dumps(alert.notification_channels), now, now
            )
            
            db_manager.execute_command(self.alerts_db_path, insert_sql, params)
            
        except Exception as e:
            enhanced_monitoring_logger.error(f"Failed to save alert {alert.id}: {e}")
    
    def add_alert_handler(self, channel: str, handler: Callable[[AlertEvent], None]):
        """Add custom alert handler"""
        self._alert_handlers[channel] = handler
        enhanced_monitoring_logger.info(f"Added alert handler for channel: {channel}")
    
    def start_monitoring(self):
        """Start real-time log monitoring"""
        if self._running:
            return
        
        self._running = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        enhanced_monitoring_logger.info("Log monitoring started")
    
    def stop_monitoring(self):
        """Stop log monitoring"""
        self._running = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=5)
        enhanced_monitoring_logger.info("Log monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self._running:
            try:
                self._check_alerts()
                time.sleep(30)  # Check every 30 seconds
            except Exception as e:
                enhanced_monitoring_logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _check_alerts(self):
        """Check all active alerts"""
        for alert in self._alerts.values():
            if not alert.is_active:
                continue
            
            try:
                if alert.id == "repeated_pattern":
                    self._check_pattern_alert(alert)
                else:
                    self._check_standard_alert(alert)
            except Exception as e:
                enhanced_monitoring_logger.error(f"Error checking alert {alert.id}: {e}")
    
    def _check_standard_alert(self, alert: LogAlert):
        """Check standard SQL-based alert"""
        time_threshold = datetime.now() - timedelta(minutes=alert.time_window_minutes)
        
        count_sql = f"""
        SELECT COUNT(*) as count
        FROM log_entries
        WHERE timestamp > ? AND ({alert.condition})
        """
        
        try:
            results = db_manager.execute_query(
                self.db_path, count_sql, (time_threshold.isoformat(),)
            )
            
            count = results[0]['count'] if results else 0
            
            if count >= alert.threshold:
                self._trigger_alert(alert, count, {
                    'time_window': alert.time_window_minutes,
                    'actual_count': count,
                    'threshold': alert.threshold
                })
                
        except Exception as e:
            enhanced_monitoring_logger.error(f"Error checking alert {alert.id}: {e}")
    
    def _check_pattern_alert(self, alert: LogAlert):
        """Check repeated pattern alert"""
        time_threshold = datetime.now() - timedelta(minutes=alert.time_window_minutes)
        
        pattern_sql = """
        SELECT pattern_hash, pattern_template, occurrence_count
        FROM log_patterns
        WHERE last_occurrence > ? AND occurrence_count >= ?
        ORDER BY occurrence_count DESC
        LIMIT 5
        """
        
        try:
            results = db_manager.execute_query(
                self.db_path, pattern_sql, 
                (time_threshold.isoformat(), alert.threshold)
            )
            
            for row in results:
                self._trigger_alert(alert, row['occurrence_count'], {
                    'pattern_template': row['pattern_template'],
                    'pattern_hash': row['pattern_hash'],
                    'occurrence_count': row['occurrence_count']
                })
                
        except Exception as e:
            enhanced_monitoring_logger.error(f"Error checking pattern alert: {e}")
    
    def _trigger_alert(self, alert: LogAlert, count: int, details: Dict[str, Any]):
        """Trigger an alert"""
        now = datetime.now()
        
        # Check if alert was recently triggered (avoid spam)
        if alert.last_triggered:
            last_trigger = datetime.fromisoformat(alert.last_triggered)
            if now - last_trigger < timedelta(minutes=alert.time_window_minutes):
                return
        
        # Update alert state
        alert.last_triggered = now.isoformat()
        alert.trigger_count += 1
        self._save_alert(alert)
        
        # Create alert event
        event = AlertEvent(
            alert_id=alert.id,
            alert_name=alert.name,
            level=alert.level,
            message=f"{alert.name}: {count} occurrences in {alert.time_window_minutes} minutes",
            details=details,
            timestamp=now.isoformat(),
            count=count
        )
        
        # Store alert event
        self._store_alert_event(event)
        
        # Send notifications
        self._send_notifications(event, alert)
        
        enhanced_monitoring_logger.warning(
            f"Alert triggered: {event.alert_name}",
            alert_id=event.alert_id,
            level=event.level.value,
            count=event.count,
            details=event.details
        )
    
    def _store_alert_event(self, event: AlertEvent):
        """Store alert event in database"""
        try:
            insert_sql = """
            INSERT INTO alert_events (
                alert_id, alert_name, level, message, details, timestamp, count
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            db_manager.execute_command(
                self.alerts_db_path, insert_sql,
                (event.alert_id, event.alert_name, event.level.value,
                 event.message, json.dumps(event.details), event.timestamp, event.count)
            )
            
        except Exception as e:
            enhanced_monitoring_logger.error(f"Failed to store alert event: {e}")
    
    def _send_notifications(self, event: AlertEvent, alert: LogAlert):
        """Send alert notifications"""
        for channel in alert.notification_channels:
            try:
                if channel == "console":
                    self._console_notification(event)
                elif channel == "file":
                    self._file_notification(event)
                elif channel in self._alert_handlers:
                    self._alert_handlers[channel](event)
                else:
                    enhanced_monitoring_logger.warning(f"Unknown notification channel: {channel}")
            except Exception as e:
                enhanced_monitoring_logger.error(f"Failed to send notification to {channel}: {e}")
    
    def _console_notification(self, event: AlertEvent):
        """Send console notification"""
        print(f"\nALERT [{event.level.value.upper()}]: {event.message}")
        print(f"   Details: {json.dumps(event.details, indent=2)}")
        print(f"   Time: {event.timestamp}\n")
    
    def _file_notification(self, event: AlertEvent):
        """Send file notification"""
        alert_file = settings.shared_dir / 'alerts.log'
        try:
            with open(alert_file, 'a', encoding='utf-8') as f:
                f.write(f"{event.timestamp} | {event.level.value.upper()} | {event.message}\n")
                f.write(f"Details: {json.dumps(event.details)}\n")
                f.write("-" * 80 + "\n")
        except Exception as e:
            enhanced_monitoring_logger.error(f"Failed to write alert to file: {e}")
    
    def get_recent_alerts(self, hours: int = 24, level: Optional[AlertLevel] = None) -> List[Dict[str, Any]]:
        """Get recent alert events"""
        since = datetime.now() - timedelta(hours=hours)
        
        sql = """
        SELECT * FROM alert_events 
        WHERE timestamp > ?
        """
        params = [since.isoformat()]
        
        if level:
            sql += " AND level = ?"
            params.append(level.value)
        
        sql += " ORDER BY timestamp DESC LIMIT 100"
        
        try:
            results = db_manager.execute_query(self.alerts_db_path, sql, params)
            return [dict(row) for row in results]
        except Exception as e:
            enhanced_monitoring_logger.error(f"Failed to get recent alerts: {e}")
            return []
    
    def get_alert_statistics(self, hours: int = 24) -> Dict[str, Any]:
        """Get alert statistics"""
        since = datetime.now() - timedelta(hours=hours)
        
        try:
            # Alert counts by level
            level_sql = """
            SELECT level, COUNT(*) as count
            FROM alert_events
            WHERE timestamp > ?
            GROUP BY level
            """
            
            level_results = db_manager.execute_query(
                self.alerts_db_path, level_sql, (since.isoformat(),)
            )
            level_counts = {row['level']: row['count'] for row in level_results}
            
            # Alert counts by type
            type_sql = """
            SELECT alert_name, COUNT(*) as count, MAX(timestamp) as last_occurrence
            FROM alert_events
            WHERE timestamp > ?
            GROUP BY alert_name
            ORDER BY count DESC
            """
            
            type_results = db_manager.execute_query(
                self.alerts_db_path, type_sql, (since.isoformat(),)
            )
            alert_types = [dict(row) for row in type_results]
            
            return {
                'time_period': f'Last {hours} hours',
                'total_alerts': sum(level_counts.values()),
                'alerts_by_level': level_counts,
                'alerts_by_type': alert_types,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            enhanced_monitoring_logger.error(f"Failed to get alert statistics: {e}")
            return {'error': str(e)}
    
    def acknowledge_alert(self, alert_event_id: int, acknowledged_by: str) -> bool:
        """Acknowledge an alert event"""
        try:
            update_sql = """
            UPDATE alert_events 
            SET acknowledged = 1, acknowledged_by = ?, acknowledged_at = ?
            WHERE id = ?
            """
            
            affected = db_manager.execute_command(
                self.alerts_db_path, update_sql,
                (acknowledged_by, datetime.now().isoformat(), alert_event_id)
            )
            
            return affected > 0
            
        except Exception as e:
            enhanced_monitoring_logger.error(f"Failed to acknowledge alert {alert_event_id}: {e}")
            return False


class LogDashboard:
    """Log monitoring dashboard"""
    
    def __init__(self, monitor: LogMonitor):
        self.monitor = monitor
        self.analyzer = log_analyzer
    
    def get_dashboard_data(self, hours: int = 24) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        return {
            'timestamp': datetime.now().isoformat(),
            'time_period': f'Last {hours} hours',
            'log_summary': self.analyzer.get_log_summary(hours),
            'performance_metrics': self.analyzer.get_performance_metrics(hours),
            'error_analysis': self.analyzer.get_error_analysis(hours),
            'alert_statistics': self.monitor.get_alert_statistics(hours),
            'recent_alerts': self.monitor.get_recent_alerts(hours=1)  # Last hour only
        }
    
    def generate_report(self, hours: int = 24) -> str:
        """Generate text-based monitoring report"""
        data = self.get_dashboard_data(hours)
        
        report_lines = [
            "=" * 80,
            f"LOG MONITORING REPORT - {data['timestamp']}",
            f"Time Period: {data['time_period']}",
            "=" * 80,
            "",
            "LOG SUMMARY:",
            f"  Total Entries: {data['log_summary'].get('total_entries', 0)}",
        ]
        
        # Level counts
        level_counts = data['log_summary'].get('level_counts', {})
        for level, count in level_counts.items():
            report_lines.append(f"  {level}: {count}")
        
        report_lines.extend([
            "",
            "ALERTS:",
            f"  Total Alerts: {data['alert_statistics'].get('total_alerts', 0)}"
        ])
        
        # Alert level breakdown
        alerts_by_level = data['alert_statistics'].get('alerts_by_level', {})
        for level, count in alerts_by_level.items():
            report_lines.append(f"  {level.upper()}: {count}")
        
        # Recent critical alerts
        recent_alerts = [a for a in data['recent_alerts'] if a['level'] in ['high', 'critical']]
        if recent_alerts:
            report_lines.extend([
                "",
                "RECENT CRITICAL ALERTS:",
            ])
            for alert in recent_alerts[:5]:
                report_lines.append(f"  - {alert['alert_name']} at {alert['timestamp']}")
        
        # Performance overview
        perf_data = data['performance_metrics'].get('performance_data', [])
        if perf_data:
            report_lines.extend([
                "",
                "PERFORMANCE OVERVIEW:",
                f"  Total Operations: {data['performance_metrics'].get('total_operations', 0)}"
            ])
            
            # Slowest operations
            slowest = sorted(perf_data, key=lambda x: x['avg_duration_ms'], reverse=True)[:3]
            for op in slowest:
                report_lines.append(f"  {op['operation']}: {op['avg_duration_ms']:.1f}ms avg")
        
        # Error summary
        error_summary = data['error_analysis'].get('recent_errors', [])
        if error_summary:
            report_lines.extend([
                "",
                "RECENT ERRORS:",
                f"  Total Errors: {len(error_summary)}"
            ])
            
            for error in error_summary[:3]:
                report_lines.append(f"  - {error.get('exception_type', 'Unknown')}: {error.get('message', '')[:60]}...")
        
        report_lines.extend([
            "",
            "=" * 80
        ])
        
        return "\n".join(report_lines)


# Global instances
log_monitor = LogMonitor()
log_dashboard = LogDashboard(log_monitor)


def setup_enhanced_monitoring():
    """Setup and start enhanced log monitoring"""
    try:
        # Start log monitoring
        log_monitor.start_monitoring()
        
        # Add custom alert handlers if needed
        # log_monitor.add_alert_handler("email", email_notification_handler)
        # log_monitor.add_alert_handler("slack", slack_notification_handler)
        
        enhanced_monitoring_logger.info("Enhanced log monitoring setup completed")
        return True
        
    except Exception as e:
        enhanced_monitoring_logger.error(f"Failed to setup enhanced monitoring: {e}")
        return False


def get_monitoring_status() -> Dict[str, Any]:
    """Get current monitoring system status"""
    return {
        'monitoring_active': log_monitor._running,
        'total_alerts_configured': len(log_monitor._alerts),
        'active_alerts': len([a for a in log_monitor._alerts.values() if a.is_active]),
        'alert_handlers': list(log_monitor._alert_handlers.keys()),
        'last_check': datetime.now().isoformat()
    }