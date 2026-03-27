import pytest
import json
from unittest.mock import AsyncMock, patch

from sqlalchemy import select

from database.models.RoutingAttempt import RoutingAttempt
from database.models.RoutingDecisionAudit import RoutingDecisionAudit
from database.models.Transaction import Transaction
from external_services import interswitchService
from enums.transactionEnums import TransactionStatus, TransactionType
from services import routingService


def _merchant_headers(merchant_id: str) -> dict[str, str]:
    return {"Authorization": f"Bearer aggsk_test_{merchant_id}"}


@pytest.mark.asyncio
class TestRoutingApi:
    @patch("services.tokenService.verify_token", new_callable=AsyncMock)
    @patch("services.merchantService.get_by_id_or_email", new_callable=AsyncMock)
    @patch("external_services.flutterwaveService.post_request", new_callable=AsyncMock)
    async def test_initiate_returns_selected_gateway_and_routing_summary(
        self,
        mock_post_request,
        mock_get_merchant,
        mock_verify_token,
        client,
        async_session,
        test_merchant,
    ):
        mock_verify_token.return_value = True
        mock_get_merchant.return_value = test_merchant
        mock_post_request.return_value = (
            {"data": {"link": "https://checkout.example.com/fltw-session"}},
            200,
        )

        response = await client.post(
            "/api/v1/initiate",
            json={
                "reference": "ROUTE_INIT_001",
                "amount": 5000.0,
                "currency": "NGN",
                "customer": {"email": "customer@test.com"},
                "redirect_url": "https://merchant.example.com/callback",
            },
            headers=_merchant_headers(test_merchant.id),
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["selected_gateway"] == "fltw"
        assert payload["routing"]["fallback_order"][0] == "fltw"
        assert payload["checkout_url"] == "https://checkout.example.com/fltw-session"
        assert payload["gateway_reference"]

        transaction = await async_session.scalar(
            select(Transaction).where(Transaction.reference == "ROUTE_INIT_001")
        )
        assert transaction is not None

        assert mock_post_request.await_count == 1
        _, call_kwargs = mock_post_request.await_args
        flutterwave_payload = json.loads(call_kwargs["data"])
        assert flutterwave_payload["amount"] == 5000.0
        assert flutterwave_payload["customer"]["email"] == "customer@test.com"

    @patch("services.tokenService.verify_token", new_callable=AsyncMock)
    @patch("services.merchantService.get_by_id_or_email", new_callable=AsyncMock)
    @patch("services.routingService.build_routing_decision", new_callable=AsyncMock)
    @patch("external_services.interswitchService._create_paybill_checkout", new_callable=AsyncMock)
    @patch("external_services.interswitchService._request_access_token", new_callable=AsyncMock)
    async def test_initiate_can_return_interswitch_bridge_checkout_url(
        self,
        mock_request_access_token,
        mock_create_paybill_checkout,
        mock_build_routing_decision,
        mock_get_merchant,
        mock_verify_token,
        client,
        test_merchant,
        monkeypatch,
    ):
        mock_verify_token.return_value = True
        mock_get_merchant.return_value = test_merchant
        mock_build_routing_decision.return_value = routingService.RoutingDecision(
            selected_gateway="isw",
            ranked_gateways=["isw", "fltw", "pstk"],
            score_breakdown={"isw": 98.0, "fltw": 88.0, "pstk": 80.0},
            rejected_gateways={},
            selection_reason="forced priority order applied by global routing rule",
        )
        monkeypatch.setattr(interswitchService, "INTERSWITCH_MERCHANT_CODE", "MX123")
        monkeypatch.setattr(interswitchService, "INTERSWITCH_PAY_ITEM_ID", "9405967")
        monkeypatch.setattr(interswitchService, "INTERSWITCH_CLIENT_ID", "CLIENT123")
        monkeypatch.setattr(interswitchService, "INTERSWITCH_SECRET_KEY", "SECRET456")
        monkeypatch.setattr(interswitchService, "FRONTEND_BASE_URL", "https://routex.dev")
        mock_request_access_token.return_value = "test-access-token"
        mock_create_paybill_checkout.return_value = {
            "reference": "ISW_BILL_REF_001",
            "paymentUrl": "https://newwebpay.qa.interswitchng.com/pay/ISW_BILL_REF_001",
            "code": "200",
        }

        response = await client.post(
            "/api/v1/initiate",
            json={
                "reference": "ROUTE_INIT_ISW_001",
                "amount": 5000.0,
                "currency": "NGN",
                "customer": {"email": "customer@test.com"},
                "redirect_url": "https://merchant.example.com/callback",
            },
            headers=_merchant_headers(test_merchant.id),
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["selected_gateway"] == "isw"
        assert payload["checkout_url"] == "https://newwebpay.qa.interswitchng.com/pay/ISW_BILL_REF_001"
        assert payload["routing"]["fallback_order"][0] == "isw"

    @patch("services.tokenService.verify_token", new_callable=AsyncMock)
    @patch("services.merchantService.get_by_id_or_email", new_callable=AsyncMock)
    @patch("external_services.paystackService.post_request", new_callable=AsyncMock)
    async def test_initiate_honors_manual_gateway_override(
        self,
        mock_post_request,
        mock_get_merchant,
        mock_verify_token,
        client,
        test_merchant,
    ):
        mock_verify_token.return_value = True
        mock_get_merchant.return_value = test_merchant
        mock_post_request.return_value = (
            {"data": {"authorization_url": "https://checkout.example.com/pstk-session"}},
            200,
        )

        response = await client.post(
            "/api/v1/initiate",
            json={
                "reference": "ROUTE_INIT_PSTK_001",
                "amount": 5000.0,
                "currency": "NGN",
                "customer": {"email": "customer@test.com"},
                "gateway_code": "pstk",
            },
            headers=_merchant_headers(test_merchant.id),
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["selected_gateway"] == "pstk"
        assert payload["routing"]["selection_reason"] == "merchant selected gateway override"
        assert payload["routing"]["fallback_order"][0] == "pstk"
        assert payload["checkout_url"] == "https://checkout.example.com/pstk-session"

    @patch("services.tokenService.verify_token", new_callable=AsyncMock)
    @patch("services.merchantService.get_by_id_or_email", new_callable=AsyncMock)
    @patch("external_services.paystackService.post_request", new_callable=AsyncMock)
    async def test_initiate_accepts_gateway_alias_for_manual_override(
        self,
        mock_post_request,
        mock_get_merchant,
        mock_verify_token,
        client,
        test_merchant,
    ):
        mock_verify_token.return_value = True
        mock_get_merchant.return_value = test_merchant
        mock_post_request.return_value = (
            {"data": {"authorization_url": "https://checkout.example.com/pstk-alias"}},
            200,
        )

        response = await client.post(
            "/api/v1/initiate",
            json={
                "reference": "ROUTE_INIT_PSTK_ALIAS_001",
                "amount": 5000.0,
                "currency": "NGN",
                "customer": {"email": "customer@test.com"},
                "gateway": "pstk",
            },
            headers=_merchant_headers(test_merchant.id),
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["selected_gateway"] == "pstk"
        assert payload["routing"]["selection_reason"] == "merchant selected gateway override"
        assert payload["checkout_url"] == "https://checkout.example.com/pstk-alias"

    @patch("services.tokenService.verify_token", new_callable=AsyncMock)
    @patch("services.merchantService.get_by_id_or_email", new_callable=AsyncMock)
    async def test_initiate_rejects_unknown_manual_gateway_override(
        self,
        mock_get_merchant,
        mock_verify_token,
        client,
        test_merchant,
    ):
        mock_verify_token.return_value = True
        mock_get_merchant.return_value = test_merchant

        response = await client.post(
            "/api/v1/initiate",
            json={
                "reference": "ROUTE_INIT_UNKNOWN_GATEWAY",
                "amount": 5000.0,
                "currency": "NGN",
                "customer": {"email": "customer@test.com"},
                "gateway_code": "bogus",
            },
            headers=_merchant_headers(test_merchant.id),
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Requested gateway 'bogus' is not supported."

    @patch("services.tokenService.verify_token", new_callable=AsyncMock)
    @patch("services.merchantService.get_by_id_or_email", new_callable=AsyncMock)
    @patch("services.emailService.send_merchant_receipt_email")
    @patch("services.emailService.send_customer_receipt_email")
    @patch("external_services.koraService.resolve_account", new_callable=AsyncMock)
    @patch("external_services.koraService.post_request", new_callable=AsyncMock)
    async def test_payout_returns_selected_gateway_and_router_metadata(
        self,
        mock_post_request,
        mock_resolve_account,
        mock_send_customer_receipt,
        mock_send_merchant_receipt,
        mock_get_merchant,
        mock_verify_token,
        client,
        async_session,
        test_merchant,
        test_wallet,
    ):
        del test_wallet
        del mock_send_customer_receipt
        del mock_send_merchant_receipt

        mock_verify_token.return_value = True
        mock_get_merchant.return_value = test_merchant
        mock_resolve_account.return_value = (True, "Ada Lovelace")
        mock_post_request.return_value = ({"status": True}, 200)

        response = await client.post(
            "/api/v1/payout",
            json={
                "reference": "ROUTE_PAYOUT_001",
                "amount": 1000.0,
                "currency": "NGN",
                "destination": {
                    "account_number": "0123456789",
                    "bank_code": "058",
                },
                "customer": {
                    "email": "customer@test.com",
                    "name": "Ada Lovelace",
                },
                "narration": "Vendor payout",
            },
            headers=_merchant_headers(test_merchant.id),
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["selected_gateway"] == "kora"
        assert payload["routing"]["fallback_order"][0] == "kora"
        assert payload["gateway_reference"]
        assert payload["data"]["reference"] == "ROUTE_PAYOUT_001"

    @patch("services.tokenService.verify_token", new_callable=AsyncMock)
    @patch("services.merchantService.get_by_id_or_email", new_callable=AsyncMock)
    async def test_verify_returns_selected_gateway_and_attempts(
        self,
        mock_get_merchant,
        mock_verify_token,
        client,
        async_session,
        test_merchant,
        test_customer,
    ):
        mock_verify_token.return_value = True
        mock_get_merchant.return_value = test_merchant

        transaction = Transaction(
            merchant_id=test_merchant.id,
            customer_id=test_customer.id,
            amount=2500.0,
            charge=25.0,
            currency="NGN",
            type=TransactionType.CREDIT.value,
            status=TransactionStatus.SUCCESS.value,
            mode="test",
            processor="fltw",
            selected_gateway="fltw",
            reference="ROUTE_VERIFY_001",
            processor_reference="FLTW_PROC_001",
        )
        async_session.add(transaction)
        await async_session.commit()
        await async_session.refresh(transaction)

        async_session.add(
            RoutingAttempt(
                transaction_id=transaction.id,
                attempt_no=1,
                gateway_code="fltw",
                operation="collection",
                status="success",
                gateway_reference="FLTW_PROC_001",
                latency_ms=840,
            )
        )
        async_session.add(
            RoutingDecisionAudit(
                transaction_id=transaction.id,
                selected_gateway="fltw",
                eligible_gateways=["fltw", "pstk", "kora"],
                rejected_gateways={"isw": "processor_inactive"},
                reason="highest score among eligible gateways",
                score_breakdown={"fltw": 92.4, "pstk": 88.1, "kora": 81.2},
                fallback_order=["fltw", "pstk", "kora"],
            )
        )
        await async_session.commit()

        response = await client.get(
            "/api/v1/transactions/verify?reference=ROUTE_VERIFY_001",
            headers=_merchant_headers(test_merchant.id),
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["data"]["selected_gateway"] == "fltw"
        assert payload["data"]["gateway_reference"] == "FLTW_PROC_001"
        assert payload["data"]["attempts"][0]["gateway"] == "fltw"

    @patch("services.tokenService.verify_token", new_callable=AsyncMock)
    @patch("services.merchantService.get_by_id_or_email", new_callable=AsyncMock)
    @patch("external_services.interswitchService.get_request", new_callable=AsyncMock)
    async def test_verify_requeries_interswitch_transactions(
        self,
        mock_get_request,
        mock_get_merchant,
        mock_verify_token,
        client,
        async_session,
        test_merchant,
        test_customer,
        monkeypatch,
    ):
        mock_verify_token.return_value = True
        mock_get_merchant.return_value = test_merchant
        mock_get_request.return_value = (
            {
                "Amount": 250000,
                "MerchantReference": "ISW_PROC_001",
                "PaymentReference": "ISW_PAY_001",
                "RetrievalReferenceNumber": "123456789012",
                "ResponseCode": "00",
                "ResponseDescription": "Approved by Financial Institution",
            },
            200,
        )
        monkeypatch.setattr(interswitchService, "INTERSWITCH_MERCHANT_CODE", "MX123")

        transaction = Transaction(
            merchant_id=test_merchant.id,
            customer_id=test_customer.id,
            amount=2500.0,
            charge=25.0,
            currency="NGN",
            type=TransactionType.CREDIT.value,
            status=TransactionStatus.PENDING.value,
            mode="test",
            processor="isw",
            selected_gateway="isw",
            reference="ROUTE_VERIFY_ISW_001",
            processor_reference="ISW_PROC_001",
        )
        async_session.add(transaction)
        await async_session.commit()
        await async_session.refresh(transaction)

        async_session.add(
            RoutingAttempt(
                transaction_id=transaction.id,
                attempt_no=1,
                gateway_code="isw",
                operation="collection",
                status="pending",
                gateway_reference="ISW_PROC_001",
                latency_ms=0,
            )
        )
        async_session.add(
            RoutingDecisionAudit(
                transaction_id=transaction.id,
                selected_gateway="isw",
                eligible_gateways=["isw", "fltw", "pstk"],
                rejected_gateways={},
                reason="highest score among eligible gateways",
                score_breakdown={"isw": 94.0, "fltw": 89.5, "pstk": 87.1},
                fallback_order=["isw", "fltw", "pstk"],
            )
        )
        await async_session.commit()

        response = await client.get(
            "/api/v1/transactions/verify?reference=ROUTE_VERIFY_ISW_001",
            headers=_merchant_headers(test_merchant.id),
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["data"]["selected_gateway"] == "isw"
        assert payload["data"]["status"] == "success"
        assert payload["data"]["gateway_reference"] == "ISW_PROC_001"
