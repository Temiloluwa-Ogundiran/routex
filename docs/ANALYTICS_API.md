# Analytics API Documentation

## Overview
The Analytics API provides comprehensive business insights for merchants. It offers flexible endpoints for analyzing revenue, transactions, customers, wallets, and performance metrics.

## Authentication
All analytics endpoints require user authentication via Bearer token.

## Base URL
```
/analytics
```

---

## Endpoints

### 1. Dashboard Summary
**GET** `/analytics/dashboard`

Get a comprehensive dashboard summary with key metrics for quick overview.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| merchant_id | string | Yes | Merchant ID |
| mode | string | No | Mode: `test` or `live` (default: `test`) |
| period | string | No | Period: `today`, `week`, `month`, `quarter`, `year`, `all_time` (default: `month`) |

#### Response
```json
{
  "mode": "test",
  "period": "month",
  "revenue_metrics": {
    "total_revenue": 150000.50,
    "total_transactions": 450,
    "total_charges": 3500.00,
    "net_revenue": 146500.50,
    "average_transaction_value": 333.33,
    "success_rate": 95.5
  },
  "transaction_breakdown": {
    "successful": 430,
    "pending": 5,
    "failed": 15,
    "total": 450
  },
  "top_currency": {
    "currency": "NGN",
    "total_revenue": 100000.00,
    "transaction_count": 300,
    "total_charges": 2000.00,
    "net_revenue": 98000.00,
    "average_transaction_value": 333.33
  },
  "wallet_count": 3,
  "total_balance": 50000.00,
  "pending_payouts": 2,
  "pending_payout_amount": 5000.00
}
```

#### Use Cases
- Quick overview dashboard
- Real-time business health monitoring
- Executive summary reports

---

### 2. Revenue Analytics
**GET** `/analytics/revenue`

Get detailed revenue analytics with time series data and currency breakdown.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| merchant_id | string | Yes | Merchant ID |
| mode | string | No | Mode: `test` or `live` (default: `test`) |
| start_date | string | No | Start date (ISO format: `2024-01-01T00:00:00`) |
| end_date | string | No | End date (ISO format) |
| currency | string | No | Filter by specific currency (e.g., `NGN`, `USD`) |
| interval | string | No | Time series interval: `day`, `week`, `month` (default: `day`) |

#### Response
```json
{
  "mode": "test",
  "start_date": "2024-01-01T00:00:00",
  "end_date": "2024-01-31T23:59:59",
  "currency": null,
  "revenue_metrics": {
    "total_revenue": 150000.50,
    "total_transactions": 450,
    "total_charges": 3500.00,
    "net_revenue": 146500.50,
    "average_transaction_value": 333.33,
    "success_rate": 95.5
  },
  "time_series": [
    {
      "date": "2024-01-01T00:00:00",
      "value": 5000.00,
      "count": 15
    },
    {
      "date": "2024-01-02T00:00:00",
      "value": 6500.00,
      "count": 18
    }
  ],
  "currency_breakdown": [
    {
      "currency": "NGN",
      "total_revenue": 100000.00,
      "transaction_count": 300,
      "total_charges": 2000.00,
      "net_revenue": 98000.00,
      "average_transaction_value": 333.33
    },
    {
      "currency": "USD",
      "total_revenue": 50000.50,
      "transaction_count": 150,
      "total_charges": 1500.00,
      "net_revenue": 48500.50,
      "average_transaction_value": 333.34
    }
  ]
}
```

#### Use Cases
- Revenue trend analysis
- Financial reporting
- Currency performance comparison
- Forecasting and budgeting

---

### 3. Transaction Analytics
**GET** `/analytics/transactions`

Get detailed transaction analytics including channel breakdown and patterns.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| merchant_id | string | Yes | Merchant ID |
| mode | string | No | Mode: `test` or `live` (default: `test`) |
| start_date | string | No | Start date (ISO format) |
| end_date | string | No | End date (ISO format) |
| currency | string | No | Filter by currency |
| interval | string | No | Time series interval: `day`, `week`, `month` |

#### Response
```json
{
  "mode": "test",
  "start_date": "2024-01-01T00:00:00",
  "end_date": "2024-01-31T23:59:59",
  "currency": null,
  "transaction_breakdown": {
    "successful": 430,
    "pending": 5,
    "failed": 15,
    "total": 450
  },
  "channel_breakdown": [
    {
      "channel": "mobile_money",
      "total_revenue": 80000.00,
      "transaction_count": 250,
      "success_rate": 96.0
    },
    {
      "channel": "bank_transfer",
      "total_revenue": 70000.50,
      "transaction_count": 200,
      "success_rate": 95.0
    }
  ],
  "time_series": [...],
  "average_processing_time": null
}
```

#### Use Cases
- Channel performance analysis
- Success rate monitoring
- Transaction volume tracking
- Payment method optimization

---

### 4. Wallet Analytics
**GET** `/analytics/wallets`

Get comprehensive analytics for all merchant wallets.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| merchant_id | string | Yes | Merchant ID |
| mode | string | No | Mode: `test` or `live` (default: `test`) |

#### Response
```json
{
  "mode": "test",
  "wallets": [
    {
      "wallet_id": 1,
      "currency": "NGN",
      "current_balance": 25000.00,
      "total_credits": 100000.00,
      "total_debits": 75000.00,
      "credit_count": 300,
      "debit_count": 50,
      "total_charges_earned": 2000.00,
      "net_flow": 25000.00
    },
    {
      "wallet_id": 2,
      "currency": "USD",
      "current_balance": 15000.00,
      "total_credits": 50000.00,
      "total_debits": 35000.00,
      "credit_count": 150,
      "debit_count": 30,
      "total_charges_earned": 1500.00,
      "net_flow": 15000.00
    }
  ],
  "total_balance": 40000.00,
  "total_credits": 150000.00,
  "total_debits": 110000.00,
  "total_charges_earned": 3500.00,
  "currency_count": 2
}
```

#### Use Cases
- Multi-currency balance monitoring
- Cash flow analysis
- Wallet performance comparison
- Charge revenue tracking

---

### 5. Customer Analytics
**GET** `/analytics/customers`

Get customer analytics including top customers and retention metrics.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| merchant_id | string | Yes | Merchant ID |
| mode | string | No | Mode: `test` or `live` (default: `test`) |
| start_date | string | No | Start date (ISO format) |
| end_date | string | No | End date (ISO format) |
| top_limit | integer | No | Number of top customers to return (default: 10) |

#### Response
```json
{
  "mode": "test",
  "start_date": "2024-01-01T00:00:00",
  "end_date": "2024-01-31T23:59:59",
  "total_customers": 150,
  "active_customers": 120,
  "new_customers": 0,
  "top_customers": [
    {
      "customer_email": "customer1@example.com",
      "total_spent": 15000.00,
      "transaction_count": 45,
      "last_transaction_date": "2024-01-30T15:30:00"
    },
    {
      "customer_email": "customer2@example.com",
      "total_spent": 12000.00,
      "transaction_count": 38,
      "last_transaction_date": "2024-01-29T10:20:00"
    }
  ],
  "repeat_customer_rate": 65.5
}
```

#### Use Cases
- Customer lifetime value analysis
- Loyalty program planning
- Customer segmentation
- Retention strategy

---

### 6. Payout Analytics
**GET** `/analytics/payouts`

Get detailed payout analytics with time series data.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| merchant_id | string | Yes | Merchant ID |
| mode | string | No | Mode: `test` or `live` (default: `test`) |
| start_date | string | No | Start date (ISO format) |
| end_date | string | No | End date (ISO format) |
| currency | string | No | Filter by currency |
| interval | string | No | Time series interval: `day`, `week`, `month` |

#### Response
```json
{
  "mode": "test",
  "start_date": "2024-01-01T00:00:00",
  "end_date": "2024-01-31T23:59:59",
  "currency": null,
  "total_payouts": 75000.00,
  "payout_count": 80,
  "successful_payouts": 75,
  "failed_payouts": 3,
  "pending_payouts": 2,
  "total_payout_charges": 1500.00,
  "average_payout_amount": 1000.00,
  "time_series": [...]
}
```

#### Use Cases
- Payout volume tracking
- Cost analysis (payout charges)
- Success rate monitoring
- Cash flow planning

---

### 7. Transaction Patterns
**GET** `/analytics/patterns`

Analyze transaction patterns by hour and day of week to identify peak times.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| merchant_id | string | Yes | Merchant ID |
| mode | string | No | Mode: `test` or `live` (default: `test`) |
| start_date | string | No | Start date (ISO format) |
| end_date | string | No | End date (ISO format) |

#### Response
```json
{
  "mode": "test",
  "start_date": "2024-01-01T00:00:00",
  "end_date": "2024-01-31T23:59:59",
  "hourly_distribution": [
    {
      "hour": 0,
      "transaction_count": 5,
      "total_revenue": 1500.00
    },
    {
      "hour": 1,
      "transaction_count": 3,
      "total_revenue": 900.00
    },
    ...
    {
      "hour": 14,
      "transaction_count": 45,
      "total_revenue": 15000.00
    }
  ],
  "day_of_week_distribution": [
    {
      "day": "Monday",
      "transaction_count": 75,
      "total_revenue": 25000.00
    },
    {
      "day": "Tuesday",
      "transaction_count": 68,
      "total_revenue": 22000.00
    }
  ],
  "peak_hour": 14,
  "peak_day": "Monday",
  "average_daily_transactions": 15.0
}
```

#### Use Cases
- Resource allocation planning
- Marketing campaign timing
- Staff scheduling
- System capacity planning

---

### 8. Comparison Analytics
**GET** `/analytics/comparison`

Compare metrics between current and previous periods to track growth.

#### Query Parameters
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| merchant_id | string | Yes | Merchant ID |
| mode | string | No | Mode: `test` or `live` (default: `test`) |
| current_period | string | No | Current period: `week`, `month`, `quarter`, `year` (default: `month`) |
| compare_with | string | No | Compare with: `previous` (default: `previous`) |
| currency | string | No | Filter by currency |

#### Response
```json
{
  "mode": "test",
  "current_period": "month",
  "previous_period": "previous_month",
  "comparison": {
    "current_period": {
      "total_revenue": 150000.50,
      "total_transactions": 450,
      "total_charges": 3500.00,
      "net_revenue": 146500.50,
      "average_transaction_value": 333.33,
      "success_rate": 95.5
    },
    "previous_period": {
      "total_revenue": 120000.00,
      "total_transactions": 380,
      "total_charges": 3000.00,
      "net_revenue": 117000.00,
      "average_transaction_value": 315.79,
      "success_rate": 94.2
    },
    "revenue_change": 25.0,
    "transaction_change": 18.42,
    "success_rate_change": 1.3
  },
  "growth_trend": "up"
}
```

#### Use Cases
- Growth tracking
- Performance benchmarking
- Trend analysis
- Business planning

---

## Common Query Patterns

### Get Today's Performance
```
GET /analytics/dashboard?merchant_id=xxx&mode=live&period=today
```

### Compare This Month vs Last Month
```
GET /analytics/comparison?merchant_id=xxx&mode=live&current_period=month
```

### Analyze NGN Revenue for Q1
```
GET /analytics/revenue?merchant_id=xxx&mode=live&currency=NGN&start_date=2024-01-01T00:00:00&end_date=2024-03-31T23:59:59
```

### Find Peak Transaction Times
```
GET /analytics/patterns?merchant_id=xxx&mode=live&start_date=2024-01-01T00:00:00&end_date=2024-01-31T23:59:59
```

### Top 20 Customers This Quarter
```
GET /analytics/customers?merchant_id=xxx&mode=live&top_limit=20&start_date=2024-01-01T00:00:00&end_date=2024-03-31T23:59:59
```

---

## Error Responses

### 403 Forbidden
User doesn't belong to merchant
```json
{
  "detail": "User does not belong to merchant"
}
```

### 404 Not Found
Merchant not found
```json
{
  "detail": "Merchant not found"
}
```

---

## Best Practices

1. **Use Appropriate Time Ranges**: Don't query unnecessarily large date ranges for real-time dashboards
2. **Cache Results**: Cache analytics data for frequently accessed periods
3. **Filter by Currency**: Use currency filters when analyzing specific markets
4. **Leverage Intervals**: Use appropriate intervals (day/week/month) based on date range
5. **Monitor Peak Times**: Use pattern analytics to optimize resources and marketing
6. **Track Trends**: Use comparison endpoint regularly to monitor business growth
7. **Segment Customers**: Use customer analytics to identify and reward top customers

---

## Integration Example

```python
import requests

# Get comprehensive dashboard
response = requests.get(
    "https://api.xoropay.com/analytics/dashboard",
    params={
        "merchant_id": "merchant_123",
        "mode": "live",
        "period": "month"
    },
    headers={
        "Authorization": "Bearer YOUR_TOKEN_HERE"
    }
)

dashboard_data = response.json()
print(f"Total Revenue: {dashboard_data['revenue_metrics']['total_revenue']}")
print(f"Success Rate: {dashboard_data['revenue_metrics']['success_rate']}%")

# Get revenue trends
response = requests.get(
    "https://api.xoropay.com/analytics/revenue",
    params={
        "merchant_id": "merchant_123",
        "mode": "live",
        "interval": "day",
        "start_date": "2024-01-01T00:00:00",
        "end_date": "2024-01-31T23:59:59"
    },
    headers={
        "Authorization": "Bearer YOUR_TOKEN_HERE"
    }
)

revenue_data = response.json()
for point in revenue_data['time_series']:
    print(f"{point['date']}: {point['value']} ({point['count']} transactions)")
```

---

## Future Enhancements

Potential future additions to the analytics API:
- Export to CSV/PDF
- Scheduled reports via email
- Custom metric definitions
- Predictive analytics
- Anomaly detection
- Comparative industry benchmarks
- Real-time streaming analytics
- Custom dashboard widgets API
