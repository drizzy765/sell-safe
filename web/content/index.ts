import { instagramGuide } from "./instagram";
import { messengerGuide } from "./messenger";
import type { PlatformGuide, PlatformId } from "./types";
import { whatsappGuide } from "./whatsapp";

export const guides: Record<PlatformId, PlatformGuide> = {
  whatsapp: whatsappGuide,
  instagram: instagramGuide,
  messenger: messengerGuide,
};

export const platformIds: PlatformId[] = ["whatsapp", "instagram", "messenger"];

export type { PlatformGuide, PlatformId };
