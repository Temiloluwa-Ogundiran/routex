import Link from "next/link";

import type { RouterTransaction } from "../../lib/dashboard-api";

type RecentTransactionsProps = {
  transactions: RouterTransaction[];
};

function formatAmount(amount: number, currency: string) {
  return new Intl.NumberFormat("en-NG", {
    style: "currency",
    currency,
    maximumFractionDigits: 0,
  }).format(amount);
}

export function RecentTransactions({ transactions }: RecentTransactionsProps) {
  return (
    <section className="dashboard-section">
      <div className="section-heading section-heading--split">
        <div>
          <p className="section-kicker">Recent Routed Activity</p>
          <h2>Recent Transactions</h2>
        </div>
        <p className="inline-link">Merchant-facing references with router outcomes.</p>
      </div>

      <div className="dashboard-table-shell">
        <div className="dashboard-table dashboard-table--header">
          <span>Reference</span>
          <span>Gateway</span>
          <span>Status</span>
          <span>Amount</span>
          <span>Created</span>
        </div>

        {transactions.map((transaction) => (
          <div className="dashboard-table" key={transaction.reference}>
            <strong>
              <Link
                className="inline-link"
                href={{
                  pathname: `/admin/transactions/${transaction.reference}`,
                  query: {
                    created_at: transaction.created_at,
                  },
                }}
              >
                View {transaction.reference}
              </Link>
            </strong>
            <span>{transaction.selected_gateway ?? "unassigned"}</span>
            <span className={`dashboard-status-chip dashboard-status-chip--${transaction.status}`}>
              {transaction.status}
            </span>
            <span>{formatAmount(transaction.amount, transaction.currency)}</span>
            <time dateTime={transaction.created_at}>
              {new Date(transaction.created_at).toLocaleTimeString("en-NG", {
                hour: "2-digit",
                minute: "2-digit",
              })}
            </time>
          </div>
        ))}
      </div>
    </section>
  );
}
