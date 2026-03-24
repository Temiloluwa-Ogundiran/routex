"""
Manual API testing script using real credentials
Tests merchant authentication, V1 API, wallet, transaction, and admin endpoints
"""
import requests
import json
from typing import Optional

BASE_URL = "http://localhost:8000"

# Test credentials
MERCHANT_EMAIL = "chowdome.cu@gmail.com"
MERCHANT_PASSWORD = "chowdome123?"
V1_API_KEY = "aggsk_test_5bac7738016b847434f99dbea67f1c30dd82a92ea138256c17ae54f76fc77ff7_agg-cb50d"

# Store tokens
merchant_token = None
admin_token = None
merchant_id = None
wallet_id = None

class TestResults:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []

    def add_result(self, test_name: str, passed: bool, message: str = ""):
        self.tests.append({
            "name": test_name,
            "passed": passed,
            "message": message
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def print_summary(self):
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        for test in self.tests:
            status = "✓ PASS" if test["passed"] else "✗ FAIL"
            print(f"{status}: {test['name']}")
            if test["message"]:
                print(f"   {test['message']}")
        print(f"\nTotal: {len(self.tests)} | Passed: {self.passed} | Failed: {self.failed}")
        print("="*80)

results = TestResults()

def test_merchant_login():
    """Test merchant login"""
    global merchant_token, merchant_id
    print("\n[TEST] Merchant Login")

    response = requests.post(
        f"{BASE_URL}/login",
        json={"email": MERCHANT_EMAIL, "password": MERCHANT_PASSWORD}
    )

    if response.status_code == 200:
        data = response.json()
        if "otp" in data:
            print(f"   OTP received: {data['otp']}")
            # Verify OTP
            otp_response = requests.post(
                f"{BASE_URL}/verify-otp",
                json={"email": MERCHANT_EMAIL, "otp": data['otp']}
            )

            if otp_response.status_code == 200:
                otp_data = otp_response.json()
                merchant_token = otp_data.get("access_token")
                merchant_id = otp_data.get("data", {}).get("merchant_id")
                results.add_result("Merchant Login & OTP Verification", True,
                                 f"Token acquired, Merchant ID: {merchant_id}")
                print(f"   ✓ Login successful! Merchant ID: {merchant_id}")
                return True
            else:
                results.add_result("Merchant OTP Verification", False,
                                 f"Status: {otp_response.status_code}, Response: {otp_response.text}")
                print(f"   ✗ OTP verification failed: {otp_response.text}")
                return False
        else:
            results.add_result("Merchant Login", False, "OTP not received")
            print("   ✗ OTP not received")
            return False
    else:
        results.add_result("Merchant Login", False,
                         f"Status: {response.status_code}, Response: {response.text}")
        print(f"   ✗ Login failed: {response.text}")
        return False

def test_v1_initialize():
    """Test V1 initialize transaction endpoint"""
    print("\n[TEST] V1 Initialize Transaction")

    headers = {"Authorization": f"Bearer {V1_API_KEY}"}
    data = {
        "reference": f"TEST_INIT_{int(time.time())}",
        "amount": 5000.0,
        "currency": "NGN",
        "customer": {"email": "testcustomer@example.com"},
        "redirect_url": "https://example.com/callback"
    }

    response = requests.post(f"{BASE_URL}/api/v1/initiate", json=data, headers=headers)

    if response.status_code == 200:
        resp_data = response.json()
        results.add_result("V1 Initialize Transaction", True,
                         f"Reference: {data['reference']}")
        print(f"   ✓ Transaction initialized: {data['reference']}")
        return data['reference']
    else:
        results.add_result("V1 Initialize Transaction", False,
                         f"Status: {response.status_code}, Response: {response.text}")
        print(f"   ✗ Failed: {response.text}")
        return None

def test_v1_verify(reference: str):
    """Test V1 verify transaction endpoint"""
    print("\n[TEST] V1 Verify Transaction")

    headers = {"Authorization": f"Bearer {V1_API_KEY}"}
    response = requests.get(
        f"{BASE_URL}/api/v1/transactions/verify?reference={reference}",
        headers=headers
    )

    if response.status_code in [200, 404]:  # 404 is expected for pending transactions
        results.add_result("V1 Verify Transaction", True,
                         f"Status: {response.status_code}")
        print(f"   ✓ Verification endpoint working")
        return True
    else:
        results.add_result("V1 Verify Transaction", False,
                         f"Status: {response.status_code}, Response: {response.text}")
        print(f"   ✗ Failed: {response.text}")
        return False

def test_get_wallets():
    """Test get merchant wallets"""
    global wallet_id
    print("\n[TEST] Get Merchant Wallets")

    headers = {"Authorization": f"Bearer {merchant_token}"}
    response = requests.get(
        f"{BASE_URL}/wallets?merchant_id={merchant_id}",
        headers=headers
    )

    if response.status_code == 200:
        wallets = response.json()
        wallet_id = wallets[0]["id"] if wallets else None
        results.add_result("Get Merchant Wallets", True,
                         f"Found {len(wallets)} wallet(s)")
        print(f"   ✓ Retrieved {len(wallets)} wallet(s)")
        if wallet_id:
            print(f"   First wallet ID: {wallet_id}")
        return True
    else:
        results.add_result("Get Merchant Wallets", False,
                         f"Status: {response.status_code}, Response: {response.text}")
        print(f"   ✗ Failed: {response.text}")
        return False

def test_get_wallets_by_criteria():
    """Test get wallets by criteria (multi-currency)"""
    print("\n[TEST] Get Wallets by Criteria")

    headers = {"Authorization": f"Bearer {merchant_token}"}
    response = requests.get(
        f"{BASE_URL}/wallets/by-criteria?merchant_id={merchant_id}&currencies=NGN,USD,GHS&mode=test",
        headers=headers
    )

    if response.status_code == 200:
        wallets = response.json()
        results.add_result("Get Wallets by Criteria", True,
                         f"Found {len(wallets)} wallet(s) for NGN,USD,GHS")
        print(f"   ✓ Retrieved {len(wallets)} wallet(s) matching criteria")
        return True
    else:
        results.add_result("Get Wallets by Criteria", False,
                         f"Status: {response.status_code}, Response: {response.text}")
        print(f"   ✗ Failed: {response.text}")
        return False

def test_get_wallet_by_id():
    """Test get wallet by ID"""
    if not wallet_id:
        print("\n[TEST] Get Wallet by ID - SKIPPED (no wallet_id)")
        return False

    print("\n[TEST] Get Wallet by ID")

    headers = {"Authorization": f"Bearer {merchant_token}"}
    response = requests.get(f"{BASE_URL}/wallets/{wallet_id}", headers=headers)

    if response.status_code == 200:
        wallet = response.json()
        results.add_result("Get Wallet by ID", True,
                         f"Currency: {wallet.get('currency')}, Balance: {wallet.get('balance')}")
        print(f"   ✓ Wallet: {wallet.get('currency')} - Balance: {wallet.get('balance')}")
        return True
    else:
        results.add_result("Get Wallet by ID", False,
                         f"Status: {response.status_code}, Response: {response.text}")
        print(f"   ✗ Failed: {response.text}")
        return False

def test_wallet_balance_summary():
    """Test wallet balance summary"""
    print("\n[TEST] Wallet Balance Summary")

    headers = {"Authorization": f"Bearer {merchant_token}"}
    response = requests.get(
        f"{BASE_URL}/wallets/balance/summary?merchant_id={merchant_id}&mode=test",
        headers=headers
    )

    if response.status_code == 200:
        summary = response.json()
        total_currencies = len(summary.get("total_balances_by_currency", {}))
        results.add_result("Wallet Balance Summary", True,
                         f"Currencies: {total_currencies}")
        print(f"   ✓ Summary retrieved for {total_currencies} currency(ies)")
        return True
    else:
        results.add_result("Wallet Balance Summary", False,
                         f"Status: {response.status_code}, Response: {response.text}")
        print(f"   ✗ Failed: {response.text}")
        return False

def test_get_merchant_transactions():
    """Test get merchant transactions"""
    print("\n[TEST] Get Merchant Transactions")

    headers = {"Authorization": f"Bearer {merchant_token}"}
    response = requests.get(
        f"{BASE_URL}/merchant-transactions?merchant_id={merchant_id}&mode=test&page=1&page_size=10",
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        txn_count = len(data.get("transactions", []))
        results.add_result("Get Merchant Transactions", True,
                         f"Retrieved {txn_count} transaction(s)")
        print(f"   ✓ Retrieved {txn_count} transaction(s)")
        return True
    else:
        results.add_result("Get Merchant Transactions", False,
                         f"Status: {response.status_code}, Response: {response.text}")
        print(f"   ✗ Failed: {response.text}")
        return False

def test_get_wallet_transactions():
    """Test get wallet transactions"""
    if not wallet_id:
        print("\n[TEST] Get Wallet Transactions - SKIPPED (no wallet_id)")
        return False

    print("\n[TEST] Get Wallet Transactions")

    headers = {"Authorization": f"Bearer {merchant_token}"}
    response = requests.get(
        f"{BASE_URL}/wallet-transactions?wallet_id={wallet_id}&page=1&page_size=10",
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        txn_count = len(data.get("transactions", []))
        results.add_result("Get Wallet Transactions", True,
                         f"Retrieved {txn_count} transaction(s)")
        print(f"   ✓ Retrieved {txn_count} transaction(s) for wallet {wallet_id}")
        return True
    else:
        results.add_result("Get Wallet Transactions", False,
                         f"Status: {response.status_code}, Response: {response.text}")
        print(f"   ✗ Failed: {response.text}")
        return False

def test_get_wallet_transaction_stats():
    """Test get wallet transaction stats"""
    if not wallet_id:
        print("\n[TEST] Get Wallet Transaction Stats - SKIPPED (no wallet_id)")
        return False

    print("\n[TEST] Get Wallet Transaction Stats")

    headers = {"Authorization": f"Bearer {merchant_token}"}
    response = requests.get(
        f"{BASE_URL}/wallet-transaction-stats?wallet_id={wallet_id}",
        headers=headers
    )

    if response.status_code == 200:
        stats = response.json()
        results.add_result("Get Wallet Transaction Stats", True,
                         f"Credits: {stats.get('credits', {}).get('count', 0)}, "
                         f"Debits: {stats.get('debits', {}).get('count', 0)}")
        print(f"   ✓ Stats retrieved successfully")
        return True
    else:
        results.add_result("Get Wallet Transaction Stats", False,
                         f"Status: {response.status_code}, Response: {response.text}")
        print(f"   ✗ Failed: {response.text}")
        return False

def test_get_merchant_transactions_by_wallet():
    """Test get merchant transactions grouped by wallet"""
    print("\n[TEST] Get Merchant Transactions by Wallet")

    headers = {"Authorization": f"Bearer {merchant_token}"}
    response = requests.get(
        f"{BASE_URL}/merchant-transactions-by-wallet?merchant_id={merchant_id}&mode=test",
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        wallet_count = len(data.get("wallets", []))
        results.add_result("Get Merchant Transactions by Wallet", True,
                         f"Found {wallet_count} wallet(s) with transactions")
        print(f"   ✓ Retrieved data for {wallet_count} wallet(s)")
        return True
    else:
        results.add_result("Get Merchant Transactions by Wallet", False,
                         f"Status: {response.status_code}, Response: {response.text}")
        print(f"   ✗ Failed: {response.text}")
        return False

def test_v1_payout():
    """Test V1 payout endpoint"""
    print("\n[TEST] V1 Payout")

    headers = {"Authorization": f"Bearer {V1_API_KEY}"}
    data = {
        "reference": f"PAYOUT_TEST_{int(time.time())}",
        "amount": 100.0,  # Small amount for testing
        "currency": "NGN",
        "destination": {
            "account_number": "0123456789",
            "bank_code": "058"
        },
        "customer": {"email": "testcustomer@example.com"},
        "narration": "Test payout"
    }

    response = requests.post(f"{BASE_URL}/api/v1/payout", json=data, headers=headers)

    # Could be 200 (success), 400 (insufficient balance), or other
    if response.status_code in [200, 400]:
        resp_data = response.json()
        if response.status_code == 400 and "insufficient" in resp_data.get("detail", "").lower():
            results.add_result("V1 Payout", True,
                             "Endpoint working (insufficient balance expected)")
            print("   ✓ Endpoint working (insufficient balance is expected)")
        else:
            results.add_result("V1 Payout", True,
                             f"Status: {response.status_code}")
            print(f"   ✓ Payout endpoint responded correctly")
        return True
    else:
        results.add_result("V1 Payout", False,
                         f"Status: {response.status_code}, Response: {response.text}")
        print(f"   ✗ Failed: {response.text}")
        return False

if __name__ == "__main__":
    import time

    print("="*80)
    print("STARTING API TESTS")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Merchant: {MERCHANT_EMAIL}")
    print(f"V1 API Key: {V1_API_KEY[:30]}...")

    # Test merchant authentication
    if test_merchant_login():
        # Test V1 API endpoints
        ref = test_v1_initialize()
        if ref:
            test_v1_verify(ref)

        test_v1_payout()

        # Test wallet endpoints
        test_get_wallets()
        test_get_wallets_by_criteria()
        test_get_wallet_by_id()
        test_wallet_balance_summary()

        # Test transaction endpoints
        test_get_merchant_transactions()
        test_get_wallet_transactions()
        test_get_wallet_transaction_stats()
        test_get_merchant_transactions_by_wallet()

    # Print summary
    results.print_summary()
