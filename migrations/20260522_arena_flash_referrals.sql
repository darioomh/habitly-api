create table if not exists flash_challenges (
    id text primary key,
    title text not null,
    description text not null,
    duration_hours integer not null check (duration_hours in (24, 48, 72)),
    category text not null default 'OTRO',
    difficulty text not null default 'medium',
    xp_reward integer not null default 50,
    starts_at timestamptz not null default now(),
    ends_at timestamptz not null,
    is_active boolean not null default true,
    created_at timestamptz not null default now()
);

create table if not exists flash_participants (
    id uuid primary key default gen_random_uuid(),
    flash_challenge_id text not null references flash_challenges(id) on delete cascade,
    user_id uuid not null,
    user_name text,
    joined_at timestamptz not null default now(),
    unique (flash_challenge_id, user_id)
);

create table if not exists flash_shares (
    id uuid primary key default gen_random_uuid(),
    flash_challenge_id text not null references flash_challenges(id) on delete cascade,
    user_id uuid not null,
    created_at timestamptz not null default now()
);

create table if not exists challenge_invites (
    id uuid primary key default gen_random_uuid(),
    challenge_id uuid not null,
    user_id uuid not null,
    invite_count integer not null default 0,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (challenge_id, user_id)
);

create table if not exists referral_progress (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null unique,
    referral_code text not null unique,
    invite_count integer not null default 0,
    target_invites integer not null default 10,
    is_premium_unlocked boolean not null default false,
    referral_url text not null,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

insert into flash_challenges (id, title, description, duration_hours, category, difficulty, xp_reward, starts_at, ends_at)
values
    ('flash-no-sugar-48h', '0 azucar', '48 horas sin bebidas azucaradas ni dulces procesados.', 48, 'SALUD', 'medium', 90, now(), now() + interval '48 hours'),
    ('flash-steps-10k', '10k pasos hoy', 'Cierra el dia con 10.000 pasos y una caminata consciente.', 24, 'EJERCICIO', 'hard', 120, now(), now() + interval '24 hours'),
    ('flash-no-tiktok-24h', 'Sin TikTok', '24 horas sin scroll infinito. Recupera atencion profunda.', 24, 'PRODUCTIVIDAD', 'medium', 80, now(), now() + interval '24 hours'),
    ('flash-sleep-72h', 'Dormir 8h x 3', 'Tres noches seguidas priorizando descanso real.', 72, 'SALUD', 'hard', 160, now(), now() + interval '72 hours')
on conflict (id) do nothing;
