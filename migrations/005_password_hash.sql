-- ============================================================
-- Migration 005: Add password_hash column to users
-- Run this in the Supabase SQL Editor (Dashboard -> SQL Editor)
-- This enables secure email/password auth.
-- ============================================================

ALTER TABLE users ADD COLUMN IF NOT EXISTS password_hash TEXT;
