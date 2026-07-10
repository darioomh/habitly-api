-- Migration: Add notes JSONB column to journal_entries
-- Stores an array of {text, created_at} objects so each save appends a new note
-- The existing `note` column keeps the latest note for backward compatibility

ALTER TABLE journal_entries ADD COLUMN IF NOT EXISTS notes JSONB DEFAULT '[]';

-- Backfill: migrate existing `note` data into the `notes` array
UPDATE journal_entries
SET notes = CASE
    WHEN note IS NOT NULL AND note != '' THEN
        jsonb_build_array(jsonb_build_object('text', note, 'created_at', COALESCE(updated_at, created_at)))
    ELSE '[]'::jsonb
END
WHERE notes = '[]'::jsonb OR notes IS NULL;
