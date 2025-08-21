"""
Account Sheet Repository
Handles database operations for account_sheets table
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from app.repositories.base import BaseRepository
from app.models.database_models import AccountSheet, Account
from datetime import datetime, timedelta


class AccountSheetRepository(BaseRepository[AccountSheet]):
    """Repository for AccountSheet operations"""
    
    def __init__(self, db: Session):
        super().__init__(AccountSheet, db)
    
    def get_by_account_id(self, account_id: int) -> List[AccountSheet]:
        """Get all sheets for an account"""
        return (
            self.db.query(AccountSheet)
            .filter(AccountSheet.account_id == account_id)
            .order_by(asc(AccountSheet.sheet_type))
            .all()
        )
    
    def get_by_account_and_type(self, account_id: int, sheet_type: str) -> Optional[AccountSheet]:
        """Get specific sheet type for an account"""
        return (
            self.db.query(AccountSheet)
            .filter(
                and_(
                    AccountSheet.account_id == account_id,
                    AccountSheet.sheet_type == sheet_type
                )
            )
            .first()
        )
    
    def get_by_sheet_id(self, sheet_id: str) -> Optional[AccountSheet]:
        """Get sheet by Google Sheet ID"""
        return (
            self.db.query(AccountSheet)
            .filter(AccountSheet.sheet_id == sheet_id)
            .first()
        )
    
    def get_by_sheet_type(self, sheet_type: str) -> List[AccountSheet]:
        """Get all sheets of specific type"""
        return (
            self.db.query(AccountSheet)
            .filter(AccountSheet.sheet_type == sheet_type)
            .order_by(desc(AccountSheet.last_sync))
            .all()
        )
    
    def get_auto_sync_sheets(self) -> List[AccountSheet]:
        """Get sheets that have auto sync enabled"""
        return (
            self.db.query(AccountSheet)
            .filter(AccountSheet.auto_sync == True)
            .order_by(asc(AccountSheet.last_sync))
            .all()
        )
    
    def get_sheets_needing_sync(self) -> List[AccountSheet]:
        """Get sheets that need synchronization based on frequency"""
        sheets = []
        auto_sync_sheets = self.get_auto_sync_sheets()
        
        current_time = datetime.utcnow()
        
        for sheet in auto_sync_sheets:
            if not sheet.last_sync:
                # Never synced before
                sheets.append(sheet)
            else:
                # Check if enough time has passed
                time_since_sync = current_time - sheet.last_sync
                sync_interval = timedelta(minutes=sheet.sync_frequency)
                
                if time_since_sync >= sync_interval:
                    sheets.append(sheet)
        
        return sheets
    
    def get_sheets_by_sync_status(self, sync_status: str) -> List[AccountSheet]:
        """Get sheets by sync status"""
        return (
            self.db.query(AccountSheet)
            .filter(AccountSheet.sync_status == sync_status)
            .order_by(desc(AccountSheet.updated_at))
            .all()
        )
    
    def update_sync_status(self, sheet_id: int, sync_status: str, last_sync: datetime = None) -> Optional[AccountSheet]:
        """Update sync status and last sync time"""
        sheet = self.get(sheet_id)
        if sheet:
            sheet.sync_status = sync_status
            if last_sync:
                sheet.last_sync = last_sync
            else:
                sheet.last_sync = datetime.utcnow()
            sheet.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(sheet)
        return sheet
    
    def update_last_row(self, sheet_id: int, last_row: int) -> Optional[AccountSheet]:
        """Update the last row number for a sheet"""
        sheet = self.get(sheet_id)
        if sheet:
            sheet.last_row = last_row
            sheet.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(sheet)
        return sheet
    
    def update_headers(self, sheet_id: int, headers: List[str]) -> Optional[AccountSheet]:
        """Update sheet headers"""
        sheet = self.get(sheet_id)
        if sheet:
            import json
            sheet.headers = json.dumps(headers)
            sheet.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(sheet)
        return sheet
    
    def get_with_account(self, sheet_id: int) -> Optional[AccountSheet]:
        """Get sheet with account information"""
        return (
            self.db.query(AccountSheet)
            .join(Account, AccountSheet.account_id == Account.id)
            .filter(AccountSheet.id == sheet_id)
            .first()
        )
    
    def search_sheets(self, query: str, sheet_type: Optional[str] = None) -> List[AccountSheet]:
        """Search sheets by name or URL"""
        search_filter = or_(
            AccountSheet.sheet_name.contains(query),
            AccountSheet.sheet_url.contains(query)
        )
        
        db_query = self.db.query(AccountSheet).filter(search_filter)
        
        if sheet_type:
            db_query = db_query.filter(AccountSheet.sheet_type == sheet_type)
        
        return db_query.order_by(desc(AccountSheet.updated_at)).all()
    
    def count_by_account(self, account_id: int) -> int:
        """Count sheets for an account"""
        return (
            self.db.query(AccountSheet)
            .filter(AccountSheet.account_id == account_id)
            .count()
        )
    
    def count_by_type(self) -> Dict[str, int]:
        """Count sheets by type"""
        results = (
            self.db.query(AccountSheet.sheet_type, func.count(AccountSheet.id))
            .group_by(AccountSheet.sheet_type)
            .all()
        )
        return {sheet_type: count for sheet_type, count in results}
    
    def count_by_sync_status(self) -> Dict[str, int]:
        """Count sheets by sync status"""
        results = (
            self.db.query(AccountSheet.sync_status, func.count(AccountSheet.id))
            .group_by(AccountSheet.sync_status)
            .all()
        )
        return {status: count for status, count in results}
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """Get sync statistics"""
        total_sheets = self.db.query(AccountSheet).count()
        auto_sync_enabled = self.db.query(AccountSheet).filter(AccountSheet.auto_sync == True).count()
        
        # Sheets synced in last 24 hours
        last_24h = datetime.utcnow() - timedelta(hours=24)
        recently_synced = (
            self.db.query(AccountSheet)
            .filter(AccountSheet.last_sync >= last_24h)
            .count()
        )
        
        # Sheets needing sync
        needing_sync = len(self.get_sheets_needing_sync())
        
        # Sync status breakdown
        sync_status_counts = self.count_by_sync_status()
        
        # Type breakdown
        type_counts = self.count_by_type()
        
        return {
            'total_sheets': total_sheets,
            'auto_sync_enabled': auto_sync_enabled,
            'recently_synced_24h': recently_synced,
            'needing_sync': needing_sync,
            'sync_status_breakdown': sync_status_counts,
            'type_breakdown': type_counts
        }
    
    def get_sheets_with_errors(self) -> List[AccountSheet]:
        """Get sheets with sync errors"""
        return (
            self.db.query(AccountSheet)
            .filter(AccountSheet.sync_status == 'error')
            .order_by(desc(AccountSheet.updated_at))
            .all()
        )
    
    def create_default_sheets_for_account(self, account_id: int) -> List[AccountSheet]:
        """Create default sheets for a new account"""
        default_sheets = [
            {
                'sheet_type': 'listings',
                'sheet_name': f'Account {account_id} - Listings',
                'headers': ['Listing ID', 'eBay Item ID', 'Title', 'Price', 'Status', 'Views', 'Watchers'],
                'sync_frequency': 60
            },
            {
                'sheet_type': 'orders',
                'sheet_name': f'Account {account_id} - Orders', 
                'headers': ['Order ID', 'Customer', 'Product', 'Quantity', 'Total Amount', 'Status', 'Order Date'],
                'sync_frequency': 30
            },
            {
                'sheet_type': 'messages',
                'sheet_name': f'Account {account_id} - Messages',
                'headers': ['Message ID', 'Type', 'Subject', 'Sender', 'Priority', 'Status', 'Date'],
                'sync_frequency': 15
            },
            {
                'sheet_type': 'drafts',
                'sheet_name': f'Account {account_id} - Draft Listings',
                'headers': ['Draft ID', 'Title', 'Price', 'Image Status', 'Status', 'Created Date'],
                'sync_frequency': 120
            }
        ]
        
        created_sheets = []
        
        for sheet_config in default_sheets:
            # Generate placeholder sheet ID (would be real Google Sheet ID in production)
            import uuid
            sheet_id = f"SHEET_{uuid.uuid4().hex[:8].upper()}"
            
            sheet = AccountSheet(
                account_id=account_id,
                sheet_id=sheet_id,
                sheet_name=sheet_config['sheet_name'],
                sheet_type=sheet_config['sheet_type'],
                headers=str(sheet_config['headers']),  # Convert to JSON string
                sync_frequency=sheet_config['sync_frequency'],
                auto_sync=True,
                sync_status='pending',
                last_row=1,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            created_sheet = self.create(sheet)
            created_sheets.append(created_sheet)
        
        return created_sheets
    
    def bulk_enable_sync(self, sheet_ids: List[int], auto_sync: bool = True) -> int:
        """Bulk enable/disable auto sync for multiple sheets"""
        updated = (
            self.db.query(AccountSheet)
            .filter(AccountSheet.id.in_(sheet_ids))
            .update(
                {
                    AccountSheet.auto_sync: auto_sync,
                    AccountSheet.updated_at: datetime.utcnow()
                }, 
                synchronize_session=False
            )
        )
        self.db.commit()
        return updated
    
    def bulk_update_sync_frequency(self, sheet_ids: List[int], frequency_minutes: int) -> int:
        """Bulk update sync frequency for multiple sheets"""
        updated = (
            self.db.query(AccountSheet)
            .filter(AccountSheet.id.in_(sheet_ids))
            .update(
                {
                    AccountSheet.sync_frequency: frequency_minutes,
                    AccountSheet.updated_at: datetime.utcnow()
                }, 
                synchronize_session=False
            )
        )
        self.db.commit()
        return updated
    
    def get_analytics(self, account_id: Optional[int] = None) -> Dict[str, Any]:
        """Get account sheet analytics"""
        query = self.db.query(AccountSheet)
        
        if account_id:
            query = query.filter(AccountSheet.account_id == account_id)
        
        # Basic stats
        stats = self.get_sync_statistics()
        
        # Recent activity
        recent_syncs = (
            query
            .filter(AccountSheet.last_sync.isnot(None))
            .order_by(desc(AccountSheet.last_sync))
            .limit(10)
            .all()
        )
        
        # Error sheets
        error_sheets = self.get_sheets_with_errors()
        
        # Average sync frequency
        avg_frequency = (
            query
            .with_entities(func.avg(AccountSheet.sync_frequency))
            .scalar() or 0
        )
        
        return {
            **stats,
            'recent_sync_activity': [
                {
                    'sheet_name': sheet.sheet_name,
                    'sheet_type': sheet.sheet_type,
                    'last_sync': sheet.last_sync.isoformat() if sheet.last_sync else None,
                    'sync_status': sheet.sync_status
                }
                for sheet in recent_syncs
            ],
            'error_sheets': len(error_sheets),
            'average_sync_frequency_minutes': float(avg_frequency)
        }