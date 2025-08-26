# eBay Optimizer - Quy Tắc Dự Án (Project Rules)

## 📋 Nguyên Tắc Phát Triển

### 🏗️ Clean Architecture Principles
Dự án tuân thủ nghiêm ngặt các nguyên tắc Clean Code và SOLID:

#### SOLID Principles
- **S** - Single Responsibility: Mỗi class/module chỉ có một lý do để thay đổi
- **O** - Open/Closed: Mở cho việc mở rộng, đóng cho việc sửa đổi  
- **L** - Liskov Substitution: Các subclass phải thay thế được base class
- **I** - Interface Segregation: Không ép client phụ thuộc interface không dùng
- **D** - Dependency Inversion: Phụ thuộc vào abstraction, không phụ thuộc concrete

#### Domain-Driven Design
```
Domain Layer (Business Logic)
    ↓
Application Layer (Use Cases)  
    ↓
Infrastructure Layer (External Dependencies)
    ↓
Presentation Layer (API/UI)
```

## 🗂️ Cấu Trúc File & Naming Convention

### Backend Structure
```python
# Domain Models - Focused entities
/Webapp/backend/app/domain/models/
├── base.py          # BaseModel với common functionality
├── enums.py         # All enumerations  
├── user.py          # User & UserRole entities
├── account.py       # Account & AccountSheet entities
└── listing.py       # Listing & DraftListing entities

# Business Logic - Service layer
/Webapp/backend/app/services/
├── business/        # Domain services
├── infrastructure/  # External integrations
└── interfaces.py    # Service contracts
```

### Frontend Structure  
```javascript
// Component Organization
/Webapp/frontend/src/components/
├── Layout/          # Layout components (Sidebar, TopBar)
├── Dashboard/       # Dashboard widgets  
├── Modals/         # Modal components
└── [Feature]/      # Feature-specific components

// Service Layer
/Webapp/frontend/src/services/
├── api.js          # API client configuration
├── auth.js         # Authentication service
└── specialized/    # Feature-specific services
```

## 🎯 Code Quality Standards

### Python (Backend)
```python
# Type hints bắt buộc
def calculate_health_score(self) -> float:
    """Calculate account health based on multiple metrics"""
    
# Error handling đầy đủ
try:
    result = perform_operation()
except SpecificError as e:
    logger.error(f"Operation failed: {e}")
    raise ServiceError("User-friendly message")

# Docstrings cho tất cả public methods
class Account(BaseModel):
    """eBay Account entity with business logic encapsulation"""
    
    def is_active(self) -> bool:
        """Check if account is active and operational"""
```

### JavaScript (Frontend)
```javascript
// PropTypes bắt buộc cho tất cả components
StatsCard.propTypes = {
    title: PropTypes.string.isRequired,
    value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    icon: PropTypes.element,
    trend: PropTypes.object
};

// Error boundaries cho error handling
const ErrorBoundary = ({ children }) => {
    // Handle errors gracefully
};

// Consistent naming convention
const useAccountData = () => {
    // Custom hooks prefix with 'use'
};
```

## 🔒 Security Requirements

### Authentication & Authorization
```python
# JWT token validation bắt buộc
@jwt_required
async def protected_endpoint(current_user: User = Depends(get_current_user)):
    pass

# RBAC implementation  
@require_role([UserRoleEnum.ADMIN, UserRoleEnum.MANAGER])
async def admin_endpoint():
    pass
```

### Data Protection
- **Không log sensitive data** (passwords, tokens, personal info)
- **Environment variables** cho tất cả secrets
- **Input validation** bằng Pydantic models
- **SQL Injection prevention** via SQLAlchemy ORM

## 🧪 Testing Standards

### Test Coverage Requirements
- **Backend Unit Tests**: 95% coverage minimum
- **Frontend Components**: 80% coverage minimum  
- **API Integration**: 90% coverage minimum
- **E2E Critical Paths**: 100% coverage

### Test Structure
```python
# Backend testing
def test_account_health_score_calculation():
    """Test account health score business logic"""
    # Given
    account = Account(feedback_score=98, active_listings=100)
    
    # When  
    health_score = account.calculate_health_score()
    
    # Then
    assert health_score >= 70.0
```

```javascript
// Frontend testing
describe('StatsCard Component', () => {
    test('renders with required props', () => {
        const props = { title: 'Test', value: 100 };
        render(<StatsCard {...props} />);
        expect(screen.getByText('Test')).toBeInTheDocument();
    });
});
```

## 📊 Database Design Rules

### Model Design
```python
class Account(BaseModel):
    """Domain model với business logic encapsulation"""
    
    # Business methods trong model
    def calculate_health_score(self) -> float:
        """Business logic belongs in domain model"""
    
    def can_list_more_items(self) -> bool:
        """Domain rules encapsulated in entity"""
```

### Migration Guidelines
- **Backward compatible**: Không breaking changes
- **Descriptive names**: Clear migration descriptions
- **Rollback plan**: Mỗi migration phải có rollback strategy

## 🚀 Deployment Rules

### Environment Configuration
```bash
# Development
ENVIRONMENT=development
DEBUG=True
DATABASE_URL=sqlite:///ebay_optimizer.db

# Production  
ENVIRONMENT=production
DEBUG=False
DATABASE_URL=postgresql://...
```

### Docker Guidelines
- **Multi-stage builds** để optimize image size
- **Non-root user** trong container
- **Health checks** cho tất cả services
- **Resource limits** đặt rõ ràng

## 🔧 Development Workflow

### Git Workflow
```bash
# Feature development
git checkout -b feature/account-health-scoring
# Implement feature following SOLID principles
git commit -m "feat: implement account health scoring

- Add calculate_health_score method to Account entity
- Apply single responsibility principle
- Include comprehensive unit tests
- Update API documentation"
```

### Code Review Checklist
- ✅ SOLID principles compliance
- ✅ Type hints & documentation complete  
- ✅ Error handling implemented
- ✅ Tests written & passing
- ✅ Security considerations addressed
- ✅ Performance implications considered

## 📈 Performance Standards

### Backend Performance
- **API Response Time**: 95th percentile < 500ms
- **Database Queries**: N+1 query prevention
- **Memory Usage**: Monitor for memory leaks
- **Async Operations**: Use FastAPI async capabilities

### Frontend Performance  
- **Page Load**: < 3 seconds initial load
- **Bundle Size**: Monitor và optimize regularly
- **Code Splitting**: Lazy load non-critical components
- **Caching**: Implement appropriate caching strategies

## 🤖 Automation Standards

### Browser Profiles Management
```python
# Utilities/automation/browser_profile_manager.py
class BrowserProfileManager:
    """Manage 30 eBay accounts across 5 VPS"""
    
    def distribute_profiles(self) -> Dict[int, List[str]]:
        """Distribute profiles evenly across VPS servers"""
        # 6 profiles per VPS server
```

### Chrome Extension Guidelines
- **Manifest v2** compliance (for now)
- **Error handling** cho tất cả Google Sheets operations
- **Rate limiting** để tránh API quotas
- **Logging** comprehensive cho debugging

## 📚 Documentation Requirements

### Code Documentation
- **All public methods** phải có docstrings
- **API endpoints** documented với OpenAPI/Swagger
- **Architecture decisions** recorded trong ADR format
- **Setup instructions** comprehensive và accurate

### API Documentation
```python
@app.post("/api/v1/accounts", response_model=AccountResponse)
async def create_account(
    account_data: AccountCreate,
    current_user: User = Depends(get_current_user)
):
    """
    Create new eBay account
    
    Args:
        account_data: Account creation payload
        current_user: Authenticated user
        
    Returns:
        Created account with health metrics
        
    Raises:
        ValidationError: Invalid account data
        PermissionError: User lacks creation permissions
    """
```

## 🎯 Project-Specific Rules

### Multi-Account Architecture
- **30 eBay accounts** maximum per deployment
- **5 VPS servers** optimal distribution
- **6 accounts per VPS** for performance balance
- **Google Sheets 1:1** mapping với eBay accounts

### Data Flow Requirements
```
eBay → Chrome Extension → Google Sheets → WebApp Collector → SQLite → API → Frontend
```

### Integration Standards
- **Google Sheets API** rate limit compliance
- **eBay data structure** consistent mapping  
- **Error recovery** automatic retry mechanisms
- **Data validation** at every integration point

## 🔄 Maintenance & Updates

### Regular Maintenance Tasks
- **Database cleanup** monthly
- **Log rotation** weekly  
- **Security updates** immediate
- **Performance monitoring** daily
- **Backup verification** weekly

### Update Procedures
1. **Test in development** thoroughly
2. **Backup production data** before updates
3. **Rolling deployment** để minimize downtime
4. **Rollback plan** ready for quick recovery
5. **Monitor post-deployment** for issues

---

## 📞 Development Support

### Commands Reference
```bash
# Backend development
cd Webapp/backend
uvicorn app.main:app --reload

# Frontend development
cd Webapp/frontend  
npm start

# Testing
pytest Webapp/backend/tests/ -v
npm test

# Browser profiles
python Utilities/automation/browser_profile_manager.py --status
```

### Troubleshooting Resources
- **API Documentation**: http://localhost:8000/docs
- **Database Schema**: `/Webapp/backend/migrations/`
- **Error Logs**: `/logs/` directory
- **Health Monitoring**: Built-in endpoints

---

**Lưu ý**: Tất cả development phải tuân thủ các quy tắc này. Bất kỳ deviation nào cần phải có lý do rõ ràng và được document trong code comments.