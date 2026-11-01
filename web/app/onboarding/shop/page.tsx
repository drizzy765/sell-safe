import Link from "next/link";

import { ConfirmShopForm } from "@/components/ConfirmShopForm";
import { SellSafeLogo } from "@/components/SellSafeLogo";

export default function OnboardingShopPage() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto flex h-14 max-w-3xl items-center justify-between px-4">
          <Link href="/" aria-label="Sell-Safe home">
            <SellSafeLogo height={26} />
          </Link>
          <Link href="/?platform=instagram" className="text-sm text-muted-foreground hover:text-foreground">
            Instagram connect
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-3xl px-4 py-10">
        <p className="mb-2 text-sm text-muted-foreground">Step 1 · Confirm your shop</p>
        <ConfirmShopForm />
      </main>
    </div>
  );
}
