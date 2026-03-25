import { redirect } from "next/navigation";

export default async function TransactionDetailPage({
  searchParams,
}: {
  searchParams: Promise<{ created_at?: string | string[] }>;
}) {
  const query = await searchParams;
  const createdAt = Array.isArray(query.created_at)
    ? query.created_at[0]
    : query.created_at;
  const suffix = createdAt
    ? `?created_at=${encodeURIComponent(createdAt)}`
    : "";

  redirect(`/dashboard${suffix}`);
}
