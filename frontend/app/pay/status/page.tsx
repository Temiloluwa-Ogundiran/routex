import { SiteFooter } from "../../../components/layout/site-footer";
import { SiteHeader } from "../../../components/layout/site-header";
import { PaymentStatusShell } from "../../../components/pay/payment-status-shell";

type PaymentStatus = "success" | "pending" | "failed";

type PaymentStatusPageProps = {
  searchParams: Promise<{
    gateway_reference?: string;
    next?: string;
    reference?: string;
    selected_gateway?: string;
    status?: string;
  }>;
};

function normalizeStatus(status: string | undefined): PaymentStatus {
  if (status === "success" || status === "failed") {
    return status;
  }
  return "pending";
}

export default async function PaymentStatusPage({
  searchParams,
}: PaymentStatusPageProps) {
  const params = await searchParams;

  return (
    <div className="site-shell">
      <SiteHeader />
      <main className="payment-status-shell">
        <PaymentStatusShell
          gatewayReference={
            params.gateway_reference ?? "Awaiting gateway confirmation"
          }
          nextDestination={params.next ?? null}
          reference={params.reference ?? "Unavailable"}
          selectedGateway={params.selected_gateway ?? null}
          status={normalizeStatus(params.status)}
        />
      </main>
      <SiteFooter />
    </div>
  );
}
