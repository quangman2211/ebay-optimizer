#!/usr/bin/env python3
"""
Browser Profile Management Script
Manages 30 eBay browser profiles across 5 VPS servers
"""

import json
import asyncio
import logging
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import argparse

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BrowserProfileManager:
    """Manages browser profiles for eBay automation"""
    
    def __init__(self, config_path: str = None):
        if not config_path:
            config_path = Path(__file__).parent.parent / "config" / "browser_profiles_config.json"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.profiles = self.config.get("browser_profiles", {})
        self.vps_distribution = self.config.get("vps_distribution", {})
        
    def _load_config(self) -> Dict:
        """Load browser profiles configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {self.config_path}")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            return {}
    
    def list_profiles(self, vps_id: int = None) -> List[Dict]:
        """List browser profiles, optionally filtered by VPS"""
        profiles = []
        
        for account_id, profile_config in self.profiles.items():
            if vps_id and profile_config.get("vps_server") != f"VPS_{vps_id}":
                continue
                
            profiles.append({
                "account_id": int(account_id),
                "username": profile_config.get("ebay_username"),
                "profile_name": profile_config.get("profile_name"),
                "browser_type": profile_config.get("browser_type"),
                "vps_server": profile_config.get("vps_server"),
                "proxy_location": profile_config.get("proxy_config", {}).get("location"),
                "os": profile_config.get("fingerprint_config", {}).get("os")
            })
        
        return sorted(profiles, key=lambda x: x["account_id"])
    
    def get_profile(self, account_id: int) -> Optional[Dict]:
        """Get specific profile configuration"""
        return self.profiles.get(str(account_id))
    
    def get_vps_profiles(self, vps_id: int) -> List[Dict]:
        """Get all profiles for a specific VPS"""
        vps_key = f"VPS_{vps_id}"
        vps_config = self.vps_distribution.get(vps_key, {})
        account_ids = vps_config.get("accounts", [])
        
        profiles = []
        for account_id in account_ids:
            profile = self.get_profile(account_id)
            if profile:
                profiles.append(profile)
        
        return profiles
    
    def start_profile(self, account_id: int, headless: bool = False) -> bool:
        """Start a specific browser profile"""
        profile_config = self.get_profile(account_id)
        if not profile_config:
            logger.error(f"Profile {account_id} not found")
            return False
        
        try:
            browser_type = profile_config.get("browser_type")
            profile_id = profile_config.get("profile_id")
            
            if browser_type == "hidemyacc":
                return self._start_hidemyacc_profile(profile_id, headless)
            elif browser_type == "multilogin":
                return self._start_multilogin_profile(profile_id, headless)
            else:
                logger.error(f"Unsupported browser type: {browser_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error starting profile {account_id}: {e}")
            return False
    
    def _start_hidemyacc_profile(self, profile_id: str, headless: bool = False) -> bool:
        """Start HideMyAcc browser profile"""
        try:
            cmd = [
                "hidemyacc-cli",
                "start",
                "--profile", profile_id,
                "--wait-until-loaded"
            ]
            
            if headless:
                cmd.append("--headless")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                logger.info(f"HideMyAcc profile {profile_id} started successfully")
                return True
            else:
                logger.error(f"Failed to start HideMyAcc profile {profile_id}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout starting HideMyAcc profile {profile_id}")
            return False
        except FileNotFoundError:
            logger.error("HideMyAcc CLI not found. Please install HideMyAcc.")
            return False
    
    def _start_multilogin_profile(self, profile_id: str, headless: bool = False) -> bool:
        """Start Multilogin browser profile"""
        try:
            # Multilogin API endpoint
            api_url = "https://launcher.mlx.yt:45001/api/v1/profile/start"
            
            import requests
            
            payload = {
                "uuid": profile_id,
                "headless": headless
            }
            
            response = requests.post(api_url, json=payload, timeout=60)
            
            if response.status_code == 200:
                logger.info(f"Multilogin profile {profile_id} started successfully")
                return True
            else:
                logger.error(f"Failed to start Multilogin profile {profile_id}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to Multilogin API: {e}")
            return False
        except ImportError:
            logger.error("requests library not found. Please install: pip install requests")
            return False
    
    def stop_profile(self, account_id: int) -> bool:
        """Stop a specific browser profile"""
        profile_config = self.get_profile(account_id)
        if not profile_config:
            logger.error(f"Profile {account_id} not found")
            return False
        
        try:
            browser_type = profile_config.get("browser_type")
            profile_id = profile_config.get("profile_id")
            
            if browser_type == "hidemyacc":
                return self._stop_hidemyacc_profile(profile_id)
            elif browser_type == "multilogin":
                return self._stop_multilogin_profile(profile_id)
            else:
                logger.error(f"Unsupported browser type: {browser_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error stopping profile {account_id}: {e}")
            return False
    
    def _stop_hidemyacc_profile(self, profile_id: str) -> bool:
        """Stop HideMyAcc browser profile"""
        try:
            cmd = ["hidemyacc-cli", "stop", "--profile", profile_id]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                logger.info(f"HideMyAcc profile {profile_id} stopped successfully")
                return True
            else:
                logger.error(f"Failed to stop HideMyAcc profile {profile_id}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout stopping HideMyAcc profile {profile_id}")
            return False
        except FileNotFoundError:
            logger.error("HideMyAcc CLI not found")
            return False
    
    def _stop_multilogin_profile(self, profile_id: str) -> bool:
        """Stop Multilogin browser profile"""
        try:
            import requests
            
            api_url = "https://launcher.mlx.yt:45001/api/v1/profile/stop"
            payload = {"uuid": profile_id}
            
            response = requests.post(api_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Multilogin profile {profile_id} stopped successfully")
                return True
            else:
                logger.error(f"Failed to stop Multilogin profile {profile_id}: {response.text}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to Multilogin API: {e}")
            return False
    
    def start_vps_profiles(self, vps_id: int, max_concurrent: int = None) -> Dict[str, bool]:
        """Start all profiles for a specific VPS"""
        profiles = self.get_vps_profiles(vps_id)
        
        if max_concurrent is None:
            vps_config = self.vps_distribution.get(f"VPS_{vps_id}", {})
            max_concurrent = vps_config.get("max_concurrent_profiles", 6)
        
        results = {}
        started_count = 0
        
        for profile in profiles:
            if started_count >= max_concurrent:
                logger.warning(f"Reached concurrent limit ({max_concurrent}) for VPS_{vps_id}")
                break
            
            account_id = profile.get("account_id")
            success = self.start_profile(account_id)
            results[f"account_{account_id}"] = success
            
            if success:
                started_count += 1
        
        logger.info(f"Started {started_count}/{len(profiles)} profiles for VPS_{vps_id}")
        return results
    
    def stop_vps_profiles(self, vps_id: int) -> Dict[str, bool]:
        """Stop all profiles for a specific VPS"""
        profiles = self.get_vps_profiles(vps_id)
        results = {}
        
        for profile in profiles:
            account_id = profile.get("account_id")
            success = self.stop_profile(account_id)
            results[f"account_{account_id}"] = success
        
        return results
    
    def get_profile_status(self, account_id: int) -> Dict:
        """Get status of a specific profile"""
        profile_config = self.get_profile(account_id)
        if not profile_config:
            return {"error": f"Profile {account_id} not found"}
        
        # This would need to be implemented based on browser APIs
        # For now, return basic info
        return {
            "account_id": account_id,
            "username": profile_config.get("ebay_username"),
            "profile_name": profile_config.get("profile_name"),
            "browser_type": profile_config.get("browser_type"),
            "vps_server": profile_config.get("vps_server"),
            "status": "unknown",  # Would need API call to determine
            "last_checked": datetime.now().isoformat()
        }
    
    def export_config_for_vps(self, vps_id: int, output_path: str = None) -> str:
        """Export configuration for a specific VPS"""
        profiles = self.get_vps_profiles(vps_id)
        vps_config = self.vps_distribution.get(f"VPS_{vps_id}", {})
        
        export_data = {
            "vps_id": vps_id,
            "vps_config": vps_config,
            "profiles": profiles,
            "export_timestamp": datetime.now().isoformat()
        }
        
        if not output_path:
            output_path = f"/tmp/vps_{vps_id}_config.json"
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        logger.info(f"VPS_{vps_id} configuration exported to {output_path}")
        return output_path

def main():
    parser = argparse.ArgumentParser(description="Browser Profile Manager")
    parser.add_argument("action", choices=[
        "list", "start", "stop", "status", "start-vps", "stop-vps", "export"
    ])
    parser.add_argument("--account-id", type=int, help="Account ID")
    parser.add_argument("--vps-id", type=int, help="VPS ID (1-5)")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    parser.add_argument("--max-concurrent", type=int, help="Max concurrent profiles for VPS")
    parser.add_argument("--config", help="Path to configuration file")
    
    args = parser.parse_args()
    
    manager = BrowserProfileManager(args.config)
    
    if args.action == "list":
        profiles = manager.list_profiles(args.vps_id)
        print(f"\nFound {len(profiles)} profiles:")
        print("-" * 80)
        for profile in profiles:
            print(f"ID: {profile['account_id']:2d} | "
                  f"{profile['username']:18s} | "
                  f"{profile['browser_type']:10s} | "
                  f"{profile['vps_server']:5s} | "
                  f"{profile['proxy_location']}")
    
    elif args.action == "start":
        if not args.account_id:
            print("--account-id required for start action")
            sys.exit(1)
        
        success = manager.start_profile(args.account_id, args.headless)
        if success:
            print(f"Profile {args.account_id} started successfully")
        else:
            print(f"Failed to start profile {args.account_id}")
            sys.exit(1)
    
    elif args.action == "stop":
        if not args.account_id:
            print("--account-id required for stop action")
            sys.exit(1)
        
        success = manager.stop_profile(args.account_id)
        if success:
            print(f"Profile {args.account_id} stopped successfully")
        else:
            print(f"Failed to stop profile {args.account_id}")
            sys.exit(1)
    
    elif args.action == "status":
        if not args.account_id:
            print("--account-id required for status action")
            sys.exit(1)
        
        status = manager.get_profile_status(args.account_id)
        print(f"Profile Status: {json.dumps(status, indent=2)}")
    
    elif args.action == "start-vps":
        if not args.vps_id:
            print("--vps-id required for start-vps action")
            sys.exit(1)
        
        results = manager.start_vps_profiles(args.vps_id, args.max_concurrent)
        print(f"VPS_{args.vps_id} start results:")
        for profile, success in results.items():
            status = "✓" if success else "✗"
            print(f"  {status} {profile}")
    
    elif args.action == "stop-vps":
        if not args.vps_id:
            print("--vps-id required for stop-vps action")
            sys.exit(1)
        
        results = manager.stop_vps_profiles(args.vps_id)
        print(f"VPS_{args.vps_id} stop results:")
        for profile, success in results.items():
            status = "✓" if success else "✗"
            print(f"  {status} {profile}")
    
    elif args.action == "export":
        if not args.vps_id:
            print("--vps-id required for export action")
            sys.exit(1)
        
        output_path = manager.export_config_for_vps(args.vps_id)
        print(f"Configuration exported to {output_path}")

if __name__ == "__main__":
    main()