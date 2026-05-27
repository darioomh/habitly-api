from app.database import supabase

# Create challenge_habits table
try:
    supabase.table("challenge_habits").select("*").limit(1).execute()
    print("challenge_habits already exists")
except:
    sql = """
    CREATE TABLE IF NOT EXISTS challenge_habits (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        challenge_id UUID REFERENCES challenges(id) ON DELETE CASCADE,
        habit_id UUID REFERENCES habits(id) ON DELETE CASCADE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        UNIQUE(challenge_id, habit_id)
    );
    """
    supabase.query(sql)
    print("Created challenge_habits")

# Create challenge_points_log table
try:
    supabase.table("challenge_points_log").select("*").limit(1).execute()
    print("challenge_points_log already exists")
except:
    sql = """
    CREATE TABLE IF NOT EXISTS challenge_points_log (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        challenge_id UUID REFERENCES challenges(id) ON DELETE CASCADE,
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        habit_id UUID REFERENCES habits(id),
        points INTEGER NOT NULL,
        reason TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """
    supabase.query(sql)
    print("Created challenge_points_log")

# also create challenge_invites if missing
try:
    supabase.table("challenge_invites").select("*").limit(1).execute()
    print("challenge_invites already exists")
except:
    sql = """
    CREATE TABLE IF NOT EXISTS challenge_invites (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        challenge_id UUID REFERENCES challenges(id) ON DELETE CASCADE,
        user_id UUID REFERENCES users(id) ON DELETE CASCADE,
        invite_count INTEGER DEFAULT 1,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        UNIQUE(challenge_id, user_id)
    );
    """
    supabase.query(sql)
    print("Created challenge_invites")
