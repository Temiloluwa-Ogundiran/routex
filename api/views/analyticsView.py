from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.session import get_async_session
from database.models.User import User
from services import userService, merchantService, analyticsService
from schemas import analyticsSchema
from enums import tokenEnums
from typing import Optional
from datetime import datetime

analytics_router = APIRouter()


@analytics_router.get("/analytics/dashboard", response_model=analyticsSchema.DashboardSummaryResponse)
async def get_dashboard_summary(
    merchant_id: str = Query(..., description="Merchant ID"),
    mode: tokenEnums.TokenMode = Query(tokenEnums.TokenMode.TEST, description="Mode: test or live"),
    period: str = Query("month", description="Period: today, week, month, quarter, year, all_time"),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    """
    Get comprehensive dashboard summary for merchant
    Includes revenue metrics, transaction breakdown, top currency, and wallet stats
    """
    merchant = await merchantService.get_by_id_or_email(session=session, id=merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    if not await userService.user_in_merchant(session=session, merchant=merchant, user=user):
        raise HTTPException(status_code=403, detail="User does not belong to merchant")

    # Get date range
    start_date, end_date = await analyticsService.get_date_range(period)

    # Get revenue metrics
    revenue_metrics = await analyticsService.get_revenue_metrics(
        session=session,
        merchant_id=merchant_id,
        mode=mode,
        start_date=start_date,
        end_date=end_date
    )

    # Get transaction breakdown
    transaction_breakdown = await analyticsService.get_transaction_breakdown(
        session=session,
        merchant_id=merchant_id,
        mode=mode,
        start_date=start_date,
        end_date=end_date
    )

    # Get currency breakdown to find top currency
    currency_breakdown = await analyticsService.get_currency_breakdown(
        session=session,
        merchant_id=merchant_id,
        mode=mode,
        start_date=start_date,
        end_date=end_date
    )
    top_currency = currency_breakdown[0] if currency_breakdown else None

    # Get wallet analytics
    wallet_analytics = await analyticsService.get_wallet_analytics(
        session=session,
        merchant_id=merchant_id,
        mode=mode
    )
    wallet_count = len(wallet_analytics)
    total_balance = sum(w['current_balance'] for w in wallet_analytics)

    # Get payout analytics for pending info
    payout_analytics = await analyticsService.get_payout_analytics(
        session=session,
        merchant_id=merchant_id,
        mode=mode
    )

    return {
        "mode": mode,
        "period": period,
        "revenue_metrics": revenue_metrics,
        "transaction_breakdown": transaction_breakdown,
        "top_currency": top_currency,
        "wallet_count": wallet_count,
        "total_balance": total_balance,
        "pending_payouts": payout_analytics['pending_payouts'],
        "pending_payout_amount": 0  # Would need to calculate pending payout amounts
    }


@analytics_router.get("/analytics/revenue", response_model=analyticsSchema.RevenueAnalyticsResponse)
async def get_revenue_analytics(
    merchant_id: str = Query(..., description="Merchant ID"),
    mode: tokenEnums.TokenMode = Query(tokenEnums.TokenMode.TEST, description="Mode: test or live"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    currency: Optional[str] = Query(None, description="Filter by currency"),
    interval: str = Query("day", description="Time series interval: day, week, month"),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    """
    Get detailed revenue analytics with time series data
    """
    merchant = await merchantService.get_by_id_or_email(session=session, id=merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    if not await userService.user_in_merchant(session=session, merchant=merchant, user=user):
        raise HTTPException(status_code=403, detail="User does not belong to merchant")

    # Parse dates
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    # Get revenue metrics
    revenue_metrics = await analyticsService.get_revenue_metrics(
        session=session,
        merchant_id=merchant_id,
        mode=mode,
        start_date=start_dt,
        end_date=end_dt,
        currency=currency
    )

    # Get time series data
    time_series = await analyticsService.get_time_series_data(
        session=session,
        merchant_id=merchant_id,
        mode=mode,
        start_date=start_dt,
        end_date=end_dt,
        currency=currency,
        interval=interval
    )

    # Get currency breakdown
    currency_breakdown = await analyticsService.get_currency_breakdown(
        session=session,
        merchant_id=merchant_id,
        mode=mode,
        start_date=start_dt,
        end_date=end_dt
    )

    return {
        "mode": mode,
        "start_date": start_date,
        "end_date": end_date,
        "currency": currency,
        "revenue_metrics": revenue_metrics,
        "time_series": time_series,
        "currency_breakdown": currency_breakdown
    }


@analytics_router.get("/analytics/transactions", response_model=analyticsSchema.TransactionAnalyticsResponse)
async def get_transaction_analytics(
    merchant_id: str = Query(..., description="Merchant ID"),
    mode: tokenEnums.TokenMode = Query(tokenEnums.TokenMode.TEST, description="Mode: test or live"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    currency: Optional[str] = Query(None, description="Filter by currency"),
    interval: str = Query("day", description="Time series interval: day, week, month"),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    """
    Get detailed transaction analytics including channel breakdown
    """
    merchant = await merchantService.get_by_id_or_email(session=session, id=merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    if not await userService.user_in_merchant(session=session, merchant=merchant, user=user):
        raise HTTPException(status_code=403, detail="User does not belong to merchant")

    # Parse dates
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    # Get transaction breakdown
    transaction_breakdown = await analyticsService.get_transaction_breakdown(
        session=session,
        merchant_id=merchant_id,
        mode=mode,
        start_date=start_dt,
        end_date=end_dt,
        currency=currency
    )

    # Get channel breakdown
    channel_breakdown = await analyticsService.get_channel_breakdown(
        session=session,
        merchant_id=merchant_id,
        mode=mode,
        start_date=start_dt,
        end_date=end_dt,
        currency=currency
    )

    # Get time series
    time_series = await analyticsService.get_time_series_data(
        session=session,
        merchant_id=merchant_id,
        mode=mode,
        start_date=start_dt,
        end_date=end_dt,
        currency=currency,
        interval=interval
    )

    return {
        "mode": mode,
        "start_date": start_date,
        "end_date": end_date,
        "currency": currency,
        "transaction_breakdown": transaction_breakdown,
        "channel_breakdown": channel_breakdown,
        "time_series": time_series,
        "average_processing_time": None  # Would need to track processing times
    }


@analytics_router.get("/analytics/wallets", response_model=analyticsSchema.WalletAnalyticsResponse)
async def get_wallet_analytics(
    merchant_id: str = Query(..., description="Merchant ID"),
    mode: tokenEnums.TokenMode = Query(tokenEnums.TokenMode.TEST, description="Mode: test or live"),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    """
    Get comprehensive wallet analytics for all merchant wallets
    """
    merchant = await merchantService.get_by_id_or_email(session=session, id=merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    if not await userService.user_in_merchant(session=session, merchant=merchant, user=user):
        raise HTTPException(status_code=403, detail="User does not belong to merchant")

    # Get wallet analytics
    wallets = await analyticsService.get_wallet_analytics(
        session=session,
        merchant_id=merchant_id,
        mode=mode
    )

    total_balance = sum(w['current_balance'] for w in wallets)
    total_credits = sum(w['total_credits'] for w in wallets)
    total_debits = sum(w['total_debits'] for w in wallets)
    total_charges_earned = sum(w['total_charges_earned'] for w in wallets)
    currency_count = len(set(w['currency'] for w in wallets))

    return {
        "mode": mode,
        "wallets": wallets,
        "total_balance": total_balance,
        "total_credits": total_credits,
        "total_debits": total_debits,
        "total_charges_earned": total_charges_earned,
        "currency_count": currency_count
    }


@analytics_router.get("/analytics/customers", response_model=analyticsSchema.CustomerAnalyticsResponse)
async def get_customer_analytics(
    merchant_id: str = Query(..., description="Merchant ID"),
    mode: tokenEnums.TokenMode = Query(tokenEnums.TokenMode.TEST, description="Mode: test or live"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    top_limit: int = Query(10, description="Number of top customers to return"),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    """
    Get customer analytics including top customers and repeat rate
    """
    merchant = await merchantService.get_by_id_or_email(session=session, id=merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    if not await userService.user_in_merchant(session=session, merchant=merchant, user=user):
        raise HTTPException(status_code=403, detail="User does not belong to merchant")

    # Parse dates
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    # Get customer analytics
    customer_analytics = await analyticsService.get_customer_analytics(
        session=session,
        merchant_id=merchant_id,
        mode=mode,
        start_date=start_dt,
        end_date=end_dt
    )

    # Get top customers
    top_customers = await analyticsService.get_top_customers(
        session=session,
        merchant_id=merchant_id,
        mode=mode,
        start_date=start_dt,
        end_date=end_dt,
        limit=top_limit
    )

    return {
        "mode": mode,
        "start_date": start_date,
        "end_date": end_date,
        "total_customers": customer_analytics['total_customers'],
        "active_customers": customer_analytics['active_customers'],
        "new_customers": customer_analytics['new_customers'],
        "top_customers": top_customers,
        "repeat_customer_rate": customer_analytics['repeat_customer_rate']
    }


@analytics_router.get("/analytics/payouts", response_model=analyticsSchema.PayoutAnalyticsResponse)
async def get_payout_analytics(
    merchant_id: str = Query(..., description="Merchant ID"),
    mode: tokenEnums.TokenMode = Query(tokenEnums.TokenMode.TEST, description="Mode: test or live"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    currency: Optional[str] = Query(None, description="Filter by currency"),
    interval: str = Query("day", description="Time series interval: day, week, month"),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    """
    Get payout analytics with time series data
    """
    merchant = await merchantService.get_by_id_or_email(session=session, id=merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    if not await userService.user_in_merchant(session=session, merchant=merchant, user=user):
        raise HTTPException(status_code=403, detail="User does not belong to merchant")

    # Parse dates
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    # Get payout analytics
    payout_analytics = await analyticsService.get_payout_analytics(
        session=session,
        merchant_id=merchant_id,
        mode=mode,
        start_date=start_dt,
        end_date=end_dt,
        currency=currency
    )

    # Get time series for payouts
    time_series = await analyticsService.get_time_series_data(
        session=session,
        merchant_id=merchant_id,
        mode=mode,
        start_date=start_dt,
        end_date=end_dt,
        currency=currency,
        interval=interval
    )

    return {
        "mode": mode,
        "start_date": start_date,
        "end_date": end_date,
        "currency": currency,
        "total_payouts": payout_analytics['total_payouts'],
        "payout_count": payout_analytics['payout_count'],
        "successful_payouts": payout_analytics['successful_payouts'],
        "failed_payouts": payout_analytics['failed_payouts'],
        "pending_payouts": payout_analytics['pending_payouts'],
        "total_payout_charges": payout_analytics['total_payout_charges'],
        "average_payout_amount": payout_analytics['average_payout_amount'],
        "time_series": time_series
    }


@analytics_router.get("/analytics/patterns", response_model=analyticsSchema.TransactionPatternResponse)
async def get_transaction_patterns(
    merchant_id: str = Query(..., description="Merchant ID"),
    mode: tokenEnums.TokenMode = Query(tokenEnums.TokenMode.TEST, description="Mode: test or live"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    """
    Get transaction patterns - hourly and day-of-week distribution
    Helps identify peak transaction times
    """
    merchant = await merchantService.get_by_id_or_email(session=session, id=merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    if not await userService.user_in_merchant(session=session, merchant=merchant, user=user):
        raise HTTPException(status_code=403, detail="User does not belong to merchant")

    # Parse dates
    start_dt = datetime.fromisoformat(start_date) if start_date else None
    end_dt = datetime.fromisoformat(end_date) if end_date else None

    # Get transaction patterns
    patterns = await analyticsService.get_transaction_patterns(
        session=session,
        merchant_id=merchant_id,
        mode=mode,
        start_date=start_dt,
        end_date=end_dt
    )

    # Calculate average daily transactions
    if start_dt and end_dt:
        days = (end_dt - start_dt).days or 1
        total_transactions = sum(h['transaction_count'] for h in patterns['hourly_distribution'])
        average_daily = total_transactions / days
    else:
        average_daily = 0

    return {
        "mode": mode,
        "start_date": start_date,
        "end_date": end_date,
        "hourly_distribution": patterns['hourly_distribution'],
        "day_of_week_distribution": patterns['day_of_week_distribution'],
        "peak_hour": patterns['peak_hour'],
        "peak_day": patterns['peak_day'],
        "average_daily_transactions": average_daily
    }


@analytics_router.get("/analytics/comparison")
async def get_comparison_analytics(
    merchant_id: str = Query(..., description="Merchant ID"),
    mode: tokenEnums.TokenMode = Query(tokenEnums.TokenMode.TEST, description="Mode: test or live"),
    current_period: str = Query("month", description="Current period: week, month, quarter, year"),
    compare_with: str = Query("previous", description="Compare with: previous (same period before)"),
    currency: Optional[str] = Query(None, description="Filter by currency"),
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(userService.get_current_user)
):
    """
    Compare metrics between current and previous periods
    Shows growth trends and changes
    """
    merchant = await merchantService.get_by_id_or_email(session=session, id=merchant_id)
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    if not await userService.user_in_merchant(session=session, merchant=merchant, user=user):
        raise HTTPException(status_code=403, detail="User does not belong to merchant")

    # Get current period date range
    current_start, current_end = await analyticsService.get_date_range(current_period)

    # Calculate previous period
    if current_start and current_end:
        period_length = current_end - current_start
        previous_end = current_start
        previous_start = previous_end - period_length
    else:
        previous_start = None
        previous_end = None

    # Get current period metrics
    current_metrics = await analyticsService.get_revenue_metrics(
        session=session,
        merchant_id=merchant_id,
        mode=mode,
        start_date=current_start,
        end_date=current_end,
        currency=currency
    )

    # Get previous period metrics
    previous_metrics = await analyticsService.get_revenue_metrics(
        session=session,
        merchant_id=merchant_id,
        mode=mode,
        start_date=previous_start,
        end_date=previous_end,
        currency=currency
    )

    # Calculate changes
    revenue_change = 0
    transaction_change = 0
    success_rate_change = 0

    if previous_metrics['total_revenue'] > 0:
        revenue_change = ((current_metrics['total_revenue'] - previous_metrics['total_revenue']) /
                          previous_metrics['total_revenue'] * 100)

    if previous_metrics['total_transactions'] > 0:
        transaction_change = ((current_metrics['total_transactions'] - previous_metrics['total_transactions']) /
                              previous_metrics['total_transactions'] * 100)

    success_rate_change = current_metrics['success_rate'] - previous_metrics['success_rate']

    # Determine trend
    if revenue_change > 5:
        growth_trend = "up"
    elif revenue_change < -5:
        growth_trend = "down"
    else:
        growth_trend = "stable"

    return {
        "mode": mode,
        "current_period": current_period,
        "previous_period": f"previous_{current_period}",
        "comparison": {
            "current_period": current_metrics,
            "previous_period": previous_metrics,
            "revenue_change": revenue_change,
            "transaction_change": transaction_change,
            "success_rate_change": success_rate_change
        },
        "growth_trend": growth_trend
    }
