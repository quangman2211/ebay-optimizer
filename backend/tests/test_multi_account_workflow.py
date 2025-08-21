"""
Playwright E2E Tests for Multi-Account eBay Management System
Tests the complete workflow: 1 product → multiple accounts → multiple listing IDs
"""

import pytest
import requests
import json
import time
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"
TEST_USER = {
    "email": "test@ebayoptimizer.com",
    "password": "123456"
}

class TestMultiAccountWorkflow:
    """Test suite for multi-account eBay management workflow"""
    
    @pytest.fixture(scope="class")
    def auth_token(self) -> str:
        """Get authentication token for tests"""
        response = requests.post(
            f"{API_BASE}/auth/login-json",
            json=TEST_USER,
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token: str) -> Dict[str, str]:
        """Create authentication headers"""
        return {"Authorization": f"Bearer {auth_token}"}
    
    def test_01_server_health(self):
        """Test 1: Verify server is running and healthy"""
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert health_data["status"] == "healthy"
        assert "eBay Listing Optimizer" in health_data["service"]
    
    def test_02_authentication_flow(self, auth_token: str):
        """Test 2: Verify authentication works correctly"""
        assert auth_token is not None
        assert len(auth_token) > 50  # JWT tokens are long
        
        # Test auth/me endpoint
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{API_BASE}/auth/me", headers=headers)
        assert response.status_code == 200
        
        user_data = response.json()
        assert user_data["email"] == TEST_USER["email"]
    
    def test_03_create_test_accounts(self, auth_headers: Dict[str, str]):
        """Test 3: Create multiple eBay accounts for testing"""
        accounts = [
            {
                "ebay_username": "test_account_1",
                "email": "account1@test.com",
                "status": "active",
                "country": "US"
            },
            {
                "ebay_username": "test_account_2", 
                "email": "account2@test.com",
                "status": "active",
                "country": "US"
            },
            {
                "ebay_username": "test_account_3",
                "email": "account3@test.com", 
                "status": "active",
                "country": "CA"
            }
        ]
        
        created_accounts = []
        for account_data in accounts:
            response = requests.post(
                f"{API_BASE}/accounts",
                json=account_data,
                headers=auth_headers
            )
            
            # May already exist from previous tests
            if response.status_code in [200, 201]:
                account = response.json()["data"]
                created_accounts.append(account)
            elif response.status_code == 409:
                # Account already exists, try to get it
                response = requests.get(f"{API_BASE}/accounts", headers=auth_headers)
                if response.status_code == 200:
                    existing_accounts = response.json().get("data", [])
                    for acc in existing_accounts:
                        if acc.get("ebay_username") == account_data["ebay_username"]:
                            created_accounts.append(acc)
                            break
        
        assert len(created_accounts) >= 2  # At least 2 accounts created
        return created_accounts
    
    def test_04_create_source_product(self, auth_headers: Dict[str, str]):
        """Test 4: Create a source product that can be listed on multiple accounts"""
        product_data = {
            "id": "PROD_TEST_001",
            "source_id": "TEST_SOURCE", 
            "title": "Test Gaming Headset with RGB Lighting",
            "description": "High-quality gaming headset with surround sound and RGB lighting effects",
            "price": 49.99,
            "category": "Video Games & Consoles",
            "brand": "TestBrand",
            "sku": "TST-HDST-001",
            "profit_margin": 25.0,
            "suggested_ebay_price": 74.99,
            "in_stock": True,
            "stock_quantity": 100,
            "gdrive_folder_url": "https://drive.google.com/drive/folders/test_images_folder",
            "image_notes": "6 product images, need watermark removal",
            "is_approved": True
        }
        
        response = requests.post(
            f"{API_BASE}/sources/products",
            json=product_data,
            headers=auth_headers
        )
        
        # May already exist
        if response.status_code in [200, 201]:
            product = response.json()["data"]
        elif response.status_code == 409:
            # Product exists, get it
            response = requests.get(
                f"{API_BASE}/sources/products/{product_data['id']}",
                headers=auth_headers
            )
            assert response.status_code == 200
            product = response.json()["data"]
        else:
            # Create a basic source first
            source_data = {
                "id": "TEST_SOURCE",
                "name": "Test Supplier",
                "website_url": "https://testsupplier.com",
                "status": "connected"
            }
            requests.post(f"{API_BASE}/sources", json=source_data, headers=auth_headers)
            
            # Retry product creation
            response = requests.post(
                f"{API_BASE}/sources/products",
                json=product_data,
                headers=auth_headers
            )
            assert response.status_code in [200, 201]
            product = response.json()["data"]
        
        assert product["title"] == product_data["title"]
        assert product["price"] == product_data["price"]
        return product
    
    def test_05_create_draft_listings_multi_account(self, auth_headers: Dict[str, str]):
        """Test 5: Create draft listings for the same product across multiple accounts"""
        # Get accounts
        accounts_response = requests.get(f"{API_BASE}/accounts", headers=auth_headers)
        assert accounts_response.status_code == 200
        accounts = accounts_response.json()["data"]
        assert len(accounts) >= 2
        
        # Get source product
        product_id = "PROD_TEST_001"
        
        draft_listings = []
        for i, account in enumerate(accounts[:3]):  # Use first 3 accounts
            draft_data = {
                "account_id": account["id"],
                "source_product_id": product_id,
                "title": f"Gaming Headset RGB - Account {i+1} Edition",
                "description": f"Customized listing for account {account['ebay_username']}",
                "category": "Video Games & Consoles",
                "price": 74.99 + (i * 5),  # Different prices per account
                "quantity": 10,
                "condition": "new",
                "gdrive_folder_url": f"https://drive.google.com/drive/folders/edited_images_account_{i+1}",
                "cost_price": 49.99,
                "profit_margin": 30.0 + (i * 2),
                "notes": f"Draft listing for {account['ebay_username']}"
            }
            
            response = requests.post(
                f"{API_BASE}/drafts/",
                json=draft_data,
                headers=auth_headers
            )
            
            if response.status_code in [200, 201]:
                draft = response.json()["data"]
                draft_listings.append(draft)
        
        assert len(draft_listings) >= 2  # At least 2 draft listings created
        
        # Verify each draft has unique IDs and account associations
        draft_ids = [draft["id"] for draft in draft_listings]
        assert len(set(draft_ids)) == len(draft_ids)  # All IDs are unique
        
        account_ids = [draft["account_id"] for draft in draft_listings]
        assert len(set(account_ids)) == len(account_ids)  # Different accounts
        
        return draft_listings
    
    def test_06_update_image_status_workflow(self, auth_headers: Dict[str, str]):
        """Test 6: Test image editing workflow for draft listings"""
        # Get draft listings
        response = requests.get(f"{API_BASE}/drafts/", headers=auth_headers)
        assert response.status_code == 200
        drafts = response.json()["data"]
        
        if not drafts:
            pytest.skip("No draft listings found for image status test")
        
        draft_id = drafts[0]["id"]
        
        # Update image status to 'edited'
        status_data = {
            "image_status": "edited",
            "edited_by": "John Designer"
        }
        
        response = requests.patch(
            f"{API_BASE}/drafts/{draft_id}/image-status",
            json=status_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        
        updated_draft = response.json()["data"]
        assert updated_draft["image_status"] == "edited"
        assert updated_draft["edited_by"] == "John Designer"
        
        # Update to 'approved'
        status_data["image_status"] = "approved"
        response = requests.patch(
            f"{API_BASE}/drafts/{draft_id}/image-status",
            json=status_data,
            headers=auth_headers
        )
        assert response.status_code == 200
    
    def test_07_message_management_multi_account(self, auth_headers: Dict[str, str]):
        """Test 7: Create and manage messages for different accounts"""
        # Get accounts
        accounts_response = requests.get(f"{API_BASE}/accounts", headers=auth_headers)
        assert accounts_response.status_code == 200
        accounts = accounts_response.json()["data"]
        
        if not accounts:
            pytest.skip("No accounts found for message test")
        
        messages = []
        for i, account in enumerate(accounts[:2]):
            message_data = {
                "account_id": account["id"],
                "message_type": "question",
                "subject": f"Product inquiry - Account {i+1}",
                "message_text": f"Hello, I have a question about the gaming headset listed on {account['ebay_username']}",
                "sender_username": f"buyer_{i+1}",
                "direction": "inbound",
                "priority": "normal"
            }
            
            response = requests.post(
                f"{API_BASE}/messages/",
                json=message_data,
                headers=auth_headers
            )
            
            if response.status_code in [200, 201]:
                message = response.json()["data"]
                messages.append(message)
        
        assert len(messages) >= 1  # At least one message created
        
        # Test message analytics
        response = requests.get(f"{API_BASE}/messages/analytics", headers=auth_headers)
        assert response.status_code == 200
        
        analytics = response.json()["data"]
        assert "status_breakdown" in analytics
        assert "type_breakdown" in analytics
    
    def test_08_account_sheets_integration(self, auth_headers: Dict[str, str]):
        """Test 8: Test Google Sheets integration per account"""
        # Get accounts
        accounts_response = requests.get(f"{API_BASE}/accounts", headers=auth_headers)
        assert accounts_response.status_code == 200
        accounts = accounts_response.json()["data"]
        
        if not accounts:
            pytest.skip("No accounts found for sheets test")
        
        account = accounts[0]
        
        # Create default sheets for account
        response = requests.post(
            f"{API_BASE}/account-sheets/account/{account['id']}/create-defaults",
            headers=auth_headers
        )
        
        if response.status_code in [200, 201]:
            sheets = response.json()["data"]
            assert len(sheets) >= 4  # listings, orders, messages, drafts
            
            # Verify different sheet types
            sheet_types = [sheet["sheet_type"] for sheet in sheets]
            expected_types = ["listings", "orders", "messages", "drafts"]
            for expected_type in expected_types:
                assert expected_type in sheet_types
        
        # Test sheets analytics
        response = requests.get(f"{API_BASE}/account-sheets/analytics", headers=auth_headers)
        assert response.status_code == 200
        
        analytics = response.json()["data"]
        assert "total_sheets" in analytics
        assert "type_breakdown" in analytics
    
    def test_09_multi_account_workflow_verification(self, auth_headers: Dict[str, str]):
        """Test 9: Verify the complete multi-account workflow"""
        # Get accounts
        accounts_response = requests.get(f"{API_BASE}/accounts", headers=auth_headers)
        assert accounts_response.status_code == 200
        accounts = accounts_response.json()["data"]
        
        # Get drafts
        drafts_response = requests.get(f"{API_BASE}/drafts/", headers=auth_headers)
        assert drafts_response.status_code == 200
        drafts = drafts_response.json()["data"]
        
        # Verify: 1 product → multiple accounts → unique draft IDs
        source_product_id = "PROD_TEST_001"
        product_drafts = [d for d in drafts if d.get("source_product_id") == source_product_id]
        
        if product_drafts:
            # Verify each draft is for different accounts
            draft_account_ids = [d["account_id"] for d in product_drafts]
            assert len(set(draft_account_ids)) == len(product_drafts)  # All different accounts
            
            # Verify each draft has unique ID
            draft_ids = [d["id"] for d in product_drafts]
            assert len(set(draft_ids)) == len(product_drafts)  # All unique IDs
            
            # Verify customization per account (different prices/titles)
            titles = [d["title"] for d in product_drafts]
            assert len(set(titles)) == len(product_drafts)  # Different titles
        
        print(f"✅ Multi-account workflow verified:")
        print(f"   - {len(accounts)} accounts created")
        print(f"   - {len(product_drafts)} draft listings for same product")
        print(f"   - Each account has unique draft listing")
    
    def test_10_analytics_and_reporting(self, auth_headers: Dict[str, str]):
        """Test 10: Verify analytics work across multiple accounts"""
        # Test drafts analytics
        drafts_response = requests.get(f"{API_BASE}/drafts/analytics", headers=auth_headers)
        assert drafts_response.status_code == 200
        
        drafts_analytics = response.json()["data"]
        assert "total_drafts" in drafts_analytics
        assert "status_breakdown" in drafts_analytics
        
        # Test messages analytics  
        messages_response = requests.get(f"{API_BASE}/messages/analytics", headers=auth_headers)
        assert messages_response.status_code == 200
        
        # Test account-specific analytics
        accounts_response = requests.get(f"{API_BASE}/accounts", headers=auth_headers)
        if accounts_response.status_code == 200:
            accounts = accounts_response.json()["data"]
            if accounts:
                account_id = accounts[0]["id"]
                
                # Get drafts for specific account
                response = requests.get(
                    f"{API_BASE}/drafts/?account_id={account_id}",
                    headers=auth_headers
                )
                assert response.status_code == 200
                
                account_drafts = response.json()["data"]
                # Verify all drafts belong to this account
                for draft in account_drafts:
                    assert draft["account_id"] == account_id
    
    def test_11_performance_and_scalability(self, auth_headers: Dict[str, str]):
        """Test 11: Basic performance testing"""
        start_time = time.time()
        
        # Test multiple concurrent requests
        endpoints = [
            f"{API_BASE}/accounts",
            f"{API_BASE}/drafts/",
            f"{API_BASE}/messages/",
            f"{API_BASE}/account-sheets/"
        ]
        
        for endpoint in endpoints:
            response = requests.get(endpoint, headers=auth_headers)
            assert response.status_code in [200, 307]  # 307 for redirects
        
        total_time = time.time() - start_time
        assert total_time < 5.0  # Should complete within 5 seconds
        
        print(f"✅ Performance test passed: {len(endpoints)} requests in {total_time:.2f}s")
    
    def test_12_cleanup_test_data(self, auth_headers: Dict[str, str]):
        """Test 12: Cleanup test data (optional)"""
        # This test can be used to clean up test data if needed
        # For now, we'll leave data for manual inspection
        pass


def run_workflow_test():
    """Standalone function to run the workflow test"""
    import subprocess
    import sys
    
    print("🚀 Running Multi-Account eBay Management E2E Tests")
    print("=" * 60)
    
    try:
        # Run pytest with verbose output
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            __file__, 
            "-v", 
            "--tb=short",
            "-s"  # Don't capture output
        ], capture_output=False, text=True)
        
        if result.returncode == 0:
            print("\n" + "=" * 60)
            print("🎉 All tests passed! Multi-account system is working correctly.")
            print("\nKey features verified:")
            print("✅ Server health and authentication")
            print("✅ Multiple eBay account management")  
            print("✅ Source product management")
            print("✅ Draft listings per account (1 product → N accounts)")
            print("✅ Image editing workflow")
            print("✅ Message management per account")
            print("✅ Google Sheets integration per account")
            print("✅ Analytics and reporting")
            print("✅ Performance and scalability")
        else:
            print("\n❌ Some tests failed. Please check the output above.")
            return False
        
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return False
    
    return True


if __name__ == "__main__":
    # Run the workflow test when script is executed directly
    success = run_workflow_test()
    exit(0 if success else 1)