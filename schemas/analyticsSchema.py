from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime


# ------------------------------
# Analytics Response Schemas
# ------------------------------

class RevenueMetrics(BaseModel):
    """Revenue metrics for a period"""
    total_revenue: float
    total_transactions: int
    total_charges: float
    net_revenue: float  # revenue - charges
    average_transaction_value: float
    success_rate: float  # percentage


class TransactionBreakdown(BaseModel):
    """Transaction breakdown by status"""
    successful: int
    pending: int
    failed: int
    total: int


class CurrencyMetrics(BaseModel):
    """Metrics for a specific currency"""
    currency: str
    total_revenue: float
    transaction_count: int
    total_charges: float
    net_revenue: float
    average_transaction_value: float


class ChannelMetrics(BaseModel):
    """Metrics for a specific payment channel"""
    channel: str
    total_revenue: float
    transaction_count: int
    success_rate: float


class TimeSeriesDataPoint(BaseModel):
    """Single data point in time series"""
    date: str  # ISO format date
    value: float
    count: int


class WalletAnalytics(BaseModel):
    """Analytics for a specific wallet"""
    wallet_id: int
    currency: str
    current_balance: float
    total_credits: float
    total_debits: float
    credit_count: int
    debit_count: int
    total_charges_earned: float
    net_flow: float  # credits - debits


class TopCustomer(BaseModel):
    """Top customer by transaction volume"""
    customer_email: str
    total_spent: float
    transaction_count: int
    last_transaction_date: datetime


class DashboardSummaryResponse(BaseModel):
    """Comprehensive dashboard summary"""
    mode: str
    period: str  # today, week, month, year, all_time
    revenue_metrics: RevenueMetrics
    transaction_breakdown: TransactionBreakdown
    top_currency: Optional[CurrencyMetrics]
    wallet_count: int
    total_balance: float
    pending_payouts: int
    pending_payout_amount: float


class RevenueAnalyticsResponse(BaseModel):
    """Revenue analytics with time series"""
    mode: str
    start_date: Optional[str]
    end_date: Optional[str]
    currency: Optional[str]
    revenue_metrics: RevenueMetrics
    time_series: List[TimeSeriesDataPoint]
    currency_breakdown: List[CurrencyMetrics]


class TransactionAnalyticsResponse(BaseModel):
    """Transaction analytics"""
    mode: str
    start_date: Optional[str]
    end_date: Optional[str]
    currency: Optional[str]
    transaction_breakdown: TransactionBreakdown
    channel_breakdown: List[ChannelMetrics]
    time_series: List[TimeSeriesDataPoint]
    average_processing_time: Optional[float]  # in seconds


class WalletAnalyticsResponse(BaseModel):
    """Wallet analytics response"""
    mode: str
    wallets: List[WalletAnalytics]
    total_balance: float
    total_credits: float
    total_debits: float
    total_charges_earned: float
    currency_count: int


class CustomerAnalyticsResponse(BaseModel):
    """Customer analytics response"""
    mode: str
    start_date: Optional[str]
    end_date: Optional[str]
    total_customers: int
    active_customers: int  # customers with transactions in period
    new_customers: int  # customers created in period
    top_customers: List[TopCustomer]
    repeat_customer_rate: float  # percentage


class PayoutAnalyticsResponse(BaseModel):
    """Payout analytics response"""
    mode: str
    start_date: Optional[str]
    end_date: Optional[str]
    currency: Optional[str]
    total_payouts: float
    payout_count: int
    successful_payouts: int
    failed_payouts: int
    pending_payouts: int
    total_payout_charges: float
    average_payout_amount: float
    time_series: List[TimeSeriesDataPoint]


class ComparisonMetrics(BaseModel):
    """Comparison metrics between periods"""
    current_period: RevenueMetrics
    previous_period: RevenueMetrics
    revenue_change: float  # percentage
    transaction_change: float  # percentage
    success_rate_change: float  # percentage points


class GrowthAnalyticsResponse(BaseModel):
    """Growth analytics comparing periods"""
    mode: str
    current_period: str
    previous_period: str
    comparison: ComparisonMetrics
    growth_trend: str  # up, down, stable


class HourlyDistribution(BaseModel):
    """Transaction distribution by hour"""
    hour: int  # 0-23
    transaction_count: int
    total_revenue: float


class DayOfWeekDistribution(BaseModel):
    """Transaction distribution by day of week"""
    day: str  # Monday, Tuesday, etc.
    transaction_count: int
    total_revenue: float


class TransactionPatternResponse(BaseModel):
    """Transaction pattern analytics"""
    mode: str
    start_date: Optional[str]
    end_date: Optional[str]
    hourly_distribution: List[HourlyDistribution]
    day_of_week_distribution: List[DayOfWeekDistribution]
    peak_hour: int
    peak_day: str
    average_daily_transactions: float


class PerformanceMetrics(BaseModel):
    """Performance metrics"""
    mode: str
    period: str
    total_volume_processed: float
    total_transactions_processed: int
    uptime_percentage: float  # based on successful vs failed
    average_response_time: Optional[float]
    fastest_channel: Optional[str]
    slowest_channel: Optional[str]


class ExportMetrics(BaseModel):
    """Metrics for data export"""
    format: str  # csv, json, pdf
    data_type: str  # transactions, analytics, etc.
    record_count: int
    generated_at: datetime
