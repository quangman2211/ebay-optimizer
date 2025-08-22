"""
3-Tier Google Sheets Management System
Following SOLID principles for multi-account eBay management

Architecture:
- Tầng 1: Master Dashboard (Admin oversight)
- Tầng 2: Account Sheets (eBay Manager per account)  
- Tầng 3: Staff Workflow Sheets (Fulfillment Staff individual)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

from app.services.interfaces import IDataReader, IDataWriter
from app.services.google_sheets import GoogleSheetsService
from app.models.database_models import User, Account, Order, SheetsSyncLog
from app.core.rbac import RBACService, Permission

logger = logging.getLogger(__name__)


class SheetTier(str, Enum):
    """Sheet hierarchy levels"""
    MASTER = "master"       # Admin level - tổng quan toàn bộ
    ACCOUNT = "account"     # eBay Manager level - per account
    STAFF = "staff"         # Fulfillment Staff level - per user


class SheetType(str, Enum):
    """Types of operations in sheets"""
    ORDERS_IMPORT = "orders_import"
    ORDERS_PROCESSING = "orders_processing"
    TRACKING_EXPORT = "tracking_export"
    PERFORMANCE_REPORT = "performance_report"
    BLACKLIST_CHECK = "blacklist_check"
    STAFF_WORKLOAD = "staff_workload"


@dataclass
class SheetConfig:
    """Configuration for a specific sheet"""
    spreadsheet_id: str
    sheet_name: str
    tier: SheetTier
    sheet_type: SheetType
    account_id: Optional[int] = None
    user_id: Optional[int] = None
    auto_sync: bool = True
    sync_interval_minutes: int = 15
    permissions: List[str] = None


class ISheetTemplate(ABC):
    """Interface for sheet templates - Single Responsibility"""
    
    @abstractmethod
    def get_headers(self) -> List[str]:
        """Get column headers for this sheet type"""
        pass
    
    @abstractmethod
    def transform_data(self, data: List[Dict]) -> List[Dict]:
        """Transform data to sheet format"""
        pass
    
    @abstractmethod
    def validate_data(self, data: List[Dict]) -> tuple[bool, List[str]]:
        """Validate data before writing to sheet"""
        pass


class MasterDashboardTemplate(ISheetTemplate):
    """Master Dashboard template - Admin overview"""
    
    def get_headers(self) -> List[str]:
        return [
            "Account_ID", "Account_Name", "Total_Orders", "Pending_Orders",
            "Processing_Orders", "Shipped_Orders", "Revenue_Today", 
            "Revenue_Week", "Revenue_Month", "Staff_Assigned", "Last_Update",
            "Sync_Status", "Blacklist_Flags", "Performance_Score"
        ]
    
    def transform_data(self, accounts_data: List[Dict]) -> List[Dict]:
        """Transform account data for master dashboard"""
        transformed = []
        for account in accounts_data:
            transformed.append({
                "Account_ID": account.get("id", ""),
                "Account_Name": account.get("name", ""),
                "Total_Orders": account.get("total_orders", 0),
                "Pending_Orders": account.get("pending_orders", 0),
                "Processing_Orders": account.get("processing_orders", 0),
                "Shipped_Orders": account.get("shipped_orders", 0),
                "Revenue_Today": account.get("revenue_today", 0),
                "Revenue_Week": account.get("revenue_week", 0),
                "Revenue_Month": account.get("revenue_month", 0),
                "Staff_Assigned": account.get("staff_count", 0),
                "Last_Update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Sync_Status": account.get("sync_status", "Unknown"),
                "Blacklist_Flags": account.get("blacklist_flags", 0),
                "Performance_Score": account.get("performance_score", 0)
            })
        return transformed
    
    def validate_data(self, data: List[Dict]) -> tuple[bool, List[str]]:
        """Validate master dashboard data"""
        errors = []
        for i, row in enumerate(data):
            if not row.get("Account_ID"):
                errors.append(f"Row {i+1}: Missing Account_ID")
            if not isinstance(row.get("Total_Orders", 0), (int, float)):
                errors.append(f"Row {i+1}: Invalid Total_Orders format")
        return len(errors) == 0, errors


class AccountSheetTemplate(ISheetTemplate):
    """Account Sheet template - eBay Manager per account"""
    
    def get_headers(self) -> List[str]:
        return [
            "Order_ID", "eBay_Order_ID", "Customer_Name", "Customer_Email",
            "Customer_Phone", "Shipping_Address", "Product_Title", "Quantity",
            "Price", "Order_Date", "Status", "Assigned_To", "Assigned_Date",
            "Blacklist_Status", "Blacklist_Reason", "Tracking_Number",
            "Carrier", "Ship_Date", "Supplier", "Notes", "Last_Update"
        ]
    
    def transform_data(self, orders_data: List[Dict]) -> List[Dict]:
        """Transform orders for account sheet"""
        transformed = []
        for order in orders_data:
            transformed.append({
                "Order_ID": order.get("id", ""),
                "eBay_Order_ID": order.get("ebay_order_id", ""),
                "Customer_Name": order.get("customer_name", ""),
                "Customer_Email": order.get("customer_email", ""),
                "Customer_Phone": order.get("customer_phone", ""),
                "Shipping_Address": order.get("shipping_address", ""),
                "Product_Title": order.get("product_title", ""),
                "Quantity": order.get("quantity", 1),
                "Price": order.get("price_ebay", 0),
                "Order_Date": order.get("order_date", ""),
                "Status": order.get("status", "pending"),
                "Assigned_To": order.get("assigned_to_user_name", ""),
                "Assigned_Date": order.get("assignment_date", ""),
                "Blacklist_Status": order.get("blacklist_status", "pending"),
                "Blacklist_Reason": order.get("blacklist_reason", ""),
                "Tracking_Number": order.get("tracking_number", ""),
                "Carrier": order.get("carrier", ""),
                "Ship_Date": order.get("actual_ship_date", ""),
                "Supplier": order.get("supplier_name", ""),
                "Notes": order.get("fulfillment_notes", ""),
                "Last_Update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        return transformed
    
    def validate_data(self, data: List[Dict]) -> tuple[bool, List[str]]:
        """Validate account sheet data"""
        errors = []
        for i, row in enumerate(data):
            if not row.get("Order_ID"):
                errors.append(f"Row {i+1}: Missing Order_ID")
            if not row.get("Customer_Email"):
                errors.append(f"Row {i+1}: Missing Customer_Email")
        return len(errors) == 0, errors


class StaffWorkflowTemplate(ISheetTemplate):
    """Staff Workflow template - Individual fulfillment staff"""
    
    def get_headers(self) -> List[str]:
        return [
            "Order_ID", "eBay_Order_ID", "Customer_Name", "Product_Title",
            "Quantity", "Order_Date", "Status", "Priority", "Supplier_Contact",
            "Supplier_Response", "Tracking_Number", "Carrier", "Ship_Date",
            "Customer_Notes", "Internal_Notes", "Completion_Date", "Last_Update"
        ]
    
    def transform_data(self, orders_data: List[Dict]) -> List[Dict]:
        """Transform orders for staff workflow"""
        transformed = []
        for order in orders_data:
            # Calculate priority based on order age and status
            order_date = order.get("order_date")
            priority = self._calculate_priority(order_date, order.get("status"))
            
            transformed.append({
                "Order_ID": order.get("id", ""),
                "eBay_Order_ID": order.get("ebay_order_id", ""),
                "Customer_Name": order.get("customer_name", ""),
                "Product_Title": order.get("product_title", ""),
                "Quantity": order.get("quantity", 1),
                "Order_Date": order_date,
                "Status": order.get("status", "pending"),
                "Priority": priority,
                "Supplier_Contact": order.get("supplier_name", ""),
                "Supplier_Response": "",  # To be filled by staff
                "Tracking_Number": order.get("tracking_number", ""),
                "Carrier": order.get("carrier", ""),
                "Ship_Date": order.get("actual_ship_date", ""),
                "Customer_Notes": order.get("notes", ""),
                "Internal_Notes": order.get("fulfillment_notes", ""),
                "Completion_Date": "",  # To be filled when completed
                "Last_Update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        return transformed
    
    def validate_data(self, data: List[Dict]) -> tuple[bool, List[str]]:
        """Validate staff workflow data"""
        errors = []
        for i, row in enumerate(data):
            if not row.get("Order_ID"):
                errors.append(f"Row {i+1}: Missing Order_ID")
            status = row.get("Status", "").lower()
            if status not in ["pending", "processing", "shipped", "completed"]:
                errors.append(f"Row {i+1}: Invalid status '{status}'")
        return len(errors) == 0, errors
    
    def _calculate_priority(self, order_date: str, status: str) -> str:
        """Calculate order priority based on age and status"""
        if not order_date:
            return "Medium"
        
        try:
            order_dt = datetime.fromisoformat(order_date.replace('Z', '+00:00'))
            age_days = (datetime.now() - order_dt).days
            
            if status in ["pending", "processing"]:
                if age_days >= 3:
                    return "High"
                elif age_days >= 1:
                    return "Medium"
                else:
                    return "Low"
            else:
                return "Low"
        except:
            return "Medium"


class SheetTemplateFactory:
    """Factory for creating sheet templates - Factory Pattern"""
    
    @staticmethod
    def create_template(sheet_type: SheetType) -> ISheetTemplate:
        """Create appropriate template based on sheet type"""
        if sheet_type == SheetType.PERFORMANCE_REPORT:
            return MasterDashboardTemplate()
        elif sheet_type in [SheetType.ORDERS_IMPORT, SheetType.ORDERS_PROCESSING]:
            return AccountSheetTemplate()
        elif sheet_type == SheetType.TRACKING_EXPORT:
            return StaffWorkflowTemplate()
        else:
            raise ValueError(f"Unknown sheet type: {sheet_type}")


class SheetManager:
    """Manages individual sheet operations - Single Responsibility"""
    
    def __init__(self, config: SheetConfig, sheets_service: GoogleSheetsService):
        self.config = config
        self.sheets_service = sheets_service
        self.template = SheetTemplateFactory.create_template(config.sheet_type)
    
    async def initialize_sheet(self) -> bool:
        """Initialize sheet with proper headers"""
        try:
            headers = self.template.get_headers()
            header_data = [dict(zip(headers, headers))]  # Header row
            
            spreadsheet_config = {
                "spreadsheet_id": self.config.spreadsheet_id,
                "sheet_name": self.config.sheet_name,
                "range": "A1:Z1"
            }
            
            success = await self.sheets_service.writer.write_data(
                f"{self.config.spreadsheet_id}!{self.config.sheet_name}!A1:Z1",
                header_data
            )
            
            if success:
                logger.info(f"Initialized sheet: {self.config.sheet_name}")
            return success
            
        except Exception as e:
            logger.error(f"Failed to initialize sheet {self.config.sheet_name}: {e}")
            return False
    
    async def sync_data(self, data: List[Dict]) -> Dict[str, Any]:
        """Sync data to sheet"""
        try:
            # Transform and validate data
            transformed_data = self.template.transform_data(data)
            is_valid, errors = self.template.validate_data(transformed_data)
            
            if not is_valid:
                return {
                    "success": False,
                    "errors": errors,
                    "rows_processed": 0
                }
            
            # Write to sheet
            spreadsheet_config = {
                "spreadsheet_id": self.config.spreadsheet_id,
                "sheet_name": self.config.sheet_name,
                "range": f"A2:Z{len(transformed_data)+1}"  # Skip header row
            }
            
            success = await self.sheets_service.writer.write_data(
                f"{self.config.spreadsheet_id}!{self.config.sheet_name}!A2:Z{len(transformed_data)+1}",
                transformed_data
            )
            
            return {
                "success": success,
                "errors": [],
                "rows_processed": len(transformed_data) if success else 0,
                "last_sync": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to sync data to {self.config.sheet_name}: {e}")
            return {
                "success": False,
                "errors": [str(e)],
                "rows_processed": 0
            }
    
    async def read_updates(self) -> List[Dict]:
        """Read updates from sheet"""
        try:
            source_id = f"{self.config.spreadsheet_id}!{self.config.sheet_name}!A1:Z1000"
            return await self.sheets_service.reader.read_data(source_id)
        except Exception as e:
            logger.error(f"Failed to read updates from {self.config.sheet_name}: {e}")
            return []


class MultiTierSheetsManager:
    """Manages the 3-tier sheet system - Facade Pattern"""
    
    def __init__(self, sheets_service: GoogleSheetsService, rbac_service: RBACService):
        self.sheets_service = sheets_service
        self.rbac_service = rbac_service
        self.sheet_managers: Dict[str, SheetManager] = {}
    
    def register_sheet(self, config: SheetConfig) -> str:
        """Register a new sheet configuration"""
        sheet_key = f"{config.tier}_{config.sheet_type}_{config.account_id or config.user_id or 'master'}"
        manager = SheetManager(config, self.sheets_service)
        self.sheet_managers[sheet_key] = manager
        return sheet_key
    
    async def sync_master_dashboard(self, accounts_data: List[Dict]) -> Dict[str, Any]:
        """Sync master dashboard with account overview"""
        master_key = f"{SheetTier.MASTER}_{SheetType.PERFORMANCE_REPORT}_master"
        if master_key not in self.sheet_managers:
            raise ValueError("Master dashboard not configured")
        
        return await self.sheet_managers[master_key].sync_data(accounts_data)
    
    async def sync_account_sheet(self, account_id: int, orders_data: List[Dict]) -> Dict[str, Any]:
        """Sync specific account sheet with orders"""
        account_key = f"{SheetTier.ACCOUNT}_{SheetType.ORDERS_IMPORT}_{account_id}"
        if account_key not in self.sheet_managers:
            raise ValueError(f"Account sheet for account {account_id} not configured")
        
        return await self.sheet_managers[account_key].sync_data(orders_data)
    
    async def sync_staff_workflow(self, user_id: int, assigned_orders: List[Dict]) -> Dict[str, Any]:
        """Sync staff workflow sheet with assigned orders"""
        staff_key = f"{SheetTier.STAFF}_{SheetType.TRACKING_EXPORT}_{user_id}"
        if staff_key not in self.sheet_managers:
            raise ValueError(f"Staff workflow for user {user_id} not configured")
        
        return await self.sheet_managers[staff_key].sync_data(assigned_orders)
    
    async def sync_all_tiers(self, sync_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Sync all three tiers in the correct order"""
        results = {}
        
        try:
            # 1. Sync staff workflows first (detailed level)
            if "staff_workflows" in sync_data:
                for user_id, orders in sync_data["staff_workflows"].items():
                    result = await self.sync_staff_workflow(int(user_id), orders)
                    results[f"staff_{user_id}"] = result
            
            # 2. Sync account sheets (aggregated level)
            if "account_sheets" in sync_data:
                for account_id, orders in sync_data["account_sheets"].items():
                    result = await self.sync_account_sheet(int(account_id), orders)
                    results[f"account_{account_id}"] = result
            
            # 3. Sync master dashboard last (summary level)
            if "master_dashboard" in sync_data:
                result = await self.sync_master_dashboard(sync_data["master_dashboard"])
                results["master_dashboard"] = result
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to sync all tiers: {e}")
            results["error"] = str(e)
            return results
    
    def get_sheet_permissions(self, user: Any, sheet_tier: SheetTier) -> List[str]:
        """Get permissions for user based on sheet tier"""
        user_permissions = self.rbac_service.get_user_permissions(user)
        
        tier_permissions = {
            SheetTier.MASTER: [Permission.ADMIN_USERS],
            SheetTier.ACCOUNT: [Permission.ORDERS_IMPORT, Permission.ORDERS_ASSIGN],
            SheetTier.STAFF: [Permission.ORDERS_PROCESS, Permission.ORDERS_SUPPLIER]
        }
        
        allowed_permissions = []
        for perm in tier_permissions.get(sheet_tier, []):
            if perm.value in user_permissions:
                allowed_permissions.append(perm.value)
        
        return allowed_permissions