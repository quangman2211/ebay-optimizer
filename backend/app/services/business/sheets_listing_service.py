"""
Sheets Listing Service (Single Responsibility Principle)
Responsible ONLY for listing-related operations with Google Sheets
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from app.core.interfaces.services import IListingDataService
from app.services.infrastructure.sheets_data_service import SheetsDataService
from app.models.listing import ListingStatus


class SheetsListingService(IListingDataService):
    """
    Single Responsibility: Handle listing-specific operations with Google Sheets
    """
    
    def __init__(self, sheets_data_service: SheetsDataService):
        self.sheets_service = sheets_data_service
        self.sheet_name = "Listings"
        
        # Column mapping for listings
        self.column_map = {
            'Listing ID': 'id',
            'eBay Item ID': 'item_id',
            'SKU': 'sku',
            'Current Title': 'title',
            'Optimized Title': 'optimized_title',
            'Description': 'description',
            'Category': 'category',
            'Price': 'price',
            'Quantity': 'quantity',
            'Condition': 'condition',
            'Status': 'status',
            'Keywords': 'keywords',
            'Item Specifics': 'item_specifics',
            'Views': 'views',
            'Watchers': 'watchers',
            'Sold': 'sold',
            'Performance Score': 'performance_score',
            'SEO Score': 'seo_score',
            'Created': 'created_at',
            'Last Updated': 'updated_at'
        }
        
        self.headers = list(self.column_map.keys())
    
    async def get_all_listings(self) -> List[Dict[str, Any]]:
        """Get all listings from Google Sheets"""
        try:
            # Get raw data from sheet
            data = await self.sheets_service.get_sheet_data(
                self.sheet_name, 
                f"A:T"  # Cover all listing columns
            )
            
            if not data:
                return []
            
            # First row should be headers
            headers = data[0] if data else self.headers
            listings = []
            
            for row_index, row in enumerate(data[1:], start=2):
                listing = self._row_to_listing(headers, row, row_index)
                if listing:
                    listings.append(listing)
            
            return listings
            
        except Exception as e:
            print(f"Error getting listings from sheets: {e}")
            return []
    
    async def get_listing_by_id(self, listing_id: str) -> Optional[Dict[str, Any]]:
        """Get single listing by ID from Google Sheets"""
        try:
            listings = await self.get_all_listings()
            for listing in listings:
                if listing.get('id') == listing_id:
                    return listing
            return None
            
        except Exception as e:
            print(f"Error getting listing by ID from sheets: {e}")
            return None
    
    async def create_listing(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new listing in Google Sheets"""
        try:
            # Prepare row data
            row_data = self._listing_to_row(listing_data)
            
            # Append to sheet
            success = await self.sheets_service.append_sheet_data(
                self.sheet_name,
                [row_data]
            )
            
            if success:
                # Add metadata
                listing_data['sheet_row'] = None  # Will be set by sheets
                listing_data['created_at'] = datetime.now().isoformat()
                listing_data['updated_at'] = datetime.now().isoformat()
                return listing_data
            else:
                raise Exception("Failed to append to sheet")
                
        except Exception as e:
            print(f"Error creating listing in sheets: {e}")
            raise
    
    async def update_listing(self, listing_id: str, listing_data: Dict[str, Any]) -> bool:
        """Update existing listing in Google Sheets"""
        try:
            # First, find the listing and its row
            listings = await self.get_all_listings()
            target_row = None
            
            for listing in listings:
                if listing.get('id') == listing_id:
                    target_row = listing.get('sheet_row')
                    break
            
            if not target_row:
                return False
            
            # Update the data with current timestamp
            listing_data['updated_at'] = datetime.now().isoformat()
            
            # Convert to row format
            row_data = self._listing_to_row(listing_data)
            
            # Update the specific row
            success = await self.sheets_service.update_sheet_data(
                self.sheet_name,
                f"A{target_row}:T{target_row}",
                [row_data]
            )
            
            return success
            
        except Exception as e:
            print(f"Error updating listing in sheets: {e}")
            return False
    
    async def delete_listing(self, listing_id: str) -> bool:
        """Delete/archive listing (change status to archived)"""
        try:
            return await self.update_listing(listing_id, {
                'status': ListingStatus.ARCHIVED,
                'updated_at': datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"Error archiving listing in sheets: {e}")
            return False
    
    async def bulk_update_listings(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk update multiple listings in Google Sheets"""
        try:
            success_count = 0
            failed_count = 0
            batch_updates = []
            
            # Get current listings to find row numbers
            current_listings = await self.get_all_listings()
            listing_rows = {listing['id']: listing.get('sheet_row') for listing in current_listings}
            
            # Prepare batch updates
            for update in updates:
                listing_id = update.get('id')
                if not listing_id or listing_id not in listing_rows:
                    failed_count += 1
                    continue
                
                row_num = listing_rows[listing_id]
                if not row_num:
                    failed_count += 1
                    continue
                
                # Add timestamp
                update['updated_at'] = datetime.now().isoformat()
                row_data = self._listing_to_row(update)
                
                batch_updates.append({
                    'sheet_name': self.sheet_name,
                    'range': f"A{row_num}:T{row_num}",
                    'values': [row_data]
                })
            
            # Execute batch update
            if batch_updates:
                success = await self.sheets_service.batch_update_data(batch_updates)
                if success:
                    success_count = len(batch_updates)
                else:
                    failed_count += len(batch_updates)
            
            return {
                'success': success_count,
                'failed': failed_count,
                'total': len(updates)
            }
            
        except Exception as e:
            print(f"Error in bulk update listings: {e}")
            return {
                'success': 0,
                'failed': len(updates),
                'total': len(updates),
                'error': str(e)
            }
    
    async def initialize_sheet(self) -> bool:
        """Initialize listings sheet with headers if it doesn't exist"""
        try:
            return await self.sheets_service.create_sheet(self.sheet_name, self.headers)
        except Exception as e:
            print(f"Error initializing listings sheet: {e}")
            return False
    
    def _row_to_listing(self, headers: List[str], row: List[str], row_index: int) -> Optional[Dict[str, Any]]:
        """Convert sheet row to listing dictionary"""
        try:
            listing = {'sheet_row': row_index}
            
            for i, header in enumerate(headers):
                if i < len(row):
                    value = row[i].strip() if row[i] else ''
                    field_name = self.column_map.get(header, header.lower().replace(' ', '_'))
                    
                    # Parse specific field types
                    if field_name in ['price', 'performance_score', 'seo_score'] and value:
                        try:
                            listing[field_name] = float(value.replace('$', '').replace(',', ''))
                        except:
                            listing[field_name] = 0.0
                    elif field_name in ['quantity', 'views', 'watchers', 'sold'] and value:
                        try:
                            listing[field_name] = int(value)
                        except:
                            listing[field_name] = 0
                    elif field_name == 'keywords' and value:
                        listing[field_name] = [k.strip() for k in value.split(',') if k.strip()]
                    elif field_name == 'item_specifics' and value:
                        try:
                            listing[field_name] = json.loads(value)
                        except:
                            listing[field_name] = {}
                    elif field_name == 'status' and value:
                        listing[field_name] = value.lower()
                    else:
                        listing[field_name] = value
            
            # Set defaults for required fields
            if 'id' not in listing or not listing['id']:
                listing['id'] = f"listing_{row_index}_{datetime.now().timestamp()}"
            
            if 'status' not in listing:
                listing['status'] = ListingStatus.DRAFT
            
            if 'created_at' not in listing:
                listing['created_at'] = datetime.now().isoformat()
            
            if 'updated_at' not in listing:
                listing['updated_at'] = datetime.now().isoformat()
            
            return listing
            
        except Exception as e:
            print(f"Error converting row to listing: {e}")
            return None
    
    def _listing_to_row(self, listing: Dict[str, Any]) -> List[str]:
        """Convert listing dictionary to sheet row"""
        try:
            row = []
            
            for header in self.headers:
                field_name = self.column_map[header]
                value = listing.get(field_name, '')
                
                # Format specific field types
                if field_name in ['keywords'] and isinstance(value, list):
                    row.append(', '.join(value))
                elif field_name == 'item_specifics' and isinstance(value, dict):
                    row.append(json.dumps(value) if value else '{}')
                elif field_name in ['price']:
                    row.append(str(value) if value else '0')
                elif field_name in ['quantity', 'views', 'watchers', 'sold']:
                    row.append(str(int(value)) if value else '0')
                elif field_name in ['performance_score', 'seo_score']:
                    row.append(str(float(value)) if value else '0.0')
                else:
                    row.append(str(value) if value is not None else '')
            
            return row
            
        except Exception as e:
            print(f"Error converting listing to row: {e}")
            return [''] * len(self.headers)
    
    async def get_listings_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get listings filtered by status"""
        try:
            all_listings = await self.get_all_listings()
            return [listing for listing in all_listings if listing.get('status', '').lower() == status.lower()]
        except Exception as e:
            print(f"Error getting listings by status: {e}")
            return []
    
    async def get_listings_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get listings filtered by category"""
        try:
            all_listings = await self.get_all_listings()
            return [listing for listing in all_listings if listing.get('category', '').lower() == category.lower()]
        except Exception as e:
            print(f"Error getting listings by category: {e}")
            return []
    
    async def search_listings(self, query: str, fields: List[str] = None) -> List[Dict[str, Any]]:
        """Search listings by query in specified fields"""
        try:
            if not fields:
                fields = ['title', 'description', 'category', 'sku']
            
            all_listings = await self.get_all_listings()
            query_lower = query.lower()
            
            matching_listings = []
            for listing in all_listings:
                for field in fields:
                    field_value = str(listing.get(field, '')).lower()
                    if query_lower in field_value:
                        matching_listings.append(listing)
                        break  # Avoid duplicates
            
            return matching_listings
            
        except Exception as e:
            print(f"Error searching listings: {e}")
            return []