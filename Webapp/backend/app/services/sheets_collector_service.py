"""
Google Sheets Collector Service
Collects data FROM 30 Google Sheets (written by Chrome Extension)
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from app.core.config import settings
from app.db.database import SessionLocal
from app.models.database_models import Order, Listing, Message, AccountSheet

logger = logging.getLogger(__name__)


@dataclass
class SheetConfig:
    """Configuration for a single Google Sheet"""
    account_id: int
    ebay_username: str
    sheet_id: str
    sheet_name: str
    browser_profile: str
    vps_id: int
    last_sync_row: Dict[str, int]  # Track last read row for each sheet tab


class GoogleSheetsCollector:
    """
    Collects data FROM Google Sheets (written by Chrome Extension)
    Each eBay account has its own dedicated Google Sheet
    """
    
    def __init__(self):
        self.service = None
        self.credentials = None
        self.sheet_configs = self._initialize_sheet_configs()
        self.last_sync_times = {}
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Sheets API service"""
        try:
            # Load credentials from service account file
            credentials_path = settings.GOOGLE_SHEETS_CREDENTIALS_PATH
            self.credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets.readonly']
            )
            self.service = build('sheets', 'v4', credentials=self.credentials)
            logger.info("Google Sheets service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets service: {e}")
            self.service = None
    
    def _initialize_sheet_configs(self) -> Dict[int, SheetConfig]:
        """Initialize configuration for all 30 Google Sheets"""
        configs = {}
        
        # Sheet configurations for 30 eBay accounts
        sheet_mappings = {
            1: ("seller_prime_001", "1ABC_SHEET_ID_001", "Profile_001", 1),
            2: ("powerstore_002", "1DEF_SHEET_ID_002", "Profile_002", 1),
            3: ("megadeals_003", "1GHI_SHEET_ID_003", "Profile_003", 1),
            4: ("topbargains_004", "1JKL_SHEET_ID_004", "Profile_004", 1),
            5: ("quickseller_005", "1MNO_SHEET_ID_005", "Profile_005", 1),
            6: ("elitestore_006", "1PQR_SHEET_ID_006", "Profile_006", 1),
            # VPS 2
            7: ("smartseller_007", "1STU_SHEET_ID_007", "Profile_007", 2),
            8: ("fasttrack_008", "1VWX_SHEET_ID_008", "Profile_008", 2),
            9: ("prodealer_009", "1YZA_SHEET_ID_009", "Profile_009", 2),
            10: ("maxstore_010", "1BCD_SHEET_ID_010", "Profile_010", 2),
            11: ("superseller_011", "1EFG_SHEET_ID_011", "Profile_011", 2),
            12: ("topchoice_012", "1HIJ_SHEET_ID_012", "Profile_012", 2),
            # VPS 3
            13: ("golddeals_013", "1KLM_SHEET_ID_013", "Profile_013", 3),
            14: ("flexstore_014", "1NOP_SHEET_ID_014", "Profile_014", 3),
            15: ("powerstore_015", "1QRS_SHEET_ID_015", "Profile_015", 3),
            16: ("titandeals_016", "1TUV_SHEET_ID_016", "Profile_016", 3),
            17: ("megaseller_017", "1WXY_SHEET_ID_017", "Profile_017", 3),
            18: ("ultrapro_018", "1ZAB_SHEET_ID_018", "Profile_018", 3),
            # VPS 4
            19: ("premiumstore_019", "1CDE_SHEET_ID_019", "Profile_019", 4),
            20: ("lightning_020", "1FGH_SHEET_ID_020", "Profile_020", 4),
            21: ("diamondstore_021", "1IJK_SHEET_ID_021", "Profile_021", 4),
            22: ("protrader_022", "1LMN_SHEET_ID_022", "Profile_022", 4),
            23: ("speedseller_023", "1OPQ_SHEET_ID_023", "Profile_023", 4),
            24: ("elitepro_024", "1RST_SHEET_ID_024", "Profile_024", 4),
            # VPS 5
            25: ("maxpro_025", "1UVW_SHEET_ID_025", "Profile_025", 5),
            26: ("ultradeals_026", "1XYZ_SHEET_ID_026", "Profile_026", 5),
            27: ("toptrader_027", "1AAA_SHEET_ID_027", "Profile_027", 5),
            28: ("giantstore_028", "1BBB_SHEET_ID_028", "Profile_028", 5),
            29: ("kingdealer_029", "1CCC_SHEET_ID_029", "Profile_029", 5),
            30: ("supremestore_030", "1DDD_SHEET_ID_030", "Profile_030", 5),
        }
        
        for account_id, (username, sheet_id, profile, vps_id) in sheet_mappings.items():
            configs[account_id] = SheetConfig(
                account_id=account_id,
                ebay_username=username,
                sheet_id=sheet_id,
                sheet_name=f"eBay_Account_{account_id:03d}",
                browser_profile=profile,
                vps_id=vps_id,
                last_sync_row={"Orders": 1, "Listings": 1, "Messages": 1}  # Start from row 2 (after headers)
            )
        
        return configs
    
    async def collect_from_sheet(self, account_id: int) -> Dict[str, Any]:
        """
        Collect data from a specific Google Sheet
        
        Args:
            account_id: The account ID to collect data for
            
        Returns:
            Dictionary containing collected data and status
        """
        if not self.service:
            logger.error("Google Sheets service not initialized")
            return {"success": False, "error": "Service not initialized"}
        
        config = self.sheet_configs.get(account_id)
        if not config:
            logger.error(f"No configuration found for account {account_id}")
            return {"success": False, "error": "Account not configured"}
        
        results = {
            "account_id": account_id,
            "username": config.ebay_username,
            "orders": [],
            "listings": [],
            "messages": [],
            "errors": []
        }
        
        try:
            # Collect Orders
            orders_data = await self._read_sheet_data(
                config.sheet_id, 
                "Orders", 
                config.last_sync_row["Orders"]
            )
            if orders_data:
                results["orders"] = self._parse_orders(orders_data)
                config.last_sync_row["Orders"] += len(orders_data)
            
            # Collect Listings
            listings_data = await self._read_sheet_data(
                config.sheet_id,
                "Listings",
                config.last_sync_row["Listings"]
            )
            if listings_data:
                results["listings"] = self._parse_listings(listings_data)
                config.last_sync_row["Listings"] += len(listings_data)
            
            # Collect Messages
            messages_data = await self._read_sheet_data(
                config.sheet_id,
                "Messages", 
                config.last_sync_row["Messages"]
            )
            if messages_data:
                results["messages"] = self._parse_messages(messages_data)
                config.last_sync_row["Messages"] += len(messages_data)
            
            logger.info(f"Collected from account {account_id}: "
                       f"{len(results['orders'])} orders, "
                       f"{len(results['listings'])} listings, "
                       f"{len(results['messages'])} messages")
            
            return results
            
        except Exception as e:
            logger.error(f"Error collecting from sheet {account_id}: {e}")
            results["errors"].append(str(e))
            return results
    
    async def _read_sheet_data(self, sheet_id: str, tab_name: str, start_row: int) -> List[List[Any]]:
        """
        Read new data from a specific sheet tab
        
        Args:
            sheet_id: Google Sheet ID
            tab_name: Tab name (Orders, Listings, Messages)
            start_row: Row to start reading from
            
        Returns:
            List of rows (each row is a list of values)
        """
        try:
            # Read from start_row to end of sheet
            range_name = f"{tab_name}!A{start_row + 1}:Z"
            
            result = self.service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            
            if values:
                logger.info(f"Read {len(values)} new rows from {tab_name}")
                return values
            else:
                logger.debug(f"No new data in {tab_name} from row {start_row + 1}")
                return []
                
        except HttpError as e:
            if e.resp.status == 404:
                logger.warning(f"Sheet or tab not found: {sheet_id}/{tab_name}")
            else:
                logger.error(f"Error reading sheet: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error reading sheet: {e}")
            return []
    
    def _parse_orders(self, rows: List[List[Any]]) -> List[Dict]:
        """Parse order data from sheet rows"""
        orders = []
        for row in rows:
            try:
                # Expected columns: Timestamp, Order ID, Buyer, Total, Status, Items, 
                # Ship Address, Tracking, Ship Date, Order Date, Payment Status
                if len(row) >= 11:
                    order = {
                        "timestamp": row[0],
                        "order_id": row[1],
                        "buyer": row[2],
                        "total": row[3],
                        "status": row[4],
                        "items": json.loads(row[5]) if row[5] else [],
                        "ship_address": row[6],
                        "tracking": row[7],
                        "ship_date": row[8],
                        "order_date": row[9],
                        "payment_status": row[10]
                    }
                    orders.append(order)
            except Exception as e:
                logger.warning(f"Error parsing order row: {e}")
                continue
        
        return orders
    
    def _parse_listings(self, rows: List[List[Any]]) -> List[Dict]:
        """Parse listing data from sheet rows"""
        listings = []
        for row in rows:
            try:
                # Expected columns: Timestamp, Item ID, Title, Price, Quantity, 
                # Quantity Sold, Views, Watchers, Status, Category, Condition, Start Date, End Date
                if len(row) >= 13:
                    listing = {
                        "timestamp": row[0],
                        "item_id": row[1],
                        "title": row[2],
                        "price": row[3],
                        "quantity": int(row[4]) if row[4] else 0,
                        "quantity_sold": int(row[5]) if row[5] else 0,
                        "views": int(row[6]) if row[6] else 0,
                        "watchers": int(row[7]) if row[7] else 0,
                        "status": row[8],
                        "category": row[9],
                        "condition": row[10],
                        "start_date": row[11],
                        "end_date": row[12]
                    }
                    listings.append(listing)
            except Exception as e:
                logger.warning(f"Error parsing listing row: {e}")
                continue
        
        return listings
    
    def _parse_messages(self, rows: List[List[Any]]) -> List[Dict]:
        """Parse message data from sheet rows"""
        messages = []
        for row in rows:
            try:
                # Expected columns: Timestamp, Sender, Subject, Content, Message Date,
                # Read Status, Message Type, Related Item ID, Related Order ID, Priority
                if len(row) >= 10:
                    message = {
                        "timestamp": row[0],
                        "sender": row[1],
                        "subject": row[2],
                        "content": row[3],
                        "message_date": row[4],
                        "read_status": row[5],
                        "message_type": row[6],
                        "related_item_id": row[7],
                        "related_order_id": row[8],
                        "priority": row[9]
                    }
                    messages.append(message)
            except Exception as e:
                logger.warning(f"Error parsing message row: {e}")
                continue
        
        return messages
    
    async def collect_all_accounts(self, concurrent_limit: int = 10) -> Dict[str, Any]:
        """
        Collect data from all 30 Google Sheets concurrently
        
        Args:
            concurrent_limit: Maximum number of concurrent sheet reads
            
        Returns:
            Summary of collection results
        """
        logger.info(f"Starting collection from all 30 accounts (concurrent limit: {concurrent_limit})")
        
        start_time = datetime.now()
        all_results = []
        errors = []
        
        # Create semaphore for concurrent limit
        semaphore = asyncio.Semaphore(concurrent_limit)
        
        async def collect_with_limit(account_id):
            async with semaphore:
                return await self.collect_from_sheet(account_id)
        
        # Collect from all accounts concurrently
        tasks = [collect_with_limit(account_id) for account_id in range(1, 31)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        total_orders = 0
        total_listings = 0
        total_messages = 0
        successful_accounts = 0
        
        for i, result in enumerate(results, 1):
            if isinstance(result, Exception):
                errors.append(f"Account {i}: {str(result)}")
            elif isinstance(result, dict):
                if result.get("orders") or result.get("listings") or result.get("messages"):
                    successful_accounts += 1
                    total_orders += len(result.get("orders", []))
                    total_listings += len(result.get("listings", []))
                    total_messages += len(result.get("messages", []))
                    
                    # Save to database
                    await self._save_to_database(result)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        summary = {
            "collection_time": datetime.now().isoformat(),
            "duration_seconds": duration,
            "total_accounts": 30,
            "successful_accounts": successful_accounts,
            "total_orders": total_orders,
            "total_listings": total_listings,
            "total_messages": total_messages,
            "errors": errors
        }
        
        logger.info(f"Collection completed in {duration:.2f} seconds. "
                   f"Success: {successful_accounts}/30 accounts")
        
        return summary
    
    async def _save_to_database(self, data: Dict[str, Any]):
        """Save collected data to database"""
        db = SessionLocal()
        try:
            account_id = data.get("account_id")
            
            # Save orders
            for order_data in data.get("orders", []):
                # Check if order already exists
                existing = db.query(Order).filter_by(
                    order_id=order_data["order_id"]
                ).first()
                
                if not existing:
                    order = Order(
                        order_id=order_data["order_id"],
                        buyer=order_data["buyer"],
                        total=order_data["total"],
                        status=order_data["status"],
                        ship_address=order_data.get("ship_address"),
                        tracking=order_data.get("tracking"),
                        ship_date=order_data.get("ship_date"),
                        order_date=order_data.get("order_date"),
                        payment_status=order_data.get("payment_status"),
                        account_id=account_id
                    )
                    db.add(order)
            
            # Save listings
            for listing_data in data.get("listings", []):
                existing = db.query(Listing).filter_by(
                    item_id=listing_data["item_id"]
                ).first()
                
                if not existing:
                    listing = Listing(
                        item_id=listing_data["item_id"],
                        title=listing_data["title"],
                        price=listing_data["price"],
                        quantity=listing_data.get("quantity", 0),
                        status=listing_data.get("status"),
                        category=listing_data.get("category"),
                        condition=listing_data.get("condition"),
                        account_id=account_id
                    )
                    db.add(listing)
                else:
                    # Update existing listing
                    existing.quantity = listing_data.get("quantity", 0)
                    existing.status = listing_data.get("status")
                    existing.price = listing_data["price"]
            
            # Save messages
            for message_data in data.get("messages", []):
                message = Message(
                    sender=message_data["sender"],
                    subject=message_data["subject"],
                    content=message_data.get("content"),
                    message_date=message_data.get("message_date"),
                    read_status=message_data.get("read_status"),
                    message_type=message_data.get("message_type"),
                    account_id=account_id
                )
                db.add(message)
            
            db.commit()
            logger.info(f"Saved data for account {account_id} to database")
            
        except Exception as e:
            logger.error(f"Error saving to database: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def schedule_periodic_collection(self, interval_minutes: int = 300):
        """
        Schedule periodic collection from all sheets
        
        Args:
            interval_minutes: Collection interval in minutes (default 5 hours)
        """
        logger.info(f"Starting periodic collection every {interval_minutes} minutes")
        
        while True:
            try:
                # Collect from all accounts
                summary = await self.collect_all_accounts()
                
                # Log summary
                logger.info(f"Periodic collection completed: {summary}")
                
                # Update last sync times
                for account_id in range(1, 31):
                    self.last_sync_times[account_id] = datetime.now()
                
                # Wait for next collection
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Error in periodic collection: {e}")
                # Wait 1 minute before retrying
                await asyncio.sleep(60)


# Singleton instance
sheets_collector = GoogleSheetsCollector()


async def start_sheets_collection():
    """Start the sheets collection service"""
    await sheets_collector.schedule_periodic_collection(interval_minutes=300)