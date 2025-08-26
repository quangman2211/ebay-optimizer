# 📊 Google Sheets Configuration Registry

## 🎯 **Overview**
This document contains the configuration and registry of all Google Sheets used in the eBay Optimizer system. All sheets have been configured with the Google service account email for seamless integration.

---

## 📋 **eBay Account Sheets**

### 1. eBay_Sync_seller_pro_2025
- **Sheet ID**: `1Qx-G5SwGgr6F4deeHyI_zPEJbmAr3beG-wwNhfn1hmM`
- **Purpose**: Production eBay seller account
- **Type**: Primary Production Account
- **Status**: ✅ Active
- **Data Types**: Orders, Listings, Messages
- **Sync Frequency**: Real-time via Chrome Extension
- **Access**: Google service account added as Editor
- **URL**: https://docs.google.com/spreadsheets/d/1Qx-G5SwGgr6F4deeHyI_zPEJbmAr3beG-wwNhfn1hmM/

### 2. eBay_Sync_test_api_account  
- **Sheet ID**: `1GukktcwMSw4QASjVYpZLiNpkgMgGvZZ3Jkotiq6ki0c`
- **Purpose**: eBay API testing account
- **Type**: API Testing Account
- **Status**: ✅ Active
- **Data Types**: Orders, Listings (Test Data)
- **Sync Frequency**: Manual/Automated testing
- **Access**: Google service account added as Editor
- **URL**: https://docs.google.com/spreadsheets/d/1GukktcwMSw4QASjVYpZLiNpkgMgGvZZ3Jkotiq6ki0c/

### 3. eBay_Sync_test_workspace_account
- **Sheet ID**: `1I5IbaSGRY4tNr4j3HhXi38yj6Q2iOCCcFkyondG7YII`
- **Purpose**: eBay workspace testing account  
- **Type**: Workspace Testing Account
- **Status**: ✅ Active
- **Data Types**: Orders, Listings (Workspace Testing)
- **Sync Frequency**: Development testing
- **Access**: Google service account added as Editor
- **URL**: https://docs.google.com/spreadsheets/d/1I5IbaSGRY4tNr4j3HhXi38yj6Q2iOCCcFkyondG7YII/

---

## 🗄️ **System Support Sheets**

### 4. Backup_Data_Archive
- **Sheet ID**: `1XuJ1luqawfmrXN5SF4B8U4-Pwvix64abWtNOm7razOY`
- **Purpose**: Data backup and archive storage
- **Type**: Backup System
- **Status**: ✅ Active
- **Data Types**: Archived Orders, Listings, System Backups
- **Sync Frequency**: Daily automated backup
- **Access**: Google service account added as Editor
- **URL**: https://docs.google.com/spreadsheets/d/1XuJ1luqawfmrXN5SF4B8U4-Pwvix64abWtNOm7razOY/

### 5. Product_Manager_Shared
- **Sheet ID**: `1Lp0BZnpbgpjoCHoRkHbtGwmblkDlwwcuUXy_QsPZ2wo`
- **Purpose**: Shared product management data
- **Type**: Product Management
- **Status**: ✅ Active
- **Data Types**: Product Info, Inventory, Supplier Data
- **Sync Frequency**: Real-time collaboration
- **Access**: Google service account added as Editor
- **URL**: https://docs.google.com/spreadsheets/d/1Lp0BZnpbgpjoCHoRkHbtGwmblkDlwwcuUXy_QsPZ2wo/

---

## 🔧 **Technical Configuration**

### Chrome Extension Mapping
```javascript
const SHEET_ACCOUNTS = {
  'seller_pro_2025': {
    sheetId: '1Qx-G5SwGgr6F4deeHyI_zPEJbmAr3beG-wwNhfn1hmM',
    accountName: 'eBay Seller Pro 2025',
    type: 'production'
  },
  'test_api_account': {
    sheetId: '1GukktcwMSw4QASjVYpZLiNpkgMgGvZZ3Jkotiq6ki0c',
    accountName: 'Test API Account',
    type: 'testing'
  },
  'test_workspace_account': {
    sheetId: '1I5IbaSGRY4tNr4j3HhXi38yj6Q2iOCCcFkyondG7YII',
    accountName: 'Test Workspace Account', 
    type: 'testing'
  }
};
```

### Backend API Configuration
```python
GOOGLE_SHEETS_CONFIG = {
    "seller_pro_2025": "1Qx-G5SwGgr6F4deeHyI_zPEJbmAr3beG-wwNhfn1hmM",
    "test_api_account": "1GukktcwMSw4QASjVYpZLiNpkgMgGvZZ3Jkotiq6ki0c", 
    "test_workspace_account": "1I5IbaSGRY4tNr4j3HhXi38yj6Q2iOCCcFkyondG7YII",
    "backup_archive": "1XuJ1luqawfmrXN5SF4B8U4-Pwvix64abWtNOm7razOY",
    "product_manager": "1Lp0BZnpbgpjoCHoRkHbtGwmblkDlwwcuUXy_QsPZ2wo"
}
```

### Account to Sheet Mapping
| Account ID | Account Name | Sheet ID | Sheet Name |
|------------|--------------|----------|------------|
| 1 | seller_pro_2025 | 1Qx-G5SwGgr6F4deeHyI_zPEJbmAr3beG-wwNhfn1hmM | eBay_Sync_seller_pro_2025 |
| 2 | test_api_account | 1GukktcwMSw4QASjVYpZLiNpkgMgGvZZ3Jkotiq6ki0c | eBay_Sync_test_api_account |
| 3 | test_workspace_account | 1I5IbaSGRY4tNr4j3HhXi38yj6Q2iOCCcFkyondG7YII | eBay_Sync_test_workspace_account |

---

## 📐 **Sheet Structure Standards**

### Orders Sheet Structure
| Column | Field | Type | Description |
|--------|-------|------|-------------|
| A | Sales Record # | String | eBay sales record number |
| B | Order Number | String | eBay order number (unique) |
| C | Buyer Username | String | eBay buyer username |
| D | Buyer Name | String | Full buyer name |
| E | Buyer Email | String | Buyer email address |
| F | Item Number | String | eBay item number |
| G | Item Title | Text | Product title |
| H | Custom Label | String | SKU/Custom label |
| I | Quantity | Number | Quantity ordered |
| J | Sold For | Currency | Item price |
| K | Total Price | Currency | Total order amount |
| L | Sale Date | Date | Date of sale |
| M | Paid Date | Date | Payment date |
| N | Ship By Date | Date | Required shipping date |
| O | Tracking Number | String | Shipping tracking |
| P | Status | String | Order status |
| Q | Account | String | Account identifier |
| R | Last Updated | DateTime | Last sync timestamp |

### Listings Sheet Structure
| Column | Field | Type | Description |
|--------|-------|------|-------------|
| A | Item Number | String | eBay item number (unique) |
| B | Title | Text | Listing title |
| C | Custom Label | String | SKU/Custom label |
| D | Available Qty | Number | Available quantity |
| E | Current Price | Currency | Current listing price |
| F | Sold Qty | Number | Quantity sold |
| G | Watchers | Number | Number of watchers |
| H | Start Date | DateTime | Listing start date |
| I | End Date | DateTime | Listing end date |
| J | Condition | String | Item condition |
| K | Status | String | Listing status |
| L | Account | String | Account identifier |
| M | Last Updated | DateTime | Last sync timestamp |

---

## 🔐 **Security & Access Control**

### Service Account Configuration
- **Service Account Email**: `[YOUR_SERVICE_ACCOUNT]@[PROJECT_ID].iam.gserviceaccount.com`
- **Permissions**: Editor access on all 5 sheets
- **Scopes Required**:
  - `https://www.googleapis.com/auth/spreadsheets`
  - `https://www.googleapis.com/auth/drive.file`

### OAuth2 Configuration (Chrome Extension)
- **Client ID**: `946607089490-qm9r863k47vqb1sf158atanlb6h74231.apps.googleusercontent.com`
- **Set in**: `ChromeExtension/v2/manifest.json` line 27
- **Scopes**: Same as service account
- **Redirect URI**: Chrome extension callback
- **Created**: August 25, 2025
- **Status**: ✅ Active & Ready for Use

### Security Best Practices
- ✅ All sheets configured with service account access
- ✅ Limited scope permissions (spreadsheets + drive.file only)
- ✅ No public access - authenticated users only
- ✅ Regular access review and cleanup
- ⚠️ Monitor API quotas and usage limits

---

## 🔄 **Sync Configuration**

### Real-time Sync (Chrome Extension)
- **Trigger**: CSV download detection
- **Process**: CSV → Parse → Transform → Sheets API
- **Target Sheets**: Account-specific sheets (1-3)
- **Error Handling**: Retry logic + error logging

### Batch Sync (Backend API)
- **Frequency**: Every 5 minutes (configurable)
- **Process**: Sheets API → Validate → Database
- **Source Sheets**: All account sheets + backup
- **Conflict Resolution**: Timestamp-based merge

### Backup Sync
- **Frequency**: Daily at 2:00 AM UTC
- **Process**: Database → Transform → Backup sheet
- **Target**: Backup_Data_Archive sheet
- **Retention**: 90 days of historical data

---

## 🛠️ **Maintenance Procedures**

### Adding New eBay Account Sheet
1. Create new Google Sheet
2. Set up standard sheet structure (Orders/Listings tabs)
3. Add service account email as Editor
4. Update Chrome Extension configuration
5. Update Backend API mapping
6. Add to this documentation
7. Test sync functionality

### Sheet Health Monitoring
- **Daily**: Check sync timestamps
- **Weekly**: Validate data integrity
- **Monthly**: Review access permissions
- **Quarterly**: Audit and cleanup unused sheets

### Troubleshooting Common Issues

#### Issue: Sync Failures
**Check**: 
1. Service account permissions
2. API quotas (100 requests/100 seconds/user)
3. Sheet structure matches expected format
4. Network connectivity

#### Issue: Data Validation Errors
**Check**:
1. Required fields are populated
2. Data types match expected format
3. Duplicate detection logic
4. Field length limits

#### Issue: Permission Denied
**Check**:
1. Service account email in sheet sharing
2. OAuth2 token validity (Chrome Extension)
3. Scopes configuration
4. API key restrictions

---

## 📊 **Usage Statistics & Monitoring**

### Key Metrics to Track
- **Sync Success Rate**: >95% target
- **API Quota Usage**: <80% daily limit
- **Data Processing Time**: <30s per CSV
- **Error Rate**: <5% of operations
- **Sheet Write Latency**: <2s average

### Monitoring Setup
- Backend API logs
- Chrome Extension telemetry  
- Google Sheets API usage dashboards
- Error notification webhooks

---

## 🚀 **Future Enhancements**

### Planned Improvements
1. **Multi-Region Support**: Additional backup sheets
2. **Advanced Validation**: Real-time data quality checks
3. **Performance Optimization**: Batch operations
4. **Enhanced Security**: Row-level permissions
5. **Analytics Integration**: BigQuery export

### Sheet Versioning
- **Current Version**: 1.0
- **Migration Path**: Documented in separate guide
- **Backward Compatibility**: Maintained for 2 versions

---

## 📝 **Change Log**

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-08-25 | 1.0 | Initial configuration setup | Claude Code |

---

## 💡 **Tips & Best Practices**

1. **Performance**: Use batch operations when possible
2. **Reliability**: Always validate data before writing
3. **Security**: Regular permission audits
4. **Monitoring**: Set up alerts for sync failures
5. **Documentation**: Keep this file updated with changes

---

*Last Updated: August 25, 2025*  
*Maintainer: eBay Optimizer Development Team*