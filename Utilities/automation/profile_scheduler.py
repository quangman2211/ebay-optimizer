#!/usr/bin/env python3
"""
Browser Profile Automation Scheduler
Schedules and manages automated eBay data collection across 30 browser profiles
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import schedule
import time
import threading
from dataclasses import dataclass, asdict
from enum import Enum

from browser_profile_manager import BrowserProfileManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProfileStatus(Enum):
    """Browser profile status states"""
    IDLE = "idle"
    STARTING = "starting"
    RUNNING = "running"
    COLLECTING = "collecting"
    ERROR = "error"
    STOPPING = "stopping"
    STOPPED = "stopped"

@dataclass
class CollectionTask:
    """Represents a data collection task"""
    account_id: int
    task_id: str
    scheduled_time: datetime
    collection_type: str  # orders, listings, messages, all
    priority: int = 1  # 1=high, 2=normal, 3=low
    status: str = "scheduled"
    attempts: int = 0
    max_attempts: int = 3
    error_message: str = ""
    created_at: datetime = None
    started_at: datetime = None
    completed_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class ProfileScheduler:
    """Manages automated scheduling and execution of browser profiles"""
    
    def __init__(self, config_path: str = None, max_concurrent_global: int = 10):
        self.profile_manager = BrowserProfileManager(config_path)
        self.max_concurrent_global = max_concurrent_global
        
        # Task management
        self.pending_tasks: List[CollectionTask] = []
        self.running_tasks: Dict[int, CollectionTask] = {}  # account_id -> task
        self.completed_tasks: List[CollectionTask] = []
        
        # Profile status tracking
        self.profile_status: Dict[int, ProfileStatus] = {}
        self.profile_last_activity: Dict[int, datetime] = {}
        
        # Scheduling state
        self.scheduler_running = False
        self.scheduler_thread = None
        
        # Load schedules from config
        self.schedules = self._load_schedules()
        
        logger.info(f"ProfileScheduler initialized with {len(self.schedules)} profiles")
    
    def _load_schedules(self) -> Dict[int, Dict]:
        """Load collection schedules from profile configuration"""
        schedules = {}
        
        for account_id, profile_config in self.profile_manager.profiles.items():
            account_id = int(account_id)
            schedule_config = profile_config.get("schedule", {})
            
            if schedule_config.get("auto_start", False):
                schedules[account_id] = {
                    "collection_times": schedule_config.get("collection_times", ["08:00", "14:00", "20:00"]),
                    "timezone": schedule_config.get("timezone", "UTC"),
                    "collection_types": ["orders", "listings", "messages"],
                    "enabled": True
                }
        
        return schedules
    
    def add_task(self, account_id: int, collection_type: str = "all", 
                 scheduled_time: datetime = None, priority: int = 2) -> str:
        """Add a collection task to the queue"""
        if scheduled_time is None:
            scheduled_time = datetime.now()
        
        task = CollectionTask(
            account_id=account_id,
            task_id=f"task_{account_id}_{int(time.time())}",
            scheduled_time=scheduled_time,
            collection_type=collection_type,
            priority=priority
        )
        
        self.pending_tasks.append(task)
        self.pending_tasks.sort(key=lambda t: (t.priority, t.scheduled_time))
        
        logger.info(f"Added task {task.task_id} for account {account_id}")
        return task.task_id
    
    def schedule_daily_collections(self):
        """Schedule daily collection tasks based on profile configurations"""
        scheduled_count = 0
        
        for account_id, schedule_config in self.schedules.items():
            if not schedule_config.get("enabled", True):
                continue
            
            collection_times = schedule_config.get("collection_times", [])
            timezone_str = schedule_config.get("timezone", "UTC")
            
            for time_str in collection_times:
                try:
                    # Parse time string (HH:MM format)
                    hour, minute = map(int, time_str.split(":"))
                    
                    # Calculate next scheduled time
                    now = datetime.now()
                    scheduled_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    # If time has passed today, schedule for tomorrow
                    if scheduled_time <= now:
                        scheduled_time += timedelta(days=1)
                    
                    # Add task
                    self.add_task(
                        account_id=account_id,
                        collection_type="all",
                        scheduled_time=scheduled_time,
                        priority=2
                    )
                    scheduled_count += 1
                    
                except ValueError as e:
                    logger.error(f"Invalid time format '{time_str}' for account {account_id}: {e}")
        
        logger.info(f"Scheduled {scheduled_count} daily collection tasks")
    
    async def execute_task(self, task: CollectionTask) -> bool:
        """Execute a collection task"""
        account_id = task.account_id
        
        try:
            # Update task status
            task.status = "running"
            task.started_at = datetime.now()
            task.attempts += 1
            
            self.running_tasks[account_id] = task
            self.profile_status[account_id] = ProfileStatus.STARTING
            
            logger.info(f"Starting task {task.task_id} for account {account_id}")
            
            # Start browser profile
            if not self.profile_manager.start_profile(account_id, headless=True):
                raise Exception("Failed to start browser profile")
            
            self.profile_status[account_id] = ProfileStatus.RUNNING
            
            # Wait for profile to be ready
            await asyncio.sleep(10)
            
            # Perform data collection
            self.profile_status[account_id] = ProfileStatus.COLLECTING
            success = await self._perform_collection(account_id, task.collection_type)
            
            if not success:
                raise Exception("Data collection failed")
            
            # Stop browser profile
            self.profile_status[account_id] = ProfileStatus.STOPPING
            self.profile_manager.stop_profile(account_id)
            
            # Mark task as completed
            task.status = "completed"
            task.completed_at = datetime.now()
            self.profile_status[account_id] = ProfileStatus.IDLE
            
            logger.info(f"Task {task.task_id} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Task {task.task_id} failed: {e}")
            
            task.status = "error" if task.attempts >= task.max_attempts else "retry"
            task.error_message = str(e)
            self.profile_status[account_id] = ProfileStatus.ERROR
            
            # Try to stop profile if it's running
            try:
                self.profile_manager.stop_profile(account_id)
            except:
                pass
            
            return False
            
        finally:
            # Clean up
            if account_id in self.running_tasks:
                del self.running_tasks[account_id]
            
            self.profile_last_activity[account_id] = datetime.now()
            
            # Move to completed tasks
            self.completed_tasks.append(task)
            
            # Keep only last 100 completed tasks
            if len(self.completed_tasks) > 100:
                self.completed_tasks = self.completed_tasks[-100:]
    
    async def _perform_collection(self, account_id: int, collection_type: str) -> bool:
        """Perform actual data collection for an account"""
        # This would integrate with the Chrome extension
        # For now, simulate collection process
        
        profile_config = self.profile_manager.get_profile(account_id)
        if not profile_config:
            return False
        
        sheet_id = profile_config.get("sheet_id")
        if not sheet_id:
            logger.error(f"No sheet ID configured for account {account_id}")
            return False
        
        # Simulate collection process
        logger.info(f"Collecting {collection_type} data for account {account_id}")
        
        # In real implementation, this would:
        # 1. Navigate browser to eBay pages
        # 2. Trigger Chrome extension data collection
        # 3. Wait for data to be written to Google Sheets
        # 4. Verify data was collected successfully
        
        await asyncio.sleep(30)  # Simulate collection time
        
        logger.info(f"Collection completed for account {account_id}")
        return True
    
    async def run_scheduler(self):
        """Main scheduler loop"""
        logger.info("Starting profile scheduler")
        self.scheduler_running = True
        
        while self.scheduler_running:
            try:
                current_time = datetime.now()
                
                # Find tasks ready to execute
                ready_tasks = [
                    task for task in self.pending_tasks 
                    if task.scheduled_time <= current_time and task.status == "scheduled"
                ]
                
                # Process ready tasks
                for task in ready_tasks:
                    # Check if we can run more tasks
                    if len(self.running_tasks) >= self.max_concurrent_global:
                        logger.info("Maximum concurrent tasks reached, waiting...")
                        break
                    
                    # Check if this account is already running
                    if task.account_id in self.running_tasks:
                        continue
                    
                    # Remove from pending and start execution
                    self.pending_tasks.remove(task)
                    asyncio.create_task(self.execute_task(task))
                
                # Check for retry tasks
                retry_tasks = [
                    task for task in self.completed_tasks
                    if task.status == "retry" and task.attempts < task.max_attempts
                ]
                
                for task in retry_tasks:
                    # Wait at least 5 minutes between retries
                    if (datetime.now() - task.started_at).total_seconds() > 300:
                        task.status = "scheduled"
                        self.pending_tasks.append(task)
                        self.completed_tasks.remove(task)
                
                # Sleep before next iteration
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)
    
    def start_scheduler(self):
        """Start the scheduler in a background thread"""
        if self.scheduler_running:
            logger.warning("Scheduler already running")
            return
        
        def run_async_scheduler():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.run_scheduler())
        
        self.scheduler_thread = threading.Thread(target=run_async_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Profile scheduler started in background thread")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        if not self.scheduler_running:
            return
        
        logger.info("Stopping profile scheduler...")
        self.scheduler_running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        
        logger.info("Profile scheduler stopped")
    
    def get_status(self) -> Dict:
        """Get current scheduler status"""
        return {
            "scheduler_running": self.scheduler_running,
            "pending_tasks": len(self.pending_tasks),
            "running_tasks": len(self.running_tasks),
            "completed_tasks": len(self.completed_tasks),
            "profile_status": {
                account_id: status.value 
                for account_id, status in self.profile_status.items()
            },
            "next_scheduled_tasks": [
                {
                    "task_id": task.task_id,
                    "account_id": task.account_id,
                    "scheduled_time": task.scheduled_time.isoformat(),
                    "collection_type": task.collection_type
                }
                for task in sorted(self.pending_tasks, key=lambda t: t.scheduled_time)[:10]
            ]
        }
    
    def get_task_history(self, account_id: int = None, limit: int = 50) -> List[Dict]:
        """Get task execution history"""
        tasks = self.completed_tasks
        
        if account_id:
            tasks = [t for t in tasks if t.account_id == account_id]
        
        # Sort by completion time (most recent first)
        tasks = sorted(tasks, key=lambda t: t.completed_at or t.created_at, reverse=True)
        
        return [asdict(task) for task in tasks[:limit]]
    
    def schedule_immediate_collection(self, account_ids: List[int] = None, 
                                    collection_type: str = "all") -> List[str]:
        """Schedule immediate collection for specified accounts"""
        if account_ids is None:
            account_ids = list(self.profile_manager.profiles.keys())
            account_ids = [int(aid) for aid in account_ids]
        
        task_ids = []
        for account_id in account_ids:
            task_id = self.add_task(
                account_id=account_id,
                collection_type=collection_type,
                scheduled_time=datetime.now(),
                priority=1  # High priority
            )
            task_ids.append(task_id)
        
        logger.info(f"Scheduled immediate collection for {len(account_ids)} accounts")
        return task_ids
    
    def schedule_vps_collection(self, vps_id: int, collection_type: str = "all") -> List[str]:
        """Schedule collection for all accounts on a specific VPS"""
        vps_profiles = self.profile_manager.get_vps_profiles(vps_id)
        account_ids = [profile.get("account_id") for profile in vps_profiles]
        
        return self.schedule_immediate_collection(account_ids, collection_type)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Profile Automation Scheduler")
    parser.add_argument("action", choices=[
        "start", "stop", "status", "history", "schedule", "schedule-vps"
    ])
    parser.add_argument("--account-id", type=int, help="Account ID")
    parser.add_argument("--vps-id", type=int, help="VPS ID (1-5)")
    parser.add_argument("--collection-type", default="all", 
                       choices=["orders", "listings", "messages", "all"])
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--max-concurrent", type=int, default=10, 
                       help="Max concurrent global tasks")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    
    args = parser.parse_args()
    
    scheduler = ProfileScheduler(args.config, args.max_concurrent)
    
    if args.action == "start":
        scheduler.schedule_daily_collections()
        scheduler.start_scheduler()
        
        if args.daemon:
            logger.info("Running scheduler as daemon...")
            try:
                while scheduler.scheduler_running:
                    time.sleep(60)
            except KeyboardInterrupt:
                logger.info("Received interrupt signal")
        else:
            logger.info("Scheduler started. Press Ctrl+C to stop.")
            try:
                time.sleep(10)
                status = scheduler.get_status()
                print(f"Scheduler Status: {json.dumps(status, indent=2)}")
            except KeyboardInterrupt:
                pass
        
        scheduler.stop_scheduler()
    
    elif args.action == "stop":
        # This would need a way to communicate with running scheduler
        print("Stop command - would need IPC implementation")
    
    elif args.action == "status":
        # For demonstration - in real implementation would query running scheduler
        scheduler.schedule_daily_collections()
        status = scheduler.get_status()
        print(f"Scheduler Status: {json.dumps(status, indent=2)}")
    
    elif args.action == "history":
        history = scheduler.get_task_history(args.account_id)
        print(f"Task History ({len(history)} tasks):")
        for task in history[:10]:  # Show last 10
            print(f"  {task['task_id']}: {task['status']} - {task.get('completed_at', 'Not completed')}")
    
    elif args.action == "schedule":
        if args.account_id:
            task_ids = scheduler.schedule_immediate_collection(
                [args.account_id], args.collection_type
            )
        else:
            task_ids = scheduler.schedule_immediate_collection(
                collection_type=args.collection_type
            )
        
        print(f"Scheduled {len(task_ids)} tasks:")
        for task_id in task_ids:
            print(f"  {task_id}")
    
    elif args.action == "schedule-vps":
        if not args.vps_id:
            print("--vps-id required for schedule-vps action")
            return
        
        task_ids = scheduler.schedule_vps_collection(args.vps_id, args.collection_type)
        print(f"Scheduled {len(task_ids)} tasks for VPS_{args.vps_id}")

if __name__ == "__main__":
    main()