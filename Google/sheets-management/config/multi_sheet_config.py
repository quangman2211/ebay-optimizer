"""
Multi-Sheet Configuration for 30 eBay Accounts
Account-to-Sheet mapping and VPS distribution
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AccountSheetMapping:
    """Configuration for a single eBay account's sheet mapping"""
    account_id: int
    ebay_username: str
    vps_id: int
    browser_profile: str
    browser_type: str
    google_sheet_id: str
    sheet_name: str
    collection_schedule: List[str]
    sync_interval_minutes: int = 300  # 5 minutes default


# 30 eBay Accounts with 1-to-1 Google Sheet mapping
ACCOUNT_SHEET_MAPPINGS: Dict[int, AccountSheetMapping] = {
    # VPS 1 - Accounts 1-6
    1: AccountSheetMapping(
        account_id=1,
        ebay_username="seller_prime_001", 
        vps_id=1,
        browser_profile="hidemyacc_profile_001",
        browser_type="hidemyacc",
        google_sheet_id="1A2B3C4D5E6F7G8H9I0J1K2L3M4N5O6P7Q8R9S0T",
        sheet_name="EbayAccount_001_seller_prime_001_VPS1",
        collection_schedule=["08:00", "14:00"]
    ),
    2: AccountSheetMapping(
        account_id=2,
        ebay_username="powerstore_002",
        vps_id=1, 
        browser_profile="hidemyacc_profile_002",
        browser_type="hidemyacc",
        google_sheet_id="2B3C4D5E6F7G8H9I0J1K2L3M4N5O6P7Q8R9S0T1U2V",
        sheet_name="EbayAccount_002_powerstore_002_VPS1",
        collection_schedule=["08:00", "14:00"]
    ),
    3: AccountSheetMapping(
        account_id=3,
        ebay_username="megadeals_003",
        vps_id=1,
        browser_profile="multilogin_profile_003", 
        browser_type="multilogin",
        google_sheet_id="3C4D5E6F7G8H9I0J1K2L3M4N5O6P7Q8R9S0T1U2V3W",
        sheet_name="EbayAccount_003_megadeals_003_VPS1",
        collection_schedule=["08:00", "14:00"]
    ),
    4: AccountSheetMapping(
        account_id=4,
        ebay_username="topbargains_004",
        vps_id=1,
        browser_profile="multilogin_profile_004",
        browser_type="multilogin", 
        google_sheet_id="4D5E6F7G8H9I0J1K2L3M4N5O6P7Q8R9S0T1U2V3W4X",
        sheet_name="EbayAccount_004_topbargains_004_VPS1",
        collection_schedule=["08:00", "14:00"]
    ),
    5: AccountSheetMapping(
        account_id=5,
        ebay_username="quickseller_005",
        vps_id=1,
        browser_profile="multilogin_profile_005",
        browser_type="multilogin",
        google_sheet_id="5E6F7G8H9I0J1K2L3M4N5O6P7Q8R9S0T1U2V3W4X5Y",
        sheet_name="EbayAccount_005_quickseller_005_VPS1", 
        collection_schedule=["08:00", "14:00"]
    ),
    6: AccountSheetMapping(
        account_id=6,
        ebay_username="elitestore_006",
        vps_id=1,
        browser_profile="multilogin_profile_006",
        browser_type="multilogin",
        google_sheet_id="6F7G8H9I0J1K2L3M4N5O6P7Q8R9S0T1U2V3W4X5Y6Z",
        sheet_name="EbayAccount_006_elitestore_006_VPS1",
        collection_schedule=["08:00", "14:00"]
    ),
    
    # VPS 2 - Accounts 7-12
    7: AccountSheetMapping(
        account_id=7,
        ebay_username="smartseller_007",
        vps_id=2,
        browser_profile="hidemyacc_profile_007",
        browser_type="hidemyacc",
        google_sheet_id="7G8H9I0J1K2L3M4N5O6P7Q8R9S0T1U2V3W4X5Y6Z7A",
        sheet_name="EbayAccount_007_smartseller_007_VPS2",
        collection_schedule=["08:00", "14:00"]
    ),
    8: AccountSheetMapping(
        account_id=8,
        ebay_username="fasttrack_008",
        vps_id=2,
        browser_profile="hidemyacc_profile_008", 
        browser_type="hidemyacc",
        google_sheet_id="8H9I0J1K2L3M4N5O6P7Q8R9S0T1U2V3W4X5Y6Z7A8B",
        sheet_name="EbayAccount_008_fasttrack_008_VPS2",
        collection_schedule=["08:00", "14:00"]
    ),
    9: AccountSheetMapping(
        account_id=9,
        ebay_username="prodealer_009",
        vps_id=2,
        browser_profile="multilogin_profile_009",
        browser_type="multilogin",
        google_sheet_id="9I0J1K2L3M4N5O6P7Q8R9S0T1U2V3W4X5Y6Z7A8B9C",
        sheet_name="EbayAccount_009_prodealer_009_VPS2",
        collection_schedule=["08:00", "14:00"]
    ),
    10: AccountSheetMapping(
        account_id=10,
        ebay_username="maxstore_010",
        vps_id=2,
        browser_profile="multilogin_profile_010",
        browser_type="multilogin",
        google_sheet_id="0J1K2L3M4N5O6P7Q8R9S0T1U2V3W4X5Y6Z7A8B9C0D",
        sheet_name="EbayAccount_010_maxstore_010_VPS2",
        collection_schedule=["08:00", "14:00"]
    ),
    11: AccountSheetMapping(
        account_id=11,
        ebay_username="superseller_011", 
        vps_id=2,
        browser_profile="multilogin_profile_011",
        browser_type="multilogin",
        google_sheet_id="1K2L3M4N5O6P7Q8R9S0T1U2V3W4X5Y6Z7A8B9C0D1E",
        sheet_name="EbayAccount_011_superseller_011_VPS2",
        collection_schedule=["08:00", "14:00"]
    ),
    12: AccountSheetMapping(
        account_id=12,
        ebay_username="topchoice_012",
        vps_id=2,
        browser_profile="multilogin_profile_012",
        browser_type="multilogin",
        google_sheet_id="2L3M4N5O6P7Q8R9S0T1U2V3W4X5Y6Z7A8B9C0D1E2F",
        sheet_name="EbayAccount_012_topchoice_012_VPS2",
        collection_schedule=["08:00", "14:00"]
    ),
    
    # VPS 3 - Accounts 13-18
    13: AccountSheetMapping(
        account_id=13,
        ebay_username="golddeals_013",
        vps_id=3,
        browser_profile="hidemyacc_profile_013",
        browser_type="hidemyacc",
        google_sheet_id="3M4N5O6P7Q8R9S0T1U2V3W4X5Y6Z7A8B9C0D1E2F3G",
        sheet_name="EbayAccount_013_golddeals_013_VPS3",
        collection_schedule=["08:00", "14:00"]
    ),
    14: AccountSheetMapping(
        account_id=14,
        ebay_username="flexstore_014",
        vps_id=3,
        browser_profile="hidemyacc_profile_014",
        browser_type="hidemyacc",
        google_sheet_id="4N5O6P7Q8R9S0T1U2V3W4X5Y6Z7A8B9C0D1E2F3G4H",
        sheet_name="EbayAccount_014_flexstore_014_VPS3",
        collection_schedule=["08:00", "14:00"]
    ),
    15: AccountSheetMapping(
        account_id=15,
        ebay_username="powerstore_015",
        vps_id=3,
        browser_profile="multilogin_profile_015",
        browser_type="multilogin",
        google_sheet_id="5O6P7Q8R9S0T1U2V3W4X5Y6Z7A8B9C0D1E2F3G4H5I",
        sheet_name="EbayAccount_015_powerstore_015_VPS3",
        collection_schedule=["08:00", "14:00"]
    ),
    16: AccountSheetMapping(
        account_id=16,
        ebay_username="titandeals_016",
        vps_id=3,
        browser_profile="multilogin_profile_016",
        browser_type="multilogin",
        google_sheet_id="6P7Q8R9S0T1U2V3W4X5Y6Z7A8B9C0D1E2F3G4H5I6J",
        sheet_name="EbayAccount_016_titandeals_016_VPS3",
        collection_schedule=["08:00", "14:00"]
    ),
    17: AccountSheetMapping(
        account_id=17,
        ebay_username="megaseller_017",
        vps_id=3,
        browser_profile="multilogin_profile_017",
        browser_type="multilogin",
        google_sheet_id="7Q8R9S0T1U2V3W4X5Y6Z7A8B9C0D1E2F3G4H5I6J7K",
        sheet_name="EbayAccount_017_megaseller_017_VPS3",
        collection_schedule=["08:00", "14:00"]
    ),
    18: AccountSheetMapping(
        account_id=18,
        ebay_username="ultrapro_018",
        vps_id=3,
        browser_profile="multilogin_profile_018", 
        browser_type="multilogin",
        google_sheet_id="8R9S0T1U2V3W4X5Y6Z7A8B9C0D1E2F3G4H5I6J7K8L",
        sheet_name="EbayAccount_018_ultrapro_018_VPS3",
        collection_schedule=["08:00", "14:00"]
    ),
    
    # VPS 4 - Accounts 19-24
    19: AccountSheetMapping(
        account_id=19,
        ebay_username="premiumstore_019",
        vps_id=4,
        browser_profile="hidemyacc_profile_019",
        browser_type="hidemyacc",
        google_sheet_id="9S0T1U2V3W4X5Y6Z7A8B9C0D1E2F3G4H5I6J7K8L9M",
        sheet_name="EbayAccount_019_premiumstore_019_VPS4",
        collection_schedule=["08:00", "14:00"]
    ),
    20: AccountSheetMapping(
        account_id=20,
        ebay_username="lightning_020",
        vps_id=4,
        browser_profile="hidemyacc_profile_020",
        browser_type="hidemyacc",
        google_sheet_id="0T1U2V3W4X5Y6Z7A8B9C0D1E2F3G4H5I6J7K8L9M0N",
        sheet_name="EbayAccount_020_lightning_020_VPS4",
        collection_schedule=["08:00", "14:00"]
    ),
    21: AccountSheetMapping(
        account_id=21,
        ebay_username="diamondstore_021",
        vps_id=4,
        browser_profile="multilogin_profile_021",
        browser_type="multilogin",
        google_sheet_id="1U2V3W4X5Y6Z7A8B9C0D1E2F3G4H5I6J7K8L9M0N1O",
        sheet_name="EbayAccount_021_diamondstore_021_VPS4",
        collection_schedule=["08:00", "14:00"]
    ),
    22: AccountSheetMapping(
        account_id=22,
        ebay_username="protrader_022",
        vps_id=4,
        browser_profile="multilogin_profile_022",
        browser_type="multilogin",
        google_sheet_id="2V3W4X5Y6Z7A8B9C0D1E2F3G4H5I6J7K8L9M0N1O2P",
        sheet_name="EbayAccount_022_protrader_022_VPS4",
        collection_schedule=["08:00", "14:00"]
    ),
    23: AccountSheetMapping(
        account_id=23,
        ebay_username="speedseller_023",
        vps_id=4,
        browser_profile="multilogin_profile_023",
        browser_type="multilogin",
        google_sheet_id="3W4X5Y6Z7A8B9C0D1E2F3G4H5I6J7K8L9M0N1O2P3Q",
        sheet_name="EbayAccount_023_speedseller_023_VPS4",
        collection_schedule=["08:00", "14:00"]
    ),
    24: AccountSheetMapping(
        account_id=24,
        ebay_username="elitepro_024",
        vps_id=4,
        browser_profile="multilogin_profile_024",
        browser_type="multilogin",
        google_sheet_id="4X5Y6Z7A8B9C0D1E2F3G4H5I6J7K8L9M0N1O2P3Q4R",
        sheet_name="EbayAccount_024_elitepro_024_VPS4",
        collection_schedule=["08:00", "14:00"]
    ),
    
    # VPS 5 - Accounts 25-30
    25: AccountSheetMapping(
        account_id=25,
        ebay_username="maxpro_025",
        vps_id=5,
        browser_profile="hidemyacc_profile_025",
        browser_type="hidemyacc",
        google_sheet_id="5Y6Z7A8B9C0D1E2F3G4H5I6J7K8L9M0N1O2P3Q4R5S",
        sheet_name="EbayAccount_025_maxpro_025_VPS5",
        collection_schedule=["08:00", "14:00"]
    ),
    26: AccountSheetMapping(
        account_id=26,
        ebay_username="ultradeals_026",
        vps_id=5,
        browser_profile="hidemyacc_profile_026",
        browser_type="hidemyacc",
        google_sheet_id="6Z7A8B9C0D1E2F3G4H5I6J7K8L9M0N1O2P3Q4R5S6T",
        sheet_name="EbayAccount_026_ultradeals_026_VPS5",
        collection_schedule=["08:00", "14:00"]
    ),
    27: AccountSheetMapping(
        account_id=27,
        ebay_username="toptrader_027",
        vps_id=5,
        browser_profile="multilogin_profile_027",
        browser_type="multilogin",
        google_sheet_id="7A8B9C0D1E2F3G4H5I6J7K8L9M0N1O2P3Q4R5S6T7U",
        sheet_name="EbayAccount_027_toptrader_027_VPS5",
        collection_schedule=["08:00", "14:00"]
    ),
    28: AccountSheetMapping(
        account_id=28,
        ebay_username="giantstore_028",
        vps_id=5,
        browser_profile="multilogin_profile_028",
        browser_type="multilogin",
        google_sheet_id="8B9C0D1E2F3G4H5I6J7K8L9M0N1O2P3Q4R5S6T7U8V",
        sheet_name="EbayAccount_028_giantstore_028_VPS5",
        collection_schedule=["08:00", "14:00"]
    ),
    29: AccountSheetMapping(
        account_id=29,
        ebay_username="kingdealer_029",
        vps_id=5,
        browser_profile="multilogin_profile_029",
        browser_type="multilogin",
        google_sheet_id="9C0D1E2F3G4H5I6J7K8L9M0N1O2P3Q4R5S6T7U8V9W",
        sheet_name="EbayAccount_029_kingdealer_029_VPS5",
        collection_schedule=["08:00", "14:00"]
    ),
    30: AccountSheetMapping(
        account_id=30,
        ebay_username="supremestore_030",
        vps_id=5,
        browser_profile="multilogin_profile_030",
        browser_type="multilogin",
        google_sheet_id="0D1E2F3G4H5I6J7K8L9M0N1O2P3Q4R5S6T7U8V9W0X",
        sheet_name="EbayAccount_030_supremestore_030_VPS5",
        collection_schedule=["08:00", "14:00"]
    )
}


# VPS Distribution Configuration
VPS_CONFIGURATIONS = {
    1: {
        "server_ip": "192.168.1.101",
        "accounts": [1, 2, 3, 4, 5, 6],
        "hidemyacc_accounts": [1, 2],
        "multilogin_accounts": [3, 4, 5, 6],
        "total_accounts": 6
    },
    2: {
        "server_ip": "192.168.1.102", 
        "accounts": [7, 8, 9, 10, 11, 12],
        "hidemyacc_accounts": [7, 8],
        "multilogin_accounts": [9, 10, 11, 12],
        "total_accounts": 6
    },
    3: {
        "server_ip": "192.168.1.103",
        "accounts": [13, 14, 15, 16, 17, 18],
        "hidemyacc_accounts": [13, 14],
        "multilogin_accounts": [15, 16, 17, 18],
        "total_accounts": 6
    },
    4: {
        "server_ip": "192.168.1.104",
        "accounts": [19, 20, 21, 22, 23, 24],
        "hidemyacc_accounts": [19, 20],
        "multilogin_accounts": [21, 22, 23, 24],
        "total_accounts": 6
    },
    5: {
        "server_ip": "192.168.1.105",
        "accounts": [25, 26, 27, 28, 29, 30],
        "hidemyacc_accounts": [25, 26],
        "multilogin_accounts": [27, 28, 29, 30], 
        "total_accounts": 6
    }
}


# Helper Functions
def get_account_config(account_id: int) -> AccountSheetMapping:
    """Get complete configuration for specific account"""
    return ACCOUNT_SHEET_MAPPINGS.get(account_id)


def get_vps_accounts(vps_id: int) -> List[int]:
    """Get all account IDs assigned to specific VPS"""
    return VPS_CONFIGURATIONS.get(vps_id, {}).get("accounts", [])


def get_sheet_id(account_id: int) -> str:
    """Get Google Sheet ID for specific account"""
    config = ACCOUNT_SHEET_MAPPINGS.get(account_id)
    return config.google_sheet_id if config else None


def get_all_sheet_ids() -> List[str]:
    """Get all Google Sheet IDs for batch operations"""
    return [config.google_sheet_id for config in ACCOUNT_SHEET_MAPPINGS.values()]


def get_accounts_by_browser_type(browser_type: str) -> List[int]:
    """Get all accounts using specific browser type"""
    return [
        account_id for account_id, config in ACCOUNT_SHEET_MAPPINGS.items()
        if config.browser_type == browser_type
    ]


def get_accounts_by_vps(vps_id: int) -> List[AccountSheetMapping]:
    """Get all account configurations for specific VPS"""
    return [
        config for config in ACCOUNT_SHEET_MAPPINGS.values()
        if config.vps_id == vps_id
    ]


def validate_account_mapping() -> Dict[str, Any]:
    """Validate complete account mapping configuration"""
    validation_result = {
        "valid": True,
        "errors": [],
        "stats": {
            "total_accounts": len(ACCOUNT_SHEET_MAPPINGS),
            "total_vps": len(VPS_CONFIGURATIONS),
            "hidemyacc_profiles": 0,
            "multilogin_profiles": 0,
            "unique_sheet_ids": 0
        }
    }
    
    # Check account count
    if len(ACCOUNT_SHEET_MAPPINGS) != 30:
        validation_result["errors"].append(f"Expected 30 accounts, found {len(ACCOUNT_SHEET_MAPPINGS)}")
        validation_result["valid"] = False
    
    # Check VPS distribution
    total_vps_accounts = sum(len(config["accounts"]) for config in VPS_CONFIGURATIONS.values())
    if total_vps_accounts != 30:
        validation_result["errors"].append(f"VPS accounts total should be 30, found {total_vps_accounts}")
        validation_result["valid"] = False
    
    # Check unique sheet IDs
    sheet_ids = [config.google_sheet_id for config in ACCOUNT_SHEET_MAPPINGS.values()]
    if len(set(sheet_ids)) != 30:
        validation_result["errors"].append("All sheet IDs must be unique")
        validation_result["valid"] = False
    
    # Count browser profiles
    hidemyacc_count = len(get_accounts_by_browser_type("hidemyacc"))
    multilogin_count = len(get_accounts_by_browser_type("multilogin"))
    
    validation_result["stats"]["hidemyacc_profiles"] = hidemyacc_count
    validation_result["stats"]["multilogin_profiles"] = multilogin_count
    validation_result["stats"]["unique_sheet_ids"] = len(set(sheet_ids))
    
    # Expected distribution: 10 Hidemyacc + 20 Multilogin
    if hidemyacc_count != 10:
        validation_result["errors"].append(f"Expected 10 Hidemyacc profiles, found {hidemyacc_count}")
        validation_result["valid"] = False
    
    if multilogin_count != 20:
        validation_result["errors"].append(f"Expected 20 Multilogin profiles, found {multilogin_count}")
        validation_result["valid"] = False
    
    return validation_result


# Chrome Extension Configuration
EXTENSION_CONFIG = {
    "version": "2.0.0",
    "api_endpoints": {
        "sync_data": "/api/v1/multi-sheet/sync-data",
        "account_status": "/api/v1/multi-sheet/account-status", 
        "collection_trigger": "/api/v1/multi-sheet/collect"
    },
    "collection_settings": {
        "concurrent_accounts": 10,
        "retry_attempts": 3,
        "timeout_seconds": 30,
        "batch_size": 100
    }
}


if __name__ == "__main__":
    # Validate configuration when run directly
    result = validate_account_mapping()
    print("🔧 Account Mapping Configuration Validation:")
    print(f"✅ Valid: {result['valid']}")
    print(f"📊 Stats: {result['stats']}")
    
    if not result['valid']:
        print("❌ Errors:")
        for error in result['errors']:
            print(f"   - {error}")
    else:
        print("🎉 All 30 accounts properly configured!")