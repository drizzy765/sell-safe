"use client";

import { useState } from "react";

export function WhatsAppWaitlist() {
  const [phoneNumber, setPhoneNumber] = useState("");
  const [status, setStatus] = useState<"idle" | "submitting" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  const validatePhone = (phone: string): boolean => {
    // Nigerian format: +234XXXXXXXXXX
    const regex = /^\+234[0-9]{10}$/;
    return regex.test(phone);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validatePhone(phoneNumber)) {
      setStatus("error");
      setMessage("Please enter a valid Nigerian number (+234XXXXXXXXXX)");
      return;
    }

    setStatus("submitting");
    
    try {
      const response = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone_number: phoneNumber }),
      });
      
      if (response.ok) {
        setStatus("success");
        setMessage("You'll be notified on WhatsApp when it's ready!");
      } else if (response.status === 409) {
        setStatus("error");
        setMessage("This number is already on the waitlist.");
      } else {
        setStatus("error");
        setMessage("Something went wrong. Please try again.");
      }
    } catch (error) {
      setStatus("error");
      setMessage("Something went wrong. Please try again.");
    }
  };

  return (
    <div className="rounded-xl border border-border bg-muted p-6">
      <h3 className="mb-2 text-lg font-semibold">WhatsApp Coming Soon</h3>
      <p className="mb-4 text-sm text-muted-foreground">
        WhatsApp is temporarily unavailable. Leave your number and we'll message you when it's ready.
      </p>
      
      <form onSubmit={handleSubmit} className="space-y-3">
        <div>
          <label htmlFor="phone" className="sr-only">
            WhatsApp Number
          </label>
          <input
            type="tel"
            id="phone"
            value={phoneNumber}
            onChange={(e) => setPhoneNumber(e.target.value)}
            placeholder="+2348012345678"
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            disabled={status === "submitting" || status === "success"}
          />
        </div>
        
        <button
          type="submit"
          disabled={status === "submitting" || status === "success"}
          className="inline-flex w-full items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
        >
          {status === "submitting" ? "Submitting..." : "Notify Me"}
        </button>
        
        {status === "success" && (
          <p className="text-sm text-green-600">{message}</p>
        )}
        
        {status === "error" && (
          <p className="text-sm text-red-600">{message}</p>
        )}
      </form>
    </div>
  );
}
