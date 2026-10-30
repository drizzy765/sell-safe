"use client";

import { useState, useEffect } from "react";

interface SampleReplyDemoProps {
  productName?: string;
  productPrice?: number;
}

export function SampleReplyDemo({ 
  productName = "Black Leather Bag", 
  productPrice = 15000 
}: SampleReplyDemoProps) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [reply, setReply] = useState<string | null>(null);

  const mockCustomerQuestions = [
    "How much for the black bag?",
    "Abeg how much for the bag?",
    "Elo ni owo apo yii?",
  ];

  const [selectedQuestion, setSelectedQuestion] = useState(mockCustomerQuestions[0]);

  const generateReply = async () => {
    setIsGenerating(true);
    
    // Simulate API call delay
    await new Promise(resolve => setTimeout(resolve, 1500));
    
    // Mock AI-generated reply
    const replies = {
      "How much for the black bag?": `The ${productName} is ₦${productPrice.toLocaleString()}. We have 3 in stock. Would you like to place an order?`,
      "Abeg how much for the bag?": `The ${productName} na ₦${productPrice.toLocaleString()}. We get 3 pieces. You wan order?`,
      "Elo ni owo apo yii?": `${productName} yi ni ₦${productPrice.toLocaleString()}. A ni 3 ninu. O fe ra?`,
    };
    
    setReply(replies[selectedQuestion as keyof typeof replies] || replies["How much for the black bag?"]);
    setIsGenerating(false);
  };

  return (
    <div className="rounded-xl border border-border bg-card p-8">
      <div className="mb-6 text-center">
        <h2 className="mb-2 text-2xl font-bold">See Sell-Safe in Action</h2>
        <p className="text-muted-foreground">
          This is how Sell-Safe would reply to your customers
        </p>
      </div>

      <div className="space-y-6">
        {/* Customer Message */}
        <div className="flex justify-start">
          <div className="max-w-[80%] rounded-2xl bg-muted px-4 py-3 text-sm">
            <div className="mb-2 text-xs font-medium text-muted-foreground">Customer</div>
            <select
              value={selectedQuestion}
              onChange={(e) => {
                setSelectedQuestion(e.target.value);
                setReply(null);
              }}
              className="w-full bg-transparent text-sm focus:outline-none"
            >
              {mockCustomerQuestions.map((q) => (
                <option key={q} value={q}>
                  {q}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Generate Button */}
        {!reply && !isGenerating && (
          <div className="text-center">
            <button
              onClick={generateReply}
              className="inline-flex items-center justify-center rounded-md bg-primary px-6 py-3 text-sm font-medium text-primary-foreground hover:bg-primary/90"
            >
              See AI Reply
            </button>
          </div>
        )}

        {/* Loading */}
        {isGenerating && (
          <div className="flex justify-end">
            <div className="flex items-center space-x-2 rounded-2xl bg-primary/10 px-4 py-3 text-sm text-primary">
              <svg
                className="h-4 w-4 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                />
              </svg>
              <span>Sell-Safe is typing...</span>
            </div>
          </div>
        )}

        {/* AI Reply */}
        {reply && (
          <div className="flex justify-end">
            <div className="max-w-[80%] rounded-2xl bg-primary px-4 py-3 text-sm text-primary-foreground">
              <div className="mb-1 text-xs font-medium opacity-80">Sell-Safe</div>
              <p>{reply}</p>
            </div>
          </div>
        )}

        {/* Value Props */}
        {reply && (
          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <div className="text-center">
              <div className="mb-1 text-2xl font-bold text-primary">3</div>
              <div className="text-xs text-muted-foreground">Languages supported</div>
            </div>
            <div className="text-center">
              <div className="mb-1 text-2xl font-bold text-primary">24/7</div>
              <div className="text-xs text-muted-foreground">Instant replies</div>
            </div>
            <div className="text-center">
              <div className="mb-1 text-2xl font-bold text-primary">100%</div>
              <div className="text-xs text-muted-foreground">Real prices from catalog</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
