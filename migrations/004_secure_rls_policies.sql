-- ============================================================
-- Migration 004: Secure RLS policies (safe - checks table existence)
-- ============================================================

-- Helper: enable RLS on a table only if it exists
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'challenge_winners') THEN
    EXECUTE 'ALTER TABLE challenge_winners ENABLE ROW LEVEL SECURITY';
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'challenge_habits') THEN
    EXECUTE 'ALTER TABLE challenge_habits ENABLE ROW LEVEL SECURITY';
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'challenge_points_log') THEN
    EXECUTE 'ALTER TABLE challenge_points_log ENABLE ROW LEVEL SECURITY';
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'flash_challenges') THEN
    EXECUTE 'ALTER TABLE flash_challenges ENABLE ROW LEVEL SECURITY';
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'flash_participants') THEN
    EXECUTE 'ALTER TABLE flash_participants ENABLE ROW LEVEL SECURITY';
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'flash_shares') THEN
    EXECUTE 'ALTER TABLE flash_shares ENABLE ROW LEVEL SECURITY';
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'challenge_invites') THEN
    EXECUTE 'ALTER TABLE challenge_invites ENABLE ROW LEVEL SECURITY';
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'referral_progress') THEN
    EXECUTE 'ALTER TABLE referral_progress ENABLE ROW LEVEL SECURITY';
  END IF;
END $$;

-- DROP all permissive "allow everything" policies (safe - IF EXISTS)
DO $$
DECLARE
  t TEXT;
  pol TEXT;
BEGIN
  FOR t IN SELECT unnest(ARRAY[
    'users','user_preferences','habits','habit_logs','articles',
    'saved_articles','challenges','challenge_participants',
    'squads','squad_members','expeditions','seasons',
    'season_participants','user_fcm_tokens','journal_entries',
    'challenge_winners','challenge_habits','challenge_points_log',
    'flash_challenges','flash_participants','flash_shares',
    'challenge_invites','referral_progress'
  ]) LOOP
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = t) THEN
      FOR pol IN SELECT unnest(ARRAY[
        'Allow all access to users','Allow all access to preferences',
        'Allow all access to habits','Allow all access to habit_logs',
        'Allow all access to articles','Allow all access to saved_articles',
        'Allow all access to challenges','Allow all access to challenge_participants',
        'Allow all access to squads','Allow all access to squad_members',
        'Allow all access to expeditions','Allow all access to seasons',
        'Allow all access to season_participants','Allow all access to user_fcm_tokens',
        'Allow all access to journal_entries'
      ]) LOOP
        EXECUTE format('DROP POLICY IF EXISTS %I ON %I', pol, t);
      END LOOP;
    END IF;
  END LOOP;
END $$;

-- PUBLIC READ: articles, challenges, seasons, flash_challenges
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'articles') THEN
    DROP POLICY IF EXISTS "anon_read_articles" ON articles;
    CREATE POLICY "anon_read_articles" ON articles FOR SELECT USING (true);
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'challenges') THEN
    DROP POLICY IF EXISTS "anon_read_challenges" ON challenges;
    CREATE POLICY "anon_read_challenges" ON challenges FOR SELECT USING (true);
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'seasons') THEN
    DROP POLICY IF EXISTS "anon_read_seasons" ON seasons;
    CREATE POLICY "anon_read_seasons" ON seasons FOR SELECT USING (true);
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'flash_challenges') THEN
    DROP POLICY IF EXISTS "anon_read_flash_challenges" ON flash_challenges;
    CREATE POLICY "anon_read_flash_challenges" ON flash_challenges FOR SELECT USING (true);
  END IF;
  IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'challenge_winners') THEN
    DROP POLICY IF EXISTS "anon_read_challenge_winners" ON challenge_winners;
    CREATE POLICY "anon_read_challenge_winners" ON challenge_winners FOR SELECT USING (true);
  END IF;
END $$;

-- DENY ALL USER DATA to anon (backend uses service_role, bypasses RLS)
DO $$
DECLARE
  t TEXT;
BEGIN
  FOR t IN SELECT unnest(ARRAY[
    'users','user_preferences','habits','habit_logs','saved_articles',
    'challenge_participants','challenge_habits','challenge_points_log',
    'squads','squad_members','expeditions','season_participants',
    'user_fcm_tokens','journal_entries','flash_participants',
    'flash_shares','challenge_invites','referral_progress'
  ]) LOOP
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = t) THEN
      EXECUTE format(
        'DROP POLICY IF EXISTS deny_anon_%s ON %I; '
        'CREATE POLICY deny_anon_%s ON %I FOR ALL USING (false) WITH CHECK (false)',
        t, t, t, t
      );
    END IF;
  END LOOP;
END $$;
