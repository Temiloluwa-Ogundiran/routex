"""
Analytics service for merchant business insights
Provides comprehensive analytics on transactions, revenue, customers, and performance
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, case, extract, desc
from database.models.Transaction import Transaction
from database.models.Wallet import Wallet
from database.models.Customer import Customer
from database.models.Merchant import Merchant
from enums.transactionEnums import TransactionStatus, TransactionType
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple


async def get_date_range(period: str) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Get date range based on period string"""
    now = datetime.utcnow()

    if period == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = now
    elif period == "yesterday":
        start_date = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date.replace(hour=23, minute=59, second=59)
    elif period == "week":
        start_date = now - timedelta(days=7)
        end_date = now
    elif period == "month":
        start_date = now - timedelta(days=30)
        end_date = now
    elif period == "quarter":
        start_date = now - timedelta(days=90)
        end_date = now
    elif period == "year":
        start_date = now - timedelta(days=365)
        end_date = now
    elif period == "all_time":
        start_date = None
        end_date = None
    else:
        # Default to last 30 days
        start_date = now - timedelta(days=30)
        end_date = now

    return start_date, end_date


async def get_revenue_metrics(
    session: AsyncSession,
    merchant_id: str,
    mode: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    currency: Optional[str] = None
) -> Dict:
    """Get comprehensive revenue metrics"""

    # Build base query
    query = select(
        func.count(Transaction.id).label('total_transactions'),
        func.coalesce(func.sum(
            case((Transaction.status == TransactionStatus.SUCCESS, Transaction.amount), else_=0)
        ), 0).label('total_revenue'),
        func.coalesce(func.sum(
            case((Transaction.status == TransactionStatus.SUCCESS, Transaction.charge), else_=0)
        ), 0).label('total_charges'),
        func.count(
            case((Transaction.status == TransactionStatus.SUCCESS, 1))
        ).label('successful_count')
    ).where(
        Transaction.merchant_id == merchant_id,
        Transaction.mode == mode,
        Transaction.type == TransactionType.CREDIT
    )

    if start_date:
        query = query.where(Transaction.created_at >= start_date)
    if end_date:
        query = query.where(Transaction.created_at <= end_date)
    if currency:
        query = query.where(Transaction.currency == currency)

    result = await session.execute(query)
    row = result.first()

    total_transactions = row.total_transactions or 0
    total_revenue = float(row.total_revenue or 0)
    total_charges = float(row.total_charges or 0)
    successful_count = row.successful_count or 0

    net_revenue = total_revenue - total_charges
    average_transaction_value = total_revenue / successful_count if successful_count > 0 else 0
    success_rate = (successful_count / total_transactions * 100) if total_transactions > 0 else 0

    return {
        "total_revenue": total_revenue,
        "total_transactions": total_transactions,
        "total_charges": total_charges,
        "net_revenue": net_revenue,
        "average_transaction_value": average_transaction_value,
        "success_rate": success_rate
    }


async def get_transaction_breakdown(
    session: AsyncSession,
    merchant_id: str,
    mode: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    currency: Optional[str] = None
) -> Dict:
    """Get transaction breakdown by status"""

    query = select(
        func.count(case((Transaction.status == TransactionStatus.SUCCESS, 1))).label('successful'),
        func.count(case((Transaction.status == TransactionStatus.PENDING, 1))).label('pending'),
        func.count(case((Transaction.status == TransactionStatus.FAILED, 1))).label('failed'),
        func.count(Transaction.id).label('total')
    ).where(
        Transaction.merchant_id == merchant_id,
        Transaction.mode == mode
    )

    if start_date:
        query = query.where(Transaction.created_at >= start_date)
    if end_date:
        query = query.where(Transaction.created_at <= end_date)
    if currency:
        query = query.where(Transaction.currency == currency)

    result = await session.execute(query)
    row = result.first()

    return {
        "successful": row.successful or 0,
        "pending": row.pending or 0,
        "failed": row.failed or 0,
        "total": row.total or 0
    }


async def get_currency_breakdown(
    session: AsyncSession,
    merchant_id: str,
    mode: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Dict]:
    """Get metrics broken down by currency"""

    query = select(
        Transaction.currency,
        func.count(Transaction.id).label('transaction_count'),
        func.coalesce(func.sum(
            case((Transaction.status == TransactionStatus.SUCCESS, Transaction.amount), else_=0)
        ), 0).label('total_revenue'),
        func.coalesce(func.sum(
            case((Transaction.status == TransactionStatus.SUCCESS, Transaction.charge), else_=0)
        ), 0).label('total_charges')
    ).where(
        Transaction.merchant_id == merchant_id,
        Transaction.mode == mode,
        Transaction.type == TransactionType.CREDIT
    ).group_by(Transaction.currency)

    if start_date:
        query = query.where(Transaction.created_at >= start_date)
    if end_date:
        query = query.where(Transaction.created_at <= end_date)

    result = await session.execute(query)

    breakdown = []
    for row in result:
        total_revenue = float(row.total_revenue or 0)
        total_charges = float(row.total_charges or 0)
        transaction_count = row.transaction_count or 0

        breakdown.append({
            "currency": row.currency,
            "total_revenue": total_revenue,
            "transaction_count": transaction_count,
            "total_charges": total_charges,
            "net_revenue": total_revenue - total_charges,
            "average_transaction_value": total_revenue / transaction_count if transaction_count > 0 else 0
        })

    return breakdown


async def get_channel_breakdown(
    session: AsyncSession,
    merchant_id: str,
    mode: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    currency: Optional[str] = None
) -> List[Dict]:
    """Get metrics broken down by payment channel"""

    query = select(
        Transaction.channel,
        func.count(Transaction.id).label('transaction_count'),
        func.coalesce(func.sum(
            case((Transaction.status == TransactionStatus.SUCCESS, Transaction.amount), else_=0)
        ), 0).label('total_revenue'),
        func.count(case((Transaction.status == TransactionStatus.SUCCESS, 1))).label('successful_count')
    ).where(
        Transaction.merchant_id == merchant_id,
        Transaction.mode == mode,
        Transaction.type == TransactionType.CREDIT
    ).group_by(Transaction.channel)

    if start_date:
        query = query.where(Transaction.created_at >= start_date)
    if end_date:
        query = query.where(Transaction.created_at <= end_date)
    if currency:
        query = query.where(Transaction.currency == currency)

    result = await session.execute(query)

    breakdown = []
    for row in result:
        transaction_count = row.transaction_count or 0
        successful_count = row.successful_count or 0
        success_rate = (successful_count / transaction_count * 100) if transaction_count > 0 else 0

        breakdown.append({
            "channel": row.channel or "unknown",
            "total_revenue": float(row.total_revenue or 0),
            "transaction_count": transaction_count,
            "success_rate": success_rate
        })

    return breakdown


async def get_time_series_data(
    session: AsyncSession,
    merchant_id: str,
    mode: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    currency: Optional[str] = None,
    interval: str = "day"  # day, week, month
) -> List[Dict]:
    """Get time series data for revenue/transactions"""

    if interval == "day":
        date_trunc = func.date_trunc('day', Transaction.created_at)
    elif interval == "week":
        date_trunc = func.date_trunc('week', Transaction.created_at)
    elif interval == "month":
        date_trunc = func.date_trunc('month', Transaction.created_at)
    else:
        date_trunc = func.date_trunc('day', Transaction.created_at)

    query = select(
        date_trunc.label('date'),
        func.coalesce(func.sum(
            case((Transaction.status == TransactionStatus.SUCCESS, Transaction.amount), else_=0)
        ), 0).label('value'),
        func.count(Transaction.id).label('count')
    ).where(
        Transaction.merchant_id == merchant_id,
        Transaction.mode == mode,
        Transaction.type == TransactionType.CREDIT
    ).group_by('date').order_by('date')

    if start_date:
        query = query.where(Transaction.created_at >= start_date)
    if end_date:
        query = query.where(Transaction.created_at <= end_date)
    if currency:
        query = query.where(Transaction.currency == currency)

    result = await session.execute(query)

    time_series = []
    for row in result:
        time_series.append({
            "date": row.date.isoformat() if row.date else None,
            "value": float(row.value or 0),
            "count": row.count or 0
        })

    return time_series


async def get_wallet_analytics(
    session: AsyncSession,
    merchant_id: str,
    mode: str
) -> List[Dict]:
    """Get analytics for all merchant wallets"""

    # Get all wallets for merchant
    wallet_query = select(Wallet).where(
        Wallet.merchant_id == merchant_id,
        Wallet.mode == mode
    )
    wallet_result = await session.execute(wallet_query)
    wallets = wallet_result.scalars().all()

    analytics = []

    for wallet in wallets:
        # Get credits (incoming payments)
        credit_query = select(
            func.coalesce(func.sum(Transaction.amount), 0).label('total_credits'),
            func.count(Transaction.id).label('credit_count')
        ).where(
            Transaction.wallet_id == wallet.id,
            Transaction.type == TransactionType.CREDIT,
            Transaction.status == TransactionStatus.SUCCESS
        )
        credit_result = await session.execute(credit_query)
        credit_row = credit_result.first()

        # Get debits (payouts)
        debit_query = select(
            func.coalesce(func.sum(Transaction.amount), 0).label('total_debits'),
            func.count(Transaction.id).label('debit_count')
        ).where(
            Transaction.wallet_id == wallet.id,
            Transaction.type == TransactionType.DEBIT,
            Transaction.status == TransactionStatus.SUCCESS
        )
        debit_result = await session.execute(debit_query)
        debit_row = debit_result.first()

        # Get total charges earned
        charge_query = select(
            func.coalesce(func.sum(Transaction.charge), 0).label('total_charges')
        ).where(
            Transaction.wallet_id == wallet.id,
            Transaction.status == TransactionStatus.SUCCESS
        )
        charge_result = await session.execute(charge_query)
        charge_row = charge_result.first()

        total_credits = float(credit_row.total_credits or 0)
        total_debits = float(debit_row.total_debits or 0)

        analytics.append({
            "wallet_id": wallet.id,
            "currency": wallet.currency,
            "current_balance": wallet.balance,
            "total_credits": total_credits,
            "total_debits": total_debits,
            "credit_count": credit_row.credit_count or 0,
            "debit_count": debit_row.debit_count or 0,
            "total_charges_earned": float(charge_row.total_charges or 0),
            "net_flow": total_credits - total_debits
        })

    return analytics


async def get_top_customers(
    session: AsyncSession,
    merchant_id: str,
    mode: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 10
) -> List[Dict]:
    """Get top customers by transaction volume"""

    query = select(
        Customer.email,
        func.coalesce(func.sum(
            case((Transaction.status == TransactionStatus.SUCCESS, Transaction.amount), else_=0)
        ), 0).label('total_spent'),
        func.count(Transaction.id).label('transaction_count'),
        func.max(Transaction.created_at).label('last_transaction_date')
    ).join(
        Transaction, Transaction.customer_id == Customer.id
    ).where(
        Transaction.merchant_id == merchant_id,
        Transaction.mode == mode,
        Transaction.type == TransactionType.CREDIT
    ).group_by(Customer.email).order_by(desc('total_spent')).limit(limit)

    if start_date:
        query = query.where(Transaction.created_at >= start_date)
    if end_date:
        query = query.where(Transaction.created_at <= end_date)

    result = await session.execute(query)

    top_customers = []
    for row in result:
        top_customers.append({
            "customer_email": row.email,
            "total_spent": float(row.total_spent or 0),
            "transaction_count": row.transaction_count or 0,
            "last_transaction_date": row.last_transaction_date
        })

    return top_customers


async def get_customer_analytics(
    session: AsyncSession,
    merchant_id: str,
    mode: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict:
    """Get customer analytics"""

    # Total customers
    total_customers_query = select(func.count(func.distinct(Transaction.customer_id))).where(
        Transaction.merchant_id == merchant_id,
        Transaction.mode == mode
    )
    total_result = await session.execute(total_customers_query)
    total_customers = total_result.scalar() or 0

    # Active customers in period
    active_query = select(func.count(func.distinct(Transaction.customer_id))).where(
        Transaction.merchant_id == merchant_id,
        Transaction.mode == mode
    )
    if start_date:
        active_query = active_query.where(Transaction.created_at >= start_date)
    if end_date:
        active_query = active_query.where(Transaction.created_at <= end_date)

    active_result = await session.execute(active_query)
    active_customers = active_result.scalar() or 0

    # Repeat customers (customers with more than 1 transaction)
    repeat_query = select(
        func.count().label('repeat_count')
    ).select_from(
        select(
            Transaction.customer_id,
            func.count(Transaction.id).label('txn_count')
        ).where(
            Transaction.merchant_id == merchant_id,
            Transaction.mode == mode,
            Transaction.status == TransactionStatus.SUCCESS
        ).group_by(Transaction.customer_id).having(func.count(Transaction.id) > 1).subquery()
    )

    repeat_result = await session.execute(repeat_query)
    repeat_customers = repeat_result.scalar() or 0

    repeat_rate = (repeat_customers / total_customers * 100) if total_customers > 0 else 0

    return {
        "total_customers": total_customers,
        "active_customers": active_customers,
        "new_customers": 0,  # Would need customer creation tracking
        "repeat_customer_rate": repeat_rate
    }


async def get_payout_analytics(
    session: AsyncSession,
    merchant_id: str,
    mode: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    currency: Optional[str] = None
) -> Dict:
    """Get payout analytics"""

    query = select(
        func.coalesce(func.sum(
            case((Transaction.status == TransactionStatus.SUCCESS, Transaction.amount), else_=0)
        ), 0).label('total_payouts'),
        func.count(Transaction.id).label('payout_count'),
        func.count(case((Transaction.status == TransactionStatus.SUCCESS, 1))).label('successful'),
        func.count(case((Transaction.status == TransactionStatus.FAILED, 1))).label('failed'),
        func.count(case((Transaction.status == TransactionStatus.PENDING, 1))).label('pending'),
        func.coalesce(func.sum(
            case((Transaction.status == TransactionStatus.SUCCESS, Transaction.charge), else_=0)
        ), 0).label('total_charges')
    ).where(
        Transaction.merchant_id == merchant_id,
        Transaction.mode == mode,
        Transaction.type == TransactionType.DEBIT
    )

    if start_date:
        query = query.where(Transaction.created_at >= start_date)
    if end_date:
        query = query.where(Transaction.created_at <= end_date)
    if currency:
        query = query.where(Transaction.currency == currency)

    result = await session.execute(query)
    row = result.first()

    total_payouts = float(row.total_payouts or 0)
    payout_count = row.payout_count or 0
    successful = row.successful or 0

    return {
        "total_payouts": total_payouts,
        "payout_count": payout_count,
        "successful_payouts": successful,
        "failed_payouts": row.failed or 0,
        "pending_payouts": row.pending or 0,
        "total_payout_charges": float(row.total_charges or 0),
        "average_payout_amount": total_payouts / successful if successful > 0 else 0
    }


async def get_transaction_patterns(
    session: AsyncSession,
    merchant_id: str,
    mode: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict:
    """Get transaction patterns (hourly, day of week)"""

    # Hourly distribution
    hourly_query = select(
        extract('hour', Transaction.created_at).label('hour'),
        func.count(Transaction.id).label('transaction_count'),
        func.coalesce(func.sum(
            case((Transaction.status == TransactionStatus.SUCCESS, Transaction.amount), else_=0)
        ), 0).label('total_revenue')
    ).where(
        Transaction.merchant_id == merchant_id,
        Transaction.mode == mode
    ).group_by('hour').order_by('hour')

    if start_date:
        hourly_query = hourly_query.where(Transaction.created_at >= start_date)
    if end_date:
        hourly_query = hourly_query.where(Transaction.created_at <= end_date)

    hourly_result = await session.execute(hourly_query)

    hourly_distribution = []
    for row in hourly_result:
        hourly_distribution.append({
            "hour": int(row.hour) if row.hour else 0,
            "transaction_count": row.transaction_count or 0,
            "total_revenue": float(row.total_revenue or 0)
        })

    # Day of week distribution
    dow_query = select(
        extract('dow', Transaction.created_at).label('dow'),
        func.count(Transaction.id).label('transaction_count'),
        func.coalesce(func.sum(
            case((Transaction.status == TransactionStatus.SUCCESS, Transaction.amount), else_=0)
        ), 0).label('total_revenue')
    ).where(
        Transaction.merchant_id == merchant_id,
        Transaction.mode == mode
    ).group_by('dow').order_by('dow')

    if start_date:
        dow_query = dow_query.where(Transaction.created_at >= start_date)
    if end_date:
        dow_query = dow_query.where(Transaction.created_at <= end_date)

    dow_result = await session.execute(dow_query)

    day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    day_distribution = []

    for row in dow_result:
        day_num = int(row.dow) if row.dow is not None else 0
        day_distribution.append({
            "day": day_names[day_num],
            "transaction_count": row.transaction_count or 0,
            "total_revenue": float(row.total_revenue or 0)
        })

    # Find peak hour and day
    peak_hour = max(hourly_distribution, key=lambda x: x['transaction_count'])['hour'] if hourly_distribution else 0
    peak_day = max(day_distribution, key=lambda x: x['transaction_count'])['day'] if day_distribution else 'Unknown'

    return {
        "hourly_distribution": hourly_distribution,
        "day_of_week_distribution": day_distribution,
        "peak_hour": peak_hour,
        "peak_day": peak_day
    }
