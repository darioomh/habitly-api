-- Migration: Add is_premium_required column to challenges table
ALTER TABLE challenges ADD COLUMN IF NOT EXISTS is_premium_required BOOLEAN DEFAULT false;
