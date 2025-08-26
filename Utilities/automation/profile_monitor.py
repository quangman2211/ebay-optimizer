#!/usr/bin/env python3
"""
Browser Profile Monitoring System
Real-time monitoring and health checking for 30 eBay browser profiles
"""

import asyncio
import json
import logging
import time
import psutil
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum
import subprocess
import threading
from collections import defaultdict, deque

from browser_profile_manager import BrowserProfileManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"
    WARNING = "warning" 
    CRITICAL = "critical"
    UNKNOWN = "unknown"

@dataclass
class ProfileHealth:
    """Profile health metrics"""
    account_id: int
    status: str
    health: HealthStatus
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    response_time: float = 0.0
    last_activity: datetime = None
    error_count: int = 0
    success_rate: float = 100.0
    uptime: timedelta = timedelta(0)
    browser_process_id: Optional[int] = None
    proxy_status: str = "unknown"
    sheet_sync_status: str = "unknown"
    last_check: datetime = None
    
    def __post_init__(self):
        if self.last_check is None:
            self.last_check = datetime.now()

@dataclass
class SystemMetrics:
    """System-wide metrics"""
    timestamp: datetime
    total_profiles: int
    active_profiles: int
    healthy_profiles: int
    warning_profiles: int
    critical_profiles: int
    avg_cpu_usage: float
    avg_memory_usage: float
    total_memory_mb: float
    free_memory_mb: float
    network_io: Dict[str, int]
    disk_usage: Dict[str, float]

class ProfileMonitor:
    """Monitors browser profiles and system health"""
    
    def __init__(self, config_path: str = None, check_interval: int = 60):
        self.profile_manager = BrowserProfileManager(config_path)
        self.check_interval = check_interval
        
        # Health tracking
        self.profile_health: Dict[int, ProfileHealth] = {}
        self.health_history: Dict[int, deque] = defaultdict(lambda: deque(maxlen=100))
        self.system_metrics: deque = deque(maxlen=1000)
        
        # Monitoring state
        self.monitoring_active = False
        self.monitor_thread = None
        
        # Alert configuration
        self.alert_thresholds = {
            "cpu_warning": 70.0,
            "cpu_critical": 90.0,
            "memory_warning": 80.0,
            "memory_critical": 95.0,
            "response_time_warning": 5.0,
            "response_time_critical": 15.0,
            "error_rate_warning": 10.0,
            "error_rate_critical": 25.0
        }
        
        # Process tracking
        self.process_cache: Dict[int, psutil.Process] = {}
        
        logger.info("Profile monitor initialized")
    
    def get_browser_processes(self) -> Dict[int, List[psutil.Process]]:
        """Get browser processes grouped by profile"""
        processes = {}
        
        try:
            # Look for common browser process names
            browser_names = [
                'chrome', 'chromium', 'firefox', 'opera', 
                'hidemyacc', 'multilogin', 'antidetect'
            ]
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info']):
                try:
                    proc_info = proc.info
                    proc_name = proc_info['name'].lower()
                    
                    # Check if it's a browser process
                    if any(browser in proc_name for browser in browser_names):
                        # Try to extract profile info from command line
                        cmdline = ' '.join(proc_info.get('cmdline', []))
                        
                        # Look for profile identifiers in command line
                        for account_id in self.profile_manager.profiles.keys():
                            profile_config = self.profile_manager.get_profile(int(account_id))
                            if profile_config:
                                profile_id = profile_config.get('profile_id', '')
                                profile_name = profile_config.get('profile_name', '')
                                
                                if profile_id in cmdline or profile_name in cmdline:
                                    if int(account_id) not in processes:
                                        processes[int(account_id)] = []
                                    processes[int(account_id)].append(proc)
                                    break
                
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        
        except Exception as e:
            logger.error(f"Error getting browser processes: {e}")
        
        return processes
    
    def check_profile_health(self, account_id: int) -> ProfileHealth:
        """Check health of a specific profile"""
        profile_config = self.profile_manager.get_profile(account_id)
        if not profile_config:
            return ProfileHealth(
                account_id=account_id,
                status="not_configured",
                health=HealthStatus.CRITICAL
            )
        
        health = ProfileHealth(
            account_id=account_id,
            status="checking",
            health=HealthStatus.UNKNOWN
        )
        
        try:
            # Check if browser process is running
            browser_processes = self.get_browser_processes().get(account_id, [])
            
            if browser_processes:
                health.status = "running"
                health.browser_process_id = browser_processes[0].pid
                
                # Calculate CPU and memory usage
                total_cpu = sum(proc.cpu_percent() for proc in browser_processes)
                total_memory = sum(proc.memory_info().rss for proc in browser_processes)
                
                health.cpu_usage = total_cpu
                health.memory_usage = total_memory / (1024 * 1024)  # MB
                
                # Check response time (simulate browser health check)
                start_time = time.time()
                health.response_time = self._check_browser_response(account_id)
                
                # Update last activity
                health.last_activity = datetime.now()
                
            else:
                health.status = "stopped"
                health.browser_process_id = None
            
            # Check proxy status
            health.proxy_status = self._check_proxy_status(account_id)
            
            # Check Google Sheets sync status
            health.sheet_sync_status = self._check_sheet_sync_status(account_id)
            
            # Calculate health status
            health.health = self._calculate_health_status(health)
            
            # Update success rate based on history
            health.success_rate = self._calculate_success_rate(account_id)
            
        except Exception as e:
            logger.error(f"Error checking health for profile {account_id}: {e}")
            health.status = "error"
            health.health = HealthStatus.CRITICAL
            health.error_count += 1
        
        health.last_check = datetime.now()
        return health
    
    def _check_browser_response(self, account_id: int) -> float:
        """Check browser response time"""
        # This would need to integrate with browser automation
        # For now, simulate response check
        start_time = time.time()
        
        try:
            # Simulate health check - in real implementation:
            # 1. Send message to Chrome extension
            # 2. Check if browser responds
            # 3. Measure response time
            time.sleep(0.1)  # Simulate check time
            return (time.time() - start_time) * 1000  # ms
            
        except Exception:
            return -1  # Indicates error
    
    def _check_proxy_status(self, account_id: int) -> str:
        """Check proxy connectivity for profile"""
        profile_config = self.profile_manager.get_profile(account_id)
        if not profile_config:
            return "unknown"
        
        proxy_config = profile_config.get("proxy_config", {})
        
        # This would check actual proxy connectivity
        # For now, simulate proxy check
        return "connected"
    
    def _check_sheet_sync_status(self, account_id: int) -> str:
        """Check Google Sheets sync status"""
        profile_config = self.profile_manager.get_profile(account_id)
        if not profile_config:
            return "unknown"
        
        sheet_id = profile_config.get("sheet_id")
        if not sheet_id:
            return "no_sheet_configured"
        
        # This would check actual Google Sheets access
        # For now, simulate check
        return "synced"
    
    def _calculate_health_status(self, health: ProfileHealth) -> HealthStatus:
        """Calculate overall health status"""
        if health.status == "error" or health.response_time < 0:
            return HealthStatus.CRITICAL
        
        critical_conditions = [
            health.cpu_usage > self.alert_thresholds["cpu_critical"],
            health.memory_usage > self.alert_thresholds["memory_critical"],
            health.response_time > self.alert_thresholds["response_time_critical"],
            health.success_rate < (100 - self.alert_thresholds["error_rate_critical"])
        ]
        
        warning_conditions = [
            health.cpu_usage > self.alert_thresholds["cpu_warning"],
            health.memory_usage > self.alert_thresholds["memory_warning"],
            health.response_time > self.alert_thresholds["response_time_warning"],
            health.success_rate < (100 - self.alert_thresholds["error_rate_warning"])
        ]
        
        if any(critical_conditions):
            return HealthStatus.CRITICAL
        elif any(warning_conditions):
            return HealthStatus.WARNING
        elif health.status == "running":
            return HealthStatus.HEALTHY
        else:
            return HealthStatus.UNKNOWN
    
    def _calculate_success_rate(self, account_id: int) -> float:
        """Calculate success rate based on historical data"""
        history = self.health_history.get(account_id, deque())
        
        if len(history) == 0:
            return 100.0
        
        successful = sum(1 for h in history if h.health in [HealthStatus.HEALTHY, HealthStatus.WARNING])
        return (successful / len(history)) * 100.0
    
    def check_all_profiles(self) -> Dict[int, ProfileHealth]:
        """Check health of all profiles"""
        results = {}
        
        for account_id in self.profile_manager.profiles.keys():
            account_id = int(account_id)
            health = self.check_profile_health(account_id)
            results[account_id] = health
            
            # Update health tracking
            self.profile_health[account_id] = health
            self.health_history[account_id].append(health)
        
        return results
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        try:
            # CPU and memory info
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Network I/O
            network = psutil.net_io_counters()
            network_io = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv
            }
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage = {
                "total_gb": disk.total / (1024**3),
                "used_gb": disk.used / (1024**3),
                "free_gb": disk.free / (1024**3),
                "percent": (disk.used / disk.total) * 100
            }
            
            # Profile statistics
            profile_stats = self._get_profile_statistics()
            
            metrics = SystemMetrics(
                timestamp=datetime.now(),
                total_profiles=profile_stats["total"],
                active_profiles=profile_stats["active"],
                healthy_profiles=profile_stats["healthy"],
                warning_profiles=profile_stats["warning"],
                critical_profiles=profile_stats["critical"],
                avg_cpu_usage=cpu_percent,
                avg_memory_usage=memory.percent,
                total_memory_mb=memory.total / (1024 * 1024),
                free_memory_mb=memory.available / (1024 * 1024),
                network_io=network_io,
                disk_usage=disk_usage
            )
            
            self.system_metrics.append(metrics)
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return None
    
    def _get_profile_statistics(self) -> Dict[str, int]:
        """Get profile statistics summary"""
        stats = {
            "total": len(self.profile_manager.profiles),
            "active": 0,
            "healthy": 0,
            "warning": 0,
            "critical": 0,
            "unknown": 0
        }
        
        for health in self.profile_health.values():
            if health.status == "running":
                stats["active"] += 1
            
            if health.health == HealthStatus.HEALTHY:
                stats["healthy"] += 1
            elif health.health == HealthStatus.WARNING:
                stats["warning"] += 1
            elif health.health == HealthStatus.CRITICAL:
                stats["critical"] += 1
            else:
                stats["unknown"] += 1
        
        return stats
    
    def get_alerts(self, severity: str = None) -> List[Dict]:
        """Get current alerts"""
        alerts = []
        
        for account_id, health in self.profile_health.items():
            profile_config = self.profile_manager.get_profile(account_id)
            username = profile_config.get("ebay_username", f"Account_{account_id}") if profile_config else f"Account_{account_id}"
            
            if health.health == HealthStatus.CRITICAL:
                alerts.append({
                    "severity": "critical",
                    "account_id": account_id,
                    "username": username,
                    "message": f"Profile {username} is in critical state",
                    "details": {
                        "status": health.status,
                        "cpu_usage": health.cpu_usage,
                        "memory_usage": health.memory_usage,
                        "response_time": health.response_time,
                        "success_rate": health.success_rate
                    },
                    "timestamp": health.last_check
                })
            
            elif health.health == HealthStatus.WARNING:
                alerts.append({
                    "severity": "warning",
                    "account_id": account_id,
                    "username": username,
                    "message": f"Profile {username} has warnings",
                    "details": {
                        "status": health.status,
                        "cpu_usage": health.cpu_usage,
                        "memory_usage": health.memory_usage,
                        "response_time": health.response_time
                    },
                    "timestamp": health.last_check
                })
        
        # Filter by severity if specified
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]
        
        # Sort by severity and timestamp
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        alerts.sort(key=lambda x: (severity_order.get(x["severity"], 3), x["timestamp"]), reverse=True)
        
        return alerts
    
    def generate_health_report(self) -> Dict:
        """Generate comprehensive health report"""
        system_metrics = self.get_system_metrics()
        alerts = self.get_alerts()
        
        # VPS breakdown
        vps_health = {}
        for vps_id in range(1, 6):
            vps_profiles = self.profile_manager.get_vps_profiles(vps_id)
            vps_account_ids = [p.get("account_id") for p in vps_profiles]
            
            vps_stats = {
                "total_profiles": len(vps_account_ids),
                "healthy": 0,
                "warning": 0,
                "critical": 0,
                "avg_cpu": 0,
                "avg_memory": 0
            }
            
            cpu_values = []
            memory_values = []
            
            for account_id in vps_account_ids:
                health = self.profile_health.get(account_id)
                if health:
                    if health.health == HealthStatus.HEALTHY:
                        vps_stats["healthy"] += 1
                    elif health.health == HealthStatus.WARNING:
                        vps_stats["warning"] += 1
                    elif health.health == HealthStatus.CRITICAL:
                        vps_stats["critical"] += 1
                    
                    if health.cpu_usage > 0:
                        cpu_values.append(health.cpu_usage)
                    if health.memory_usage > 0:
                        memory_values.append(health.memory_usage)
            
            if cpu_values:
                vps_stats["avg_cpu"] = sum(cpu_values) / len(cpu_values)
            if memory_values:
                vps_stats["avg_memory"] = sum(memory_values) / len(memory_values)
            
            vps_health[f"VPS_{vps_id}"] = vps_stats
        
        return {
            "report_timestamp": datetime.now().isoformat(),
            "system_metrics": asdict(system_metrics) if system_metrics else None,
            "profile_summary": self._get_profile_statistics(),
            "vps_health": vps_health,
            "alerts": alerts,
            "top_issues": self._get_top_issues(),
            "recommendations": self._generate_recommendations()
        }
    
    def _get_top_issues(self) -> List[Dict]:
        """Get top issues across all profiles"""
        issues = []
        
        for account_id, health in self.profile_health.items():
            profile_config = self.profile_manager.get_profile(account_id)
            username = profile_config.get("ebay_username", f"Account_{account_id}") if profile_config else f"Account_{account_id}"
            
            if health.health == HealthStatus.CRITICAL:
                issues.append({
                    "account_id": account_id,
                    "username": username,
                    "issue_type": "critical_health",
                    "severity": "critical",
                    "description": f"Profile {username} is in critical state"
                })
            
            if health.cpu_usage > self.alert_thresholds["cpu_warning"]:
                issues.append({
                    "account_id": account_id,
                    "username": username,
                    "issue_type": "high_cpu",
                    "severity": "warning" if health.cpu_usage < self.alert_thresholds["cpu_critical"] else "critical",
                    "description": f"High CPU usage: {health.cpu_usage:.1f}%"
                })
            
            if health.memory_usage > self.alert_thresholds["memory_warning"]:
                issues.append({
                    "account_id": account_id,
                    "username": username,
                    "issue_type": "high_memory",
                    "severity": "warning" if health.memory_usage < self.alert_thresholds["memory_critical"] else "critical",
                    "description": f"High memory usage: {health.memory_usage:.1f}MB"
                })
        
        # Sort by severity
        severity_order = {"critical": 0, "warning": 1}
        issues.sort(key=lambda x: severity_order.get(x["severity"], 2))
        
        return issues[:10]  # Top 10 issues
    
    def _generate_recommendations(self) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # System-level recommendations
        if self.system_metrics:
            latest_metrics = self.system_metrics[-1]
            
            if latest_metrics.avg_memory_usage > 80:
                recommendations.append("Consider increasing system memory or reducing concurrent profiles")
            
            if latest_metrics.avg_cpu_usage > 70:
                recommendations.append("High CPU usage detected - consider optimizing profile schedules")
            
            if latest_metrics.disk_usage["percent"] > 85:
                recommendations.append("Low disk space - consider cleaning up logs and temporary files")
        
        # Profile-level recommendations
        critical_profiles = sum(1 for h in self.profile_health.values() if h.health == HealthStatus.CRITICAL)
        if critical_profiles > 5:
            recommendations.append("Multiple profiles in critical state - review overall system health")
        
        high_cpu_profiles = sum(1 for h in self.profile_health.values() if h.cpu_usage > 50)
        if high_cpu_profiles > 10:
            recommendations.append("Many profiles showing high CPU usage - consider staggering schedules")
        
        return recommendations
    
    async def start_monitoring(self):
        """Start continuous monitoring"""
        logger.info("Starting profile monitoring...")
        self.monitoring_active = True
        
        while self.monitoring_active:
            try:
                # Check all profiles
                self.check_all_profiles()
                
                # Get system metrics
                self.get_system_metrics()
                
                # Log summary
                stats = self._get_profile_statistics()
                logger.info(f"Health check complete: {stats['healthy']} healthy, "
                          f"{stats['warning']} warnings, {stats['critical']} critical")
                
                # Wait before next check
                await asyncio.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(30)
    
    def start_monitoring_background(self):
        """Start monitoring in background thread"""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        def run_monitoring():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.start_monitoring())
        
        self.monitor_thread = threading.Thread(target=run_monitoring, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Profile monitoring started in background")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        if not self.monitoring_active:
            return
        
        logger.info("Stopping profile monitoring...")
        self.monitoring_active = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=10)
        
        logger.info("Profile monitoring stopped")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Profile Health Monitor")
    parser.add_argument("action", choices=[
        "check", "monitor", "report", "alerts", "status"
    ])
    parser.add_argument("--account-id", type=int, help="Check specific account")
    parser.add_argument("--vps-id", type=int, help="Check specific VPS")
    parser.add_argument("--interval", type=int, default=60, help="Monitoring interval (seconds)")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--output", help="Output file for report")
    
    args = parser.parse_args()
    
    monitor = ProfileMonitor(args.config, args.interval)
    
    if args.action == "check":
        if args.account_id:
            health = monitor.check_profile_health(args.account_id)
            print(f"Profile {args.account_id} Health:")
            print(json.dumps(asdict(health), indent=2, default=str))
        else:
            results = monitor.check_all_profiles()
            print(f"Health Check Results ({len(results)} profiles):")
            for account_id, health in sorted(results.items()):
                status_icon = {
                    HealthStatus.HEALTHY: "✅",
                    HealthStatus.WARNING: "⚠️",
                    HealthStatus.CRITICAL: "❌",
                    HealthStatus.UNKNOWN: "❓"
                }.get(health.health, "❓")
                
                print(f"{status_icon} Account {account_id}: {health.health.value} "
                      f"(CPU: {health.cpu_usage:.1f}%, Mem: {health.memory_usage:.1f}MB)")
    
    elif args.action == "monitor":
        monitor.start_monitoring_background()
        
        if args.daemon:
            logger.info("Running monitor as daemon...")
            try:
                while monitor.monitoring_active:
                    time.sleep(60)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
        else:
            logger.info("Monitor started. Press Ctrl+C to stop.")
            try:
                time.sleep(10)
                stats = monitor._get_profile_statistics()
                print(f"Monitoring Status: {stats}")
            except KeyboardInterrupt:
                pass
        
        monitor.stop_monitoring()
    
    elif args.action == "report":
        monitor.check_all_profiles()  # Ensure we have current data
        report = monitor.generate_health_report()
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"Health report saved to {args.output}")
        else:
            print("=== HEALTH REPORT ===")
            print(json.dumps(report, indent=2, default=str))
    
    elif args.action == "alerts":
        monitor.check_all_profiles()
        alerts = monitor.get_alerts()
        
        print(f"Current Alerts ({len(alerts)}):")
        for alert in alerts:
            severity_icon = {"critical": "🚨", "warning": "⚠️", "info": "ℹ️"}.get(alert["severity"], "")
            print(f"{severity_icon} [{alert['severity'].upper()}] {alert['message']}")
            if alert.get("details"):
                for key, value in alert["details"].items():
                    print(f"    {key}: {value}")
    
    elif args.action == "status":
        monitor.check_all_profiles()
        system_metrics = monitor.get_system_metrics()
        
        print("=== SYSTEM STATUS ===")
        if system_metrics:
            print(f"CPU Usage: {system_metrics.avg_cpu_usage:.1f}%")
            print(f"Memory Usage: {system_metrics.avg_memory_usage:.1f}%")
            print(f"Active Profiles: {system_metrics.active_profiles}/{system_metrics.total_profiles}")
            print(f"Healthy: {system_metrics.healthy_profiles}, "
                  f"Warnings: {system_metrics.warning_profiles}, "
                  f"Critical: {system_metrics.critical_profiles}")

if __name__ == "__main__":
    main()