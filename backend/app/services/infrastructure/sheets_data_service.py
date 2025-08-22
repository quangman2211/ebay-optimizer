"""
Google Sheets Data Service (Single Responsibility Principle)
Responsible ONLY for raw data operations with Google Sheets
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio

from app.core.interfaces.services import ISheetsDataService
from app.services.infrastructure.sheets_connection_service import SheetsConnectionService


class SheetsDataService(ISheetsDataService):
    """
    Single Responsibility: Handle raw Google Sheets data operations
    """
    
    def __init__(self, connection_service: SheetsConnectionService):
        self.connection = connection_service
        
    async def get_sheet_data(self, sheet_name: str, range_name: str) -> List[List[str]]:
        """Get raw data from sheet"""
        if not await self.connection.is_connected():
            await self.connection.connect()
        
        if not await self.connection.is_connected():
            raise ConnectionError("Cannot connect to Google Sheets")
        
        try:
            def _get_data():
                service = self.connection.get_service()
                result = service.spreadsheets().values().get(
                    spreadsheetId=self.connection.get_spreadsheet_id(),
                    range=f"{sheet_name}!{range_name}"
                ).execute()
                return result.get('values', [])
            
            return await self.connection.execute_api_call(_get_data)
            
        except Exception as e:
            print(f"Error getting sheet data: {e}")
            return []
    
    async def update_sheet_data(self, sheet_name: str, range_name: str, values: List[List[str]]) -> bool:
        """Update data in sheet"""
        if not await self.connection.is_connected():
            raise ConnectionError("Not connected to Google Sheets")
        
        try:
            def _update_data():
                service = self.connection.get_service()
                body = {'values': values}
                
                service.spreadsheets().values().update(
                    spreadsheetId=self.connection.get_spreadsheet_id(),
                    range=f"{sheet_name}!{range_name}",
                    valueInputOption='USER_ENTERED',
                    body=body
                ).execute()
                return True
            
            return await self.connection.execute_api_call(_update_data)
            
        except Exception as e:
            print(f"Error updating sheet data: {e}")
            return False
    
    async def append_sheet_data(self, sheet_name: str, values: List[List[str]]) -> bool:
        """Append data to sheet"""
        if not await self.connection.is_connected():
            raise ConnectionError("Not connected to Google Sheets")
        
        try:
            def _append_data():
                service = self.connection.get_service()
                body = {'values': values}
                
                service.spreadsheets().values().append(
                    spreadsheetId=self.connection.get_spreadsheet_id(),
                    range=f"{sheet_name}!A:Z",
                    valueInputOption='USER_ENTERED',
                    insertDataOption='INSERT_ROWS',
                    body=body
                ).execute()
                return True
            
            return await self.connection.execute_api_call(_append_data)
            
        except Exception as e:
            print(f"Error appending sheet data: {e}")
            return False
    
    async def create_sheet(self, sheet_name: str, headers: List[str]) -> bool:
        """Create new sheet with headers"""
        if not await self.connection.is_connected():
            raise ConnectionError("Not connected to Google Sheets")
        
        try:
            def _create_sheet():
                service = self.connection.get_service()
                
                # First, check if sheet already exists
                spreadsheet = service.spreadsheets().get(
                    spreadsheetId=self.connection.get_spreadsheet_id()
                ).execute()
                
                existing_sheets = [sheet['properties']['title'] for sheet in spreadsheet.get('sheets', [])]
                
                if sheet_name not in existing_sheets:
                    # Create the sheet
                    request_body = {
                        'requests': [{
                            'addSheet': {
                                'properties': {'title': sheet_name}
                            }
                        }]
                    }
                    
                    service.spreadsheets().batchUpdate(
                        spreadsheetId=self.connection.get_spreadsheet_id(),
                        body=request_body
                    ).execute()
                
                # Add headers
                if headers:
                    body = {'values': [headers]}
                    service.spreadsheets().values().update(
                        spreadsheetId=self.connection.get_spreadsheet_id(),
                        range=f"{sheet_name}!A1:{chr(65 + len(headers) - 1)}1",
                        valueInputOption='USER_ENTERED',
                        body=body
                    ).execute()
                
                return True
            
            return await self.connection.execute_api_call(_create_sheet)
            
        except Exception as e:
            print(f"Error creating sheet: {e}")
            return False
    
    async def get_sheet_info(self, sheet_name: str) -> Dict[str, Any]:
        """Get sheet metadata and information"""
        if not await self.connection.is_connected():
            raise ConnectionError("Not connected to Google Sheets")
        
        try:
            def _get_info():
                service = self.connection.get_service()
                spreadsheet = service.spreadsheets().get(
                    spreadsheetId=self.connection.get_spreadsheet_id()
                ).execute()
                
                for sheet in spreadsheet.get('sheets', []):
                    if sheet['properties']['title'] == sheet_name:
                        props = sheet['properties']
                        return {
                            'title': props['title'],
                            'sheet_id': props['sheetId'],
                            'sheet_type': props.get('sheetType', 'GRID'),
                            'grid_properties': props.get('gridProperties', {}),
                            'row_count': props.get('gridProperties', {}).get('rowCount', 0),
                            'column_count': props.get('gridProperties', {}).get('columnCount', 0)
                        }
                
                return None
            
            return await self.connection.execute_api_call(_get_info)
            
        except Exception as e:
            print(f"Error getting sheet info: {e}")
            return None
    
    async def batch_update_data(self, updates: List[Dict[str, Any]]) -> bool:
        """
        Batch update multiple ranges
        updates format: [{'sheet_name': 'Sheet1', 'range': 'A1:B2', 'values': [[...]]}, ...]
        """
        if not await self.connection.is_connected():
            raise ConnectionError("Not connected to Google Sheets")
        
        try:
            def _batch_update():
                service = self.connection.get_service()
                
                data = []
                for update in updates:
                    sheet_name = update['sheet_name']
                    range_name = update['range']
                    values = update['values']
                    
                    data.append({
                        'range': f"{sheet_name}!{range_name}",
                        'values': values
                    })
                
                body = {
                    'valueInputOption': 'USER_ENTERED',
                    'data': data
                }
                
                service.spreadsheets().values().batchUpdate(
                    spreadsheetId=self.connection.get_spreadsheet_id(),
                    body=body
                ).execute()
                
                return True
            
            return await self.connection.execute_api_call(_batch_update)
            
        except Exception as e:
            print(f"Error in batch update: {e}")
            return False
    
    async def clear_sheet_data(self, sheet_name: str, range_name: str) -> bool:
        """Clear data from sheet range"""
        if not await self.connection.is_connected():
            raise ConnectionError("Not connected to Google Sheets")
        
        try:
            def _clear_data():
                service = self.connection.get_service()
                service.spreadsheets().values().clear(
                    spreadsheetId=self.connection.get_spreadsheet_id(),
                    range=f"{sheet_name}!{range_name}"
                ).execute()
                return True
            
            return await self.connection.execute_api_call(_clear_data)
            
        except Exception as e:
            print(f"Error clearing sheet data: {e}")
            return False
    
    async def get_sheet_names(self) -> List[str]:
        """Get all sheet names in the spreadsheet"""
        if not await self.connection.is_connected():
            raise ConnectionError("Not connected to Google Sheets")
        
        try:
            def _get_names():
                service = self.connection.get_service()
                spreadsheet = service.spreadsheets().get(
                    spreadsheetId=self.connection.get_spreadsheet_id()
                ).execute()
                
                return [sheet['properties']['title'] for sheet in spreadsheet.get('sheets', [])]
            
            return await self.connection.execute_api_call(_get_names)
            
        except Exception as e:
            print(f"Error getting sheet names: {e}")
            return []
    
    async def copy_sheet(self, source_sheet_id: int, destination_name: str) -> bool:
        """Copy a sheet within the same spreadsheet"""
        if not await self.connection.is_connected():
            raise ConnectionError("Not connected to Google Sheets")
        
        try:
            def _copy_sheet():
                service = self.connection.get_service()
                
                request_body = {
                    'requests': [{
                        'duplicateSheet': {
                            'sourceSheetId': source_sheet_id,
                            'newSheetName': destination_name
                        }
                    }]
                }
                
                service.spreadsheets().batchUpdate(
                    spreadsheetId=self.connection.get_spreadsheet_id(),
                    body=request_body
                ).execute()
                
                return True
            
            return await self.connection.execute_api_call(_copy_sheet)
            
        except Exception as e:
            print(f"Error copying sheet: {e}")
            return False
    
    async def delete_sheet(self, sheet_id: int) -> bool:
        """Delete a sheet by ID"""
        if not await self.connection.is_connected():
            raise ConnectionError("Not connected to Google Sheets")
        
        try:
            def _delete_sheet():
                service = self.connection.get_service()
                
                request_body = {
                    'requests': [{
                        'deleteSheet': {
                            'sheetId': sheet_id
                        }
                    }]
                }
                
                service.spreadsheets().batchUpdate(
                    spreadsheetId=self.connection.get_spreadsheet_id(),
                    body=request_body
                ).execute()
                
                return True
            
            return await self.connection.execute_api_call(_delete_sheet)
            
        except Exception as e:
            print(f"Error deleting sheet: {e}")
            return False