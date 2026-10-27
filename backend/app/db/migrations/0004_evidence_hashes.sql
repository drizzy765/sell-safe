-- Add image hashes to payment_evidence for duplicate-image detection (R5).
alter table payment_evidence add column image_sha256 text;
alter table payment_evidence add column image_phash text;
