export type PlatformId = "whatsapp" | "instagram" | "messenger";

export type StepBlock =
  | { type: "text"; body: string }
  | { type: "code"; label?: string; value: string; secret?: boolean };

export type PlatformGuide = {
  id: PlatformId;
  label: string;
  accent: string;
  prerequisites: string[];
  steps: {
    title: string;
    blocks: StepBlock[];
  }[];
  note?: string;
};
