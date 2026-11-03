"use client";

import { Mic } from "lucide-react";

import { useCallback, useEffect, useState } from "react";

import {
  Conversation,
  ReplyDraft,
  Thread,
  ThreadMessage,
  formatNaira,
  formatTime,
  initials,
} from "./types";

type InboxSync = {
  attempted?: boolean;
  ok?: boolean;
  conversations?: number;
  inserted?: number;
  error?: string | null;
  endpoint?: string | null;
};

type Props = {
  handle: string;
  replyMode: string;
  conversations: Conversation[];
  inboxSync?: InboxSync | null;
  onRefresh: () => Promise<void>;
  onModeChange: (mode: string) => Promise<void>;
};

export function InboxView({
  handle,
  replyMode,
  conversations,
  inboxSync,
  onRefresh,
  onModeChange,
}: Props) {
  const [folder, setFolder] = useState<"primary" | "general" | "requests">("primary");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [thread, setThread] = useState<Thread | null>(null);
  const [composer, setComposer] = useState("");
  const [editDraftId, setEditDraftId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const realConversations = conversations.filter((c) => !c.demo);
  const filtered = realConversations.filter((c) => {
    if (folder !== "primary" && (c.folder || "primary") !== folder) return false;
    if (!query.trim()) return true;
    const q = query.toLowerCase();
    return c.buyer.toLowerCase().includes(q) || (c.preview || "").toLowerCase().includes(q);
  });

  const loadThread = useCallback(async (buyerId: string) => {
    setError("");
    const response = await fetch(`/api/dashboard/inbox/${encodeURIComponent(buyerId)}`, {
      cache: "no-store",
    });
    const body = (await response.json().catch(() => ({}))) as Thread & { detail?: string };
    if (!response.ok) {
      setError(body.detail || "Could not load thread.");
      setThread(null);
      return;
    }
    setThread(body);
  }, []);

  useEffect(() => {
    if (!selectedId && filtered[0]) {
      setSelectedId(filtered[0].buyer_id || filtered[0].id);
    }
  }, [filtered, selectedId]);

  useEffect(() => {
    if (!selectedId) {
      setThread(null);
      return;
    }
    void loadThread(selectedId);
    const timer = setInterval(() => void loadThread(selectedId), 4000);
    return () => clearInterval(timer);
  }, [selectedId, loadThread]);

  async function takeover(paused: boolean) {
    if (!selectedId) return;
    setBusy(true);
    try {
      await fetch(`/api/dashboard/inbox/${encodeURIComponent(selectedId)}/takeover`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ paused }),
      });
      await loadThread(selectedId);
      await onRefresh();
    } finally {
      setBusy(false);
    }
  }

  async function sendManual() {
    if (!selectedId || !composer.trim()) return;
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`/api/dashboard/inbox/${encodeURIComponent(selectedId)}/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: composer.trim() }),
      });
      const body = (await response.json().catch(() => ({}))) as { detail?: string };
      if (!response.ok) {
        setError(body.detail || "Send failed.");
        return;
      }
      setComposer("");
      await loadThread(selectedId);
      await onRefresh();
    } finally {
      setBusy(false);
    }
  }

  async function approveDraft(id: string) {
    setBusy(true);
    setError("");
    try {
      const response = await fetch(`/api/dashboard/drafts/${encodeURIComponent(id)}/approve`, {
        method: "POST",
      });
      const body = (await response.json().catch(() => ({}))) as { detail?: string };
      if (!response.ok) {
        setError(body.detail || "Approve failed.");
        return;
      }
      if (selectedId) await loadThread(selectedId);
      await onRefresh();
    } finally {
      setBusy(false);
    }
  }

  async function rejectDraft(id: string) {
    setBusy(true);
    try {
      await fetch(`/api/dashboard/drafts/${encodeURIComponent(id)}/reject`, { method: "POST" });
      if (selectedId) await loadThread(selectedId);
      await onRefresh();
    } finally {
      setBusy(false);
    }
  }

  async function saveEdit(id: string) {
    setBusy(true);
    try {
      await fetch(`/api/dashboard/drafts/${encodeURIComponent(id)}/edit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: editText }),
      });
      setEditDraftId(null);
      if (selectedId) await loadThread(selectedId);
    } finally {
      setBusy(false);
    }
  }

  const mode = (thread?.reply_mode || replyMode || "auto").toUpperCase();

  return (
    <div className="flex h-[calc(100vh-0px)] min-h-[560px] overflow-hidden bg-white">
      {/* Conversation list */}
      <section className="flex w-[320px] shrink-0 flex-col border-r border-[#efefef]">
        <header className="flex items-center justify-between px-4 py-3">
          <h2 className="text-[15px] font-semibold text-[#262626]">@{handle || "shop"}</h2>
          <span className="text-xs text-[#8e8e8e]">▾</span>
        </header>
        <div className="flex gap-4 border-b border-[#efefef] px-4 text-sm">
          {(["primary", "general", "requests"] as const).map((tab) => (
            <button
              key={tab}
              type="button"
              onClick={() => setFolder(tab)}
              className={`-mb-px border-b-2 pb-2.5 capitalize ${
                folder === tab
                  ? "border-[#262626] font-semibold text-[#262626]"
                  : "border-transparent text-[#8e8e8e]"
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
        <div className="border-b border-[#efefef] px-3 py-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search"
            className="w-full rounded-lg bg-[#efefef] px-3 py-2 text-sm outline-none placeholder:text-[#8e8e8e]"
          />
        </div>
        <div className="flex-1 overflow-y-auto">
          {!filtered.length ? (
            <div className="flex h-full flex-col items-center justify-center px-6 text-center">
              <p className="text-sm font-medium text-[#262626]">No messages yet</p>
              <p className="mt-1 text-xs text-[#8e8e8e]">
                When buyers DM your Instagram, threads appear here — no demo chats.
              </p>
              {inboxSync?.error ? (
                <p className="mt-3 max-w-[260px] text-[11px] leading-snug text-[#ed4956]">
                  {inboxSync.error}
                </p>
              ) : null}
              {inboxSync?.attempted && !inboxSync.error && (inboxSync.conversations || 0) === 0 ? (
                <p className="mt-3 max-w-[260px] text-[11px] leading-snug text-[#8e8e8e]">
                  Meta returned 0 conversations. Add Testicles22 as an Instagram Tester, have
                  them DM @sellsafe.testshop.ng, then Refresh — no fake/demo threads.
                </p>
              ) : null}
              <button
                type="button"
                onClick={() => {
                  void (async () => {
                    setBusy(true);
                    try {
                      await fetch("/api/dashboard/inbox/pull", { method: "POST" });
                      await onRefresh();
                    } finally {
                      setBusy(false);
                    }
                  })();
                }}
                disabled={busy}
                className="mt-4 rounded-lg border border-[#dbdbdb] px-3 py-1.5 text-xs font-semibold text-[#262626] disabled:opacity-50"
              >
                {busy ? "Syncing…" : "Refresh inbox"}
              </button>
            </div>
          ) : (
            filtered.map((chat) => {
              const id = chat.buyer_id || chat.id;
              const active = id === selectedId;
              return (
                <button
                  key={id}
                  type="button"
                  onClick={() => setSelectedId(id)}
                  className={`flex w-full items-center gap-3 px-3 py-3 text-left hover:bg-[#fafafa] ${
                    active ? "bg-[#efefef]/70" : ""
                  }`}
                >
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[#f58529] via-[#dd2a7b] to-[#8134af] p-[2px]">
                    <div className="flex h-full w-full items-center justify-center rounded-full bg-white text-xs font-semibold text-[#262626]">
                      {initials(chat.buyer)}
                    </div>
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center justify-between gap-2">
                      <p className="truncate text-sm font-semibold text-[#262626]">{chat.buyer}</p>
                      <span className="shrink-0 text-[11px] text-[#8e8e8e]">
                        {formatTime(chat.created_at || chat.at)}
                      </span>
                    </div>
                    <p className="truncate text-xs text-[#8e8e8e]">{chat.preview}</p>
                  </div>
                  {(chat.unread || 0) > 0 ? (
                    <span className="h-2 w-2 shrink-0 rounded-full bg-[#0095f6]" />
                  ) : null}
                </button>
              );
            })
          )}
        </div>
      </section>

      {/* Thread */}
      <section className="flex min-w-0 flex-1 flex-col">
        {!selectedId || !thread ? (
          <div className="flex flex-1 flex-col items-center justify-center text-center">
            <div className="mb-3 flex h-16 w-16 items-center justify-center rounded-full border-2 border-[#262626]">
              <span className="text-2xl">✈</span>
            </div>
            <p className="text-lg font-light text-[#262626]">Your messages</p>
            <p className="mt-1 text-sm text-[#8e8e8e]">
              {realConversations.length
                ? "Select a conversation"
                : "No messages yet — your Instagram inbox is empty"}
            </p>
          </div>
        ) : (
          <>
            <header className="flex items-center justify-between border-b border-[#efefef] px-4 py-3">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[#efefef] text-xs font-semibold">
                  {initials(thread.buyer)}
                </div>
                <div>
                  <p className="text-sm font-semibold text-[#262626]">{thread.buyer}</p>
                  <p className="text-[11px] text-[#8e8e8e]">
                    {thread.paused ? "You took over" : "Active on Instagram"}
                  </p>
                </div>
              </div>
              <div className="flex flex-col items-end gap-1">
                <div className="flex items-center gap-2 rounded-full border border-[#dbdbdb] bg-white px-2 py-1 text-[11px]">
                  <span className="text-[#8e8e8e]">Sell-Safe · Muse</span>
                  {(["auto", "approve", "smart"] as const).map((m) => (
                    <button
                      key={m}
                      type="button"
                      disabled={busy}
                      onClick={() => void onModeChange(m)}
                      className={`rounded-full px-2 py-0.5 font-semibold uppercase ${
                        mode === m.toUpperCase()
                          ? "bg-[#0095f6] text-white"
                          : "text-[#8e8e8e] hover:bg-[#efefef]"
                      }`}
                    >
                      {m}
                    </button>
                  ))}
                </div>
                <p className="text-[11px] text-[#8e8e8e]">
                  {mode === "AUTO"
                    ? "AI is replying automatically"
                    : mode === "APPROVE"
                      ? "Replies wait for your approval"
                      : "Smart: simple Qs auto, sensitive ones need approve"}
                </p>
              </div>
            </header>

            {thread.window?.warn ? (
              <p className="border-b border-amber-200 bg-amber-50 px-4 py-2 text-xs text-amber-900">
                {thread.window.warn}
              </p>
            ) : null}
            {error ? (
              <p className="border-b border-red-200 bg-red-50 px-4 py-2 text-xs text-red-800">{error}</p>
            ) : null}

            <div className="flex-1 space-y-3 overflow-y-auto bg-[#fafafa] px-4 py-4">
              {thread.messages.map((msg) => (
                <MessageBubble key={msg.id} message={msg} />
              ))}
              {thread.drafts.map((draft) => (
                <DraftBubble
                  key={draft.id}
                  draft={draft}
                  busy={busy}
                  editing={editDraftId === draft.id}
                  editText={editText}
                  onEditStart={() => {
                    setEditDraftId(draft.id);
                    setEditText(draft.draft_text);
                  }}
                  onEditChange={setEditText}
                  onEditSave={() => void saveEdit(draft.id)}
                  onEditCancel={() => setEditDraftId(null)}
                  onApprove={() => void approveDraft(draft.id)}
                  onReject={() => void rejectDraft(draft.id)}
                />
              ))}
            </div>

            <footer className="border-t border-[#efefef] bg-white px-3 py-2">
              <div className="mb-2 flex gap-2">
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => void takeover(!thread.paused)}
                  className="rounded-full border border-[#dbdbdb] px-3 py-1 text-xs font-semibold text-[#262626] hover:bg-[#efefef]"
                >
                  {thread.paused ? "Hand back to Sell-Safe" : "Take over"}
                </button>
              </div>
              <div className="flex items-center gap-2 rounded-full border border-[#dbdbdb] px-3 py-2">
                <input
                  value={composer}
                  onChange={(e) => setComposer(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      void sendManual();
                    }
                  }}
                  placeholder="Message..."
                  className="min-w-0 flex-1 bg-transparent text-sm outline-none"
                  disabled={busy || !thread.window?.open}
                />
                <button
                  type="button"
                  disabled={busy || !composer.trim() || !thread.window?.open}
                  onClick={() => void sendManual()}
                  className="text-sm font-semibold text-[#0095f6] disabled:text-[#c7c7c7]"
                >
                  Send
                </button>
              </div>
            </footer>
          </>
        )}
      </section>
    </div>
  );
}

function MessageBubble({ message }: { message: ThreadMessage }) {
  const incoming = message.direction === "in";
  const isDraft = message.type === "draft" || message.meta?.status === "pending";
  const product = message.meta?.product;
  const verdict = message.meta?.verdict;

  if (isDraft) return null; // shown via drafts list

  return (
    <div className={`flex ${incoming ? "justify-start" : "justify-end"}`}>
      <div className={`max-w-[75%] space-y-2 ${incoming ? "" : "items-end"}`}>
        {message.media_url && message.type === "image" ? (
          <div className="overflow-hidden rounded-2xl border border-[#dbdbdb] bg-white">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={message.media_url} alt="" className="max-h-64 w-full object-cover [outline:1px_solid_oklch(0_0_0/0.1)] [outline-offset:-1px]" />
            {verdict ? (
              <div
                className={`border-t px-3 py-2 text-xs font-semibold ${
                  verdict === "CONFIRMED" || verdict === "Verified"
                    ? "border-emerald-200 bg-emerald-50 text-emerald-800"
                    : "border-red-200 bg-red-50 text-red-800"
                }`}
              >
                {verdict === "CONFIRMED" ? "Verified" : `Suspicious: ${(message.meta?.reasons || []).join(", ") || "check failed"}`}
              </div>
            ) : null}
          </div>
        ) : null}

        {message.type === "audio" || message.type === "voice" ? (
          <div
            className={`w-64 max-w-full rounded-2xl px-3.5 py-2.5 ${
              incoming ? "rounded-bl-md bg-[#efefef] text-[#262626]" : "rounded-br-md bg-[#efefef] text-[#262626]"
            }`}
          >
            <p className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wide text-[#6b6b80]">
              <Mic size={12} aria-hidden /> Voice note
            </p>
            {message.media_url ? (
              <audio controls preload="none" src={message.media_url} className="mt-1.5 w-full" aria-label="Play voice note" />
            ) : (
              <p className="mt-1 text-xs text-[#8e8e8e]">Audio unavailable in dashboard — listen in Instagram.</p>
            )}
            {message.text ? (
              <p className="mt-1.5 text-xs italic leading-snug text-[#52525b]">“{message.text}”</p>
            ) : null}
          </div>
        ) : null}

        {message.text && message.type !== "audio" && message.type !== "voice" ? (
          <div
            className={`rounded-2xl px-3.5 py-2 text-sm leading-snug ${
              incoming
                ? "rounded-bl-md bg-[#efefef] text-[#262626]"
                : "rounded-br-md bg-gradient-to-br from-[#5b6cff] to-[#8b5cf6] text-white"
            }`}
          >
            {message.text}
            {!incoming ? (
              <span className="mt-1 block text-right text-[10px] text-white/80">✓✓</span>
            ) : null}
          </div>
        ) : null}

        {product ? (
          <div className="w-56 overflow-hidden rounded-xl border border-[#dbdbdb] bg-white shadow-sm">
            {product.image_url ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={product.image_url} alt="" className="h-36 w-full object-cover [outline:1px_solid_oklch(0_0_0/0.1)] [outline-offset:-1px]" />
            ) : (
              <div className="flex h-36 items-center justify-center bg-[#f0f0f0] text-xs text-[#8e8e8e]">
                Product
              </div>
            )}
            <div className="space-y-0.5 p-2.5">
              <p className="text-sm font-semibold text-[#262626]">{product.name}</p>
              <p className="text-sm font-medium text-[#262626]">{formatNaira(product.price_ngn)}</p>
              {product.description ? (
                <p className="line-clamp-2 text-[11px] text-[#8e8e8e]">{product.description}</p>
              ) : null}
            </div>
          </div>
        ) : null}

        <p className={`text-[10px] text-[#8e8e8e] ${incoming ? "text-left" : "text-right"}`}>
          {formatTime(message.created_at)}
        </p>
      </div>
    </div>
  );
}

function DraftBubble({
  draft,
  busy,
  editing,
  editText,
  onEditStart,
  onEditChange,
  onEditSave,
  onEditCancel,
  onApprove,
  onReject,
}: {
  draft: ReplyDraft;
  busy: boolean;
  editing: boolean;
  editText: string;
  onEditStart: () => void;
  onEditChange: (v: string) => void;
  onEditSave: () => void;
  onEditCancel: () => void;
  onApprove: () => void;
  onReject: () => void;
}) {
  return (
    <div className="flex justify-end">
      <div className="max-w-[80%] rounded-2xl border border-dashed border-[#8b5cf6] bg-white p-3 shadow-sm">
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-wide text-[#8b5cf6]">
          Draft (pending your approval)
        </p>
        {editing ? (
          <textarea
            value={editText}
            onChange={(e) => onEditChange(e.target.value)}
            className="mb-2 w-full rounded-lg border border-[#dbdbdb] p-2 text-sm"
            rows={3}
          />
        ) : (
          <p className="mb-3 text-sm text-[#262626]">{draft.draft_text}</p>
        )}
        {draft.product ? (
          <p className="mb-3 text-xs text-[#8e8e8e]">
            Includes product card: {draft.product.name} · {formatNaira(draft.product.price_ngn)}
          </p>
        ) : null}
        <div className="flex flex-wrap gap-2">
          {editing ? (
            <>
              <button
                type="button"
                disabled={busy}
                onClick={onEditSave}
                className="rounded-lg bg-[#12a150] px-3 py-1.5 text-xs font-semibold text-white"
              >
                Save
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={onEditCancel}
                className="rounded-lg border border-[#dbdbdb] px-3 py-1.5 text-xs font-semibold"
              >
                Cancel
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                disabled={busy}
                onClick={onApprove}
                className="rounded-lg bg-[#12a150] px-3 py-1.5 text-xs font-semibold text-white"
              >
                Approve & send
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={onEditStart}
                className="rounded-lg border border-[#dbdbdb] px-3 py-1.5 text-xs font-semibold"
              >
                Edit
              </button>
              <button
                type="button"
                disabled={busy}
                onClick={onReject}
                className="rounded-lg border border-red-200 px-3 py-1.5 text-xs font-semibold text-red-600"
              >
                Reject
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
