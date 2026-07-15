-- ============================================================
-- Migration 004: Secure RLS policies
-- Drop permissive "allow all" policies and replace with
-- restrictive ones. The backend uses the service_role key
-- (bypasses RLS). The anon key is restricted.
-- ============================================================

-- ─────────────────────────────────────────────
-- 1. ENABLE RLS on tables that were missing it
-- ─────────────────────────────────────────────
ALTER TABLE challenge_winners    ENABLE ROW LEVEL SECURITY;
ALTER TABLE challenge_habits     ENABLE ROW LEVEL SECURITY;
ALTER TABLE challenge_points_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE flash_challenges     ENABLE ROW LEVEL SECURITY;
ALTER TABLE flash_participants   ENABLE ROW LEVEL SECURITY;
ALTER TABLE flash_shares         ENABLE ROW LEVEL SECURITY;
ALTER TABLE challenge_invites    ENABLE ROW LEVEL SECURITY;
ALTER TABLE referral_progress    ENABLE ROW LEVEL SECURITY;

-- ─────────────────────────────────────────────
-- 2. DROP all permissive "allow everything" policies
-- ─────────────────────────────────────────────
DROP POLICY IF EXISTS "Allow all access to users"               ON users;
DROP POLICY IF EXISTS "Allow all access to preferences"         ON user_preferences;
DROP POLICY IF EXISTS "Allow all access to habits"              ON habits;
DROP POLICY IF EXISTS "Allow all access to habit_logs"          ON habit_logs;
DROP POLICY IF EXISTS "Allow all access to articles"            ON articles;
DROP POLICY IF EXISTS "Allow all access to saved_articles"      ON saved_articles;
DROP POLICY IF EXISTS "Allow all access to challenges"          ON challenges;
DROP POLICY IF EXISTS "Allow all access to challenge_participants" ON challenge_participants;
DROP POLICY IF EXISTS "Allow all access to squads"              ON squads;
DROP POLICY IF EXISTS "Allow all access to squad_members"       ON squad_members;
DROP POLICY IF EXISTS "Allow all access to expeditions"         ON expeditions;
DROP POLICY IF EXISTS "Allow all access to seasons"             ON seasons;
DROP POLICY IF EXISTS "Allow all access to season_participants" ON season_participants;
DROP POLICY IF EXISTS "Allow all access to user_fcm_tokens"     ON user_fcm_tokens;
DROP POLICY IF EXISTS "Allow all access to journal_entries"     ON journal_entries;

-- ─────────────────────────────────────────────
-- 3. PUBLIC READ tables (anon can SELECT only)
--    articles, challenges, seasons, challenge_winners, flash_challenges
-- ─────────────────────────────────────────────

-- articles: public catalog
CREATE POLICY "anon_read_articles"
    ON articles FOR SELECT
    USING (true);

-- challenges: public challenges list
CREATE POLICY "anon_read_challenges"
    ON challenges FOR SELECT
    USING (true);

-- seasons: public season info
CREATE POLICY "anon_read_seasons"
    ON seasons FOR SELECT
    USING (true);

-- challenge_winners: public leaderboard
CREATE POLICY "anon_read_challenge_winners"
    ON challenge_winners FOR SELECT
    USING (true);

-- flash_challenges: public flash events
CREATE POLICY "anon_read_flash_challenges"
    ON flash_challenges FOR SELECT
    USING (true);

-- ─────────────────────────────────────────────
-- 4. RESTRICT ALL USER DATA (anon gets nothing)
--    Backend uses service_role which bypasses RLS,
--    so all API queries continue working normally.
-- ─────────────────────────────────────────────

-- users: no anon access
CREATE POLICY "deny_anon_users"
    ON users FOR ALL
    USING (false)
    WITH CHECK (false);

-- user_preferences
CREATE POLICY "deny_anon_user_preferences"
    ON user_preferences FOR ALL
    USING (false)
    WITH CHECK (false);

-- habits
CREATE POLICY "deny_anon_habits"
    ON habits FOR ALL
    USING (false)
    WITH CHECK (false);

-- habit_logs
CREATE POLICY "deny_anon_habit_logs"
    ON habit_logs FOR ALL
    USING (false)
    WITH CHECK (false);

-- saved_articles
CREATE POLICY "deny_anon_saved_articles"
    ON saved_articles FOR ALL
    USING (false)
    WITH CHECK (false);

-- challenge_participants
CREATE POLICY "deny_anon_challenge_participants"
    ON challenge_participants FOR ALL
    USING (false)
    WITH CHECK (false);

-- challenge_habits
CREATE POLICY "deny_anon_challenge_habits"
    ON challenge_habits FOR ALL
    USING (false)
    WITH CHECK (false);

-- challenge_points_log
CREATE POLICY "deny_anon_challenge_points_log"
    ON challenge_points_log FOR ALL
    USING (false)
    WITH CHECK (false);

-- squads
CREATE POLICY "deny_anon_squads"
    ON squads FOR ALL
    USING (false)
    WITH CHECK (false);

-- squad_members
CREATE POLICY "deny_anon_squad_members"
    ON squad_members FOR ALL
    USING (false)
    WITH CHECK (false);

-- expeditions
CREATE POLICY "deny_anon_expeditions"
    ON expeditions FOR ALL
    USING (false)
    WITH CHECK (false);

-- season_participants
CREATE POLICY "deny_anon_season_participants"
    ON season_participants FOR ALL
    USING (false)
    WITH CHECK (false);

-- user_fcm_tokens
CREATE POLICY "deny_anon_user_fcm_tokens"
    ON user_fcm_tokens FOR ALL
    USING (false)
    WITH CHECK (false);

-- journal_entries
CREATE POLICY "deny_anon_journal_entries"
    ON journal_entries FOR ALL
    USING (false)
    WITH CHECK (false);

-- flash_participants
CREATE POLICY "deny_anon_flash_participants"
    ON flash_participants FOR ALL
    USING (false)
    WITH CHECK (false);

-- flash_shares
CREATE POLICY "deny_anon_flash_shares"
    ON flash_shares FOR ALL
    USING (false)
    WITH CHECK (false);

-- challenge_invites
CREATE POLICY "deny_anon_challenge_invites"
    ON challenge_invites FOR ALL
    USING (false)
    WITH CHECK (false);

-- referral_progress
CREATE POLICY "deny_anon_referral_progress"
    ON referral_progress FOR ALL
    USING (false)
    WITH CHECK (false);
