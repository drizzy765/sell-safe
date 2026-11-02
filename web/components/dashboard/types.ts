export type Product = {
  id: string;
  name: string;
  price_ngn: number | null;
  category: string;
  description: string;
  image_urls: string[];
  stock_status: string;
  status: string;
  flags?: string[];
  confidence?: number;
};

export type MediaItem = {
  id: string;
  kind: string;
  filename: string;
  url: string;
  caption: string;
  source: string;
  content_type: string;
};

export type Conversation = {
  id: string;
  buyer_id: string;
  channel: string;
  buyer: string;
  buyer_external_id?: string;
  language?: string;
  preview: string;
  reply?: string;
  at?: string;
  created_at?: string | null;
  demo?: boolean;
  unread?: number;
  paused?: boolean;
  folder?: string;
  reply_mode?: string;
};

export type ThreadMessage = {
  id: string;
  direction: string;
  type: string;
  text: string;
  media_url?: string;
  meta?: {
    status?: string;
    mode?: string;
    product?: {
      name?: string;
      price_ngn?: number;
      image_url?: string;
      description?: string;
    };
    verdict?: string;
    reasons?: string[];
  } | null;
  created_at?: string;
};

export type ReplyDraft = {
  id: string;
  buyer_id: string;
  customer_text: string;
  draft_text: string;
  mode: string;
  status: string;
  product?: {
    name?: string;
    price_ngn?: number;
    image_url?: string;
    description?: string;
  } | null;
};

export type Thread = {
  buyer_id: string;
  buyer: string;
  buyer_external_id: string;
  channel: string;
  paused: boolean;
  reply_mode: string;
  global_reply_mode: string;
  folder: string;
  window: { open: boolean; hours_left: number; warn: string | null };
  messages: ThreadMessage[];
  drafts: ReplyDraft[];
};

export type DashboardSettings = {
  reply_mode: string;
  smart_threshold_ngn: number;
  demo_mode: boolean;
  seller_email: string;
  catalog_skipped: boolean;
};

/** Shop profile from summary / onboarding (account number never returned raw). */
export type ShopProfile = {
  id: string;
  name: string;
  handle: string;
  category?: string;
  logo_url?: string;
  reply_mode?: string;
  phone?: string;
  location?: string;
  delivery_areas?: string;
  bank_name?: string;
  account_name?: string;
  account_number_masked?: string;
  account_number_set?: boolean;
  bio?: string;
  website?: string;
};

export type Summary = {
  shop: ShopProfile | null;
  stats: {
    chats_today: number;
    orders: number;
    naira_verified: number;
    fakes_caught: number;
    avg_reply_seconds: number;
    unread_inbox?: number;
    pending_drafts?: number;
    demo?: boolean;
  };
  products: Product[];
  drafts: Product[];
  media: MediaItem[];
  inbox: Conversation[];
  receipts: { id: string; verdict: string; amount_ngn: number; reasons: string[]; demo?: boolean }[];
  reply_drafts?: ReplyDraft[];
  settings: DashboardSettings;
  demo_mode: boolean;
  session_username?: string;
  inbox_sync?: {
    attempted?: boolean;
    ok?: boolean;
    conversations?: number;
    inserted?: number;
    error?: string | null;
    endpoint?: string | null;
  };
};

export type NavTab = "inbox" | "catalog" | "orders" | "outreach" | "settings";

export function formatNaira(amount: number | null | undefined) {
  if (amount == null) return "—";
  return `₦${amount.toLocaleString("en-NG")}`;
}

export function formatTime(iso?: string | null) {
  if (!iso) return "";
  if (iso.startsWith("today")) return iso.replace("today ", "");
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString("en-NG", { hour: "numeric", minute: "2-digit" });
  } catch {
    return "";
  }
}

export function initials(name: string) {
  const parts = (name || "?").replace("@", "").split(/[._\s-]+/).filter(Boolean);
  return ((parts[0]?.[0] || "?") + (parts[1]?.[0] || "")).toUpperCase();
}
