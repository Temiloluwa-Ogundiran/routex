# X-Aggregator Test Suite

This directory contains comprehensive unit tests for the X-Aggregator payment system, with a focus on wallet integration.

## Test Coverage

### 1. Wallet Service Tests (`test_wallet_service.py`)
Tests for core wallet service functions:
- ✅ Payin charge calculation
- ✅ Payout charge calculation
- ✅ Wallet creation (get_or_create)
- ✅ Credit/debit operations
- ✅ Balance validation
- ✅ Wallet transfers
- ✅ Insufficient balance handling

### 2. Wallet API Endpoint Tests (`test_wallet_endpoints.py`)
Tests for wallet management endpoints:
- ✅ GET /wallets - List merchant wallets
- ✅ GET /wallets/by-criteria - Multi-currency filter
- ✅ GET /wallets/{wallet_id} - Get specific wallet
- ✅ POST /wallets/create - Create new wallet
- ✅ PATCH /wallets/{wallet_id}/charges - Update charges
- ✅ PATCH /wallets/{wallet_id}/toggle-active - Toggle status
- ✅ GET /wallets/balance/summary - Balance summary
- ✅ Authorization checks

### 3. V1 API Tests (`test_v1_api.py`)
Tests for V1 payment API endpoints:
- ✅ POST /api/v1/payout - Payout with wallet charges
- ✅ POST /api/v1/initiate - Transaction initialization
- ✅ GET /api/v1/transactions/verify - Transaction verification
- ✅ Wallet validation
- ✅ Insufficient balance scenarios
- ✅ Duplicate reference handling

### 4. Transaction Endpoint Tests (`test_transaction_endpoints.py`)
Tests for wallet-aware transaction endpoints:
- ✅ GET /wallet-transactions - Transactions by wallet
- ✅ GET /wallet-transaction-stats - Wallet statistics
- ✅ GET /merchant-transactions-by-wallet - Grouped by wallet
- ✅ GET /merchant-transactions - With wallet filter
- ✅ Payout with wallet integration
- ✅ Webhook handlers (payin/payout)
- ✅ Transaction-wallet linking

## Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install pytest pytest-asyncio httpx
```

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_wallet_service.py
```

### Run Specific Test Class

```bash
pytest tests/test_wallet_service.py::TestWalletService
```

### Run Specific Test

```bash
pytest tests/test_wallet_service.py::TestWalletService::test_get_payin_charge
```

### Run with Coverage

```bash
pytest --cov=. --cov-report=html
```

Then open `htmlcov/index.html` in your browser to view the coverage report.

### Run Tests in Parallel

```bash
pip install pytest-xdist
pytest -n auto
```

### Run with Verbose Output

```bash
pytest -v
```

### Run Only Fast Tests

```bash
pytest -m "not slow"
```

## Test Structure

```
tests/
├── __init__.py              # Test package initialization
├── conftest.py             # Shared fixtures and configuration
├── test_wallet_service.py  # Wallet service unit tests
├── test_wallet_endpoints.py # Wallet API endpoint tests
├── test_v1_api.py          # V1 API endpoint tests
├── test_transaction_endpoints.py # Transaction endpoint tests
└── README.md               # This file
```

## Fixtures

Common fixtures are defined in `conftest.py`:

- `async_engine` - Test database engine
- `async_session` - Test database session
- `client` - Test HTTP client
- `test_merchant` - Sample merchant
- `test_user` - Sample user
- `test_wallet` - Sample wallet with test charges
- `test_customer` - Sample customer

## Mocking

Tests use `unittest.mock` to mock external dependencies:

- External API calls (Kora, Paystack)
- Service layer functions
- Authentication/authorization

## Key Test Scenarios

### Wallet Charge Calculations
```python
# Payin: flat_charge + (percentage_charge * amount) / 100
# Example: 100 + (1.5 * 1000) / 100 = 115

# Payout: payout_flat_charge + (payout_percentage_charge * amount) / 100
# Example: 50 + (1.0 * 1000) / 100 = 60
```

### Wallet Balance Validation
- ✅ Sufficient balance → Transaction proceeds
- ❌ Insufficient balance → HTTP 400 error
- ✅ Balance updated after credit/debit

### Transaction-Wallet Linking
- All transactions must have `wallet_id` set
- Charges calculated from wallet configuration
- Balance updates reflected in wallet

## Continuous Integration

Add to your CI/CD pipeline:

```yaml
# GitHub Actions example
- name: Run tests
  run: |
    pip install -r requirements.txt
    pip install pytest pytest-asyncio httpx
    pytest
```

## Troubleshooting

### Import Errors
Ensure you're running pytest from the project root:
```bash
cd c:\Users\user\Desktop\x-aggregator
pytest
```

### Database Errors
Tests use an in-memory SQLite database. If you encounter errors:
```bash
rm test.db  # Remove any existing test database
pytest
```

### Async Errors
Ensure `pytest-asyncio` is installed:
```bash
pip install pytest-asyncio
```

## Contributing

When adding new features:
1. Write tests first (TDD approach)
2. Ensure all tests pass
3. Maintain test coverage above 80%
4. Update this README with new test descriptions

## Future Enhancements

- [ ] Integration tests with real database
- [ ] End-to-end tests for payment flows
- [ ] Load testing for high-volume scenarios
- [ ] Mock webhook delivery tests
- [ ] Performance benchmarking
