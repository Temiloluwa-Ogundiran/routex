from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.Admin import Admin
from database.session import get_async_session
from schemas.routerAnalyticsSchema import (
    RouterDashboardResponse,
    RouterGatewayHealthItem,
    RouterRuleCreateRequest,
    RouterRuleItem,
    RouterRuleUpdateRequest,
    RouterGatewayUpdateRequest,
    RouterGatewayUpdateResponse,
    RouterTransactionDetailResponse,
    RouterTransactionItem,
    RouterFailoverItem,
)
import services.adminService as adminService
import services.routerAdminService as routerAdminService
import services.routerAnalyticsService as routerAnalyticsService
import services.gatewayHealthService as gatewayHealthService


router_control_router = APIRouter()


@router_control_router.get(
    "/analytics/router/dashboard",
    response_model=RouterDashboardResponse,
)
async def get_router_dashboard(
    session: AsyncSession = Depends(get_async_session),
    admin: Admin = Depends(adminService.get_current_admin),
):
    del admin
    await gatewayHealthService.refresh_gateway_health_snapshots(session)
    return await routerAnalyticsService.get_dashboard_summary(session)


@router_control_router.get(
    "/analytics/router/gateways",
    response_model=list[RouterGatewayHealthItem],
)
async def get_router_gateways(
    session: AsyncSession = Depends(get_async_session),
    admin: Admin = Depends(adminService.get_current_admin),
):
    del admin
    await gatewayHealthService.refresh_gateway_health_snapshots(session)
    return await routerAnalyticsService.get_gateway_health_summary(session)


@router_control_router.get(
    "/analytics/router/transactions",
    response_model=list[RouterTransactionItem],
)
async def get_router_transactions(
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
    admin: Admin = Depends(adminService.get_current_admin),
):
    del admin
    return await routerAnalyticsService.get_recent_routed_transactions(session, limit=limit)


@router_control_router.get(
    "/analytics/router/transactions/{reference}",
    response_model=RouterTransactionDetailResponse,
)
async def get_router_transaction_detail(
    reference: str,
    created_at: datetime | None = Query(default=None),
    session: AsyncSession = Depends(get_async_session),
    admin: Admin = Depends(adminService.get_current_admin),
):
    del admin
    transaction_detail = await routerAnalyticsService.get_transaction_detail(
        session,
        reference,
        created_at=created_at,
    )
    if not transaction_detail:
        raise HTTPException(status_code=404, detail="Transaction not found")

    return transaction_detail


@router_control_router.get(
    "/analytics/router/failovers",
    response_model=list[RouterFailoverItem],
)
async def get_router_failovers(
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_async_session),
    admin: Admin = Depends(adminService.get_current_admin),
):
    del admin
    return await routerAnalyticsService.get_recent_failovers(session, limit=limit)


@router_control_router.get(
    "/admin/router/rules",
    response_model=list[RouterRuleItem],
)
async def list_router_rules(
    session: AsyncSession = Depends(get_async_session),
    admin: Admin = Depends(adminService.get_current_admin),
):
    del admin
    rules = await routerAdminService.list_routing_rules(session)
    return [routerAdminService.serialize_routing_rule(rule) for rule in rules]


@router_control_router.post(
    "/admin/router/rules",
    response_model=RouterRuleItem,
)
async def create_router_rule(
    payload: RouterRuleCreateRequest,
    session: AsyncSession = Depends(get_async_session),
    admin: Admin = Depends(adminService.get_current_admin),
):
    del admin
    try:
        rule = await routerAdminService.create_routing_rule(session, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return routerAdminService.serialize_routing_rule(rule)


@router_control_router.patch(
    "/admin/router/rules/{rule_id}",
    response_model=RouterRuleItem,
)
async def update_router_rule(
    rule_id: int,
    payload: RouterRuleUpdateRequest,
    session: AsyncSession = Depends(get_async_session),
    admin: Admin = Depends(adminService.get_current_admin),
):
    del admin
    try:
        rule = await routerAdminService.update_routing_rule(session, rule_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not rule:
        raise HTTPException(status_code=404, detail="Routing rule not found")

    return routerAdminService.serialize_routing_rule(rule)


@router_control_router.patch(
    "/admin/router/gateways/{gateway_code}",
    response_model=RouterGatewayUpdateResponse,
)
async def update_router_gateway(
    gateway_code: str,
    payload: RouterGatewayUpdateRequest,
    session: AsyncSession = Depends(get_async_session),
    admin: Admin = Depends(adminService.get_current_admin),
):
    del admin
    processor = await routerAdminService.update_gateway(
        session=session,
        gateway_code=gateway_code,
        is_active=payload.is_active,
        priority_weight=payload.priority_weight,
    )
    if not processor:
        raise HTTPException(status_code=404, detail="Gateway not found")

    return {
        "gateway_code": processor.code,
        "gateway_name": processor.name or processor.code.upper(),
        "is_active": bool(processor.is_active),
        "priority_weight": float(processor.priority_weight or 0.0),
        "supports_collections": bool(processor.supports_collections),
        "supports_payouts": bool(processor.supports_payouts),
    }


@router_control_router.post(
    "/admin/router/refresh-health",
    response_model=RouterDashboardResponse,
)
async def refresh_router_health(
    session: AsyncSession = Depends(get_async_session),
    admin: Admin = Depends(adminService.get_current_admin),
):
    del admin
    await gatewayHealthService.refresh_gateway_health_snapshots(session)
    return await routerAnalyticsService.get_dashboard_summary(session)
