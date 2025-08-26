"""
Google Sheets Connection Service (Single Responsibility Principle)
Responsible ONLY for managing Google Sheets API connection
"""

import os
from typing import Optional, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False

from app.core.interfaces.services import IDataConnectionService
from app.core.config import settings


class SheetsConnectionService(IDataConnectionService):
    """
    Single Responsibility: Manage Google Sheets API connection only
    """
    
    def __init__(self):
        self.service = None
        self.credentials = None
        self.spreadsheet_id = settings.SPREADSHEET_ID
        self._executor = ThreadPoolExecutor(max_workers=3)
        self._is_connected = False
        
    async def connect(self) -> bool:
        """Establish connection to Google Sheets API"""
        if not GOOGLE_API_AVAILABLE:
            return False
            
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self._executor,
                self._initialize_connection
            )
            
            self._is_connected = result
            return result
            
        except Exception as e:
            print(f"Error connecting to Google Sheets: {e}")
            self._is_connected = False
            return False
    
    def _initialize_connection(self) -> bool:
        """Initialize Google Sheets connection (sync method for thread pool)"""
        try:
            if not os.path.exists(settings.GOOGLE_SHEETS_CREDENTIALS_PATH):
                print(f"Credentials file not found: {settings.GOOGLE_SHEETS_CREDENTIALS_PATH}")
                return False
            
            self.credentials = service_account.Credentials.from_service_account_file(
                settings.GOOGLE_SHEETS_CREDENTIALS_PATH,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            
            self.service = build('sheets', 'v4', credentials=self.credentials)
            print("✅ Google Sheets connection established")
            return True
            
        except Exception as e:
            print(f"Failed to initialize Google Sheets connection: {e}")
            return False
    
    async def disconnect(self) -> bool:
        """Close connection to Google Sheets"""
        try:
            self.service = None
            self.credentials = None
            self._is_connected = False
            
            # Shutdown thread pool
            self._executor.shutdown(wait=False)
            print("✅ Google Sheets connection closed")
            return True
            
        except Exception as e:
            print(f"Error disconnecting from Google Sheets: {e}")
            return False
    
    async def is_connected(self) -> bool:
        """Check if connection is active"""
        return self._is_connected and self.service is not None
    
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection and return detailed status"""
        if not await self.is_connected():
            return {
                "connected": False,
                "error": "Not connected to Google Sheets",
                "api_available": GOOGLE_API_AVAILABLE,
                "credentials_exist": os.path.exists(settings.GOOGLE_SHEETS_CREDENTIALS_PATH) if settings.GOOGLE_SHEETS_CREDENTIALS_PATH else False
            }
        
        try:
            # Test with a simple API call
            loop = asyncio.get_event_loop()
            test_result = await loop.run_in_executor(
                self._executor,
                self._test_api_call
            )
            
            return {
                "connected": True,
                "api_available": GOOGLE_API_AVAILABLE,
                "credentials_exist": True,
                "spreadsheet_accessible": test_result["success"],
                "spreadsheet_id": self.spreadsheet_id,
                "test_details": test_result
            }
            
        except Exception as e:
            return {
                "connected": False,
                "error": str(e),
                "api_available": GOOGLE_API_AVAILABLE,
                "credentials_exist": True
            }
    
    def _test_api_call(self) -> Dict[str, Any]:
        """Test API call (sync method for thread pool)"""
        try:
            # Try to get spreadsheet metadata
            spreadsheet = self.service.spreadsheets().get(
                spreadsheetId=self.spreadsheet_id
            ).execute()
            
            return {
                "success": True,
                "spreadsheet_title": spreadsheet.get('properties', {}).get('title', 'Unknown'),
                "sheet_count": len(spreadsheet.get('sheets', [])),
                "sheets": [sheet['properties']['title'] for sheet in spreadsheet.get('sheets', [])]
            }
            
        except HttpError as error:
            return {
                "success": False,
                "error": f"HTTP Error: {error}",
                "error_code": error.resp.status if hasattr(error, 'resp') else None
            }
        except Exception as error:
            return {
                "success": False,
                "error": str(error)
            }
    
    def get_service(self):
        """Get the Google Sheets service instance"""
        return self.service
    
    def get_spreadsheet_id(self) -> Optional[str]:
        """Get the configured spreadsheet ID"""
        return self.spreadsheet_id
    
    async def execute_api_call(self, api_call_func, *args, **kwargs) -> Any:
        """
        Execute Google Sheets API call in thread pool
        Single responsibility: Handle async execution of sync API calls
        """
        if not await self.is_connected():
            raise ConnectionError("Not connected to Google Sheets")
        
        try:
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self._executor,
                api_call_func,
                *args,
                **kwargs
            )
        except Exception as e:
            print(f"API call execution failed: {e}")
            raise
    
    async def get_connection_info(self) -> Dict[str, Any]:
        """Get detailed connection information"""
        return {
            "service_type": "Google Sheets",
            "connected": await self.is_connected(),
            "api_available": GOOGLE_API_AVAILABLE,
            "spreadsheet_id": self.spreadsheet_id,
            "credentials_path": settings.GOOGLE_SHEETS_CREDENTIALS_PATH,
            "has_credentials": self.credentials is not None,
            "has_service": self.service is not None
        }
    
    def __del__(self):
        """Cleanup when service is destroyed"""
        try:
            if hasattr(self, '_executor'):
                self._executor.shutdown(wait=False)
        except:
            pass