-- Seed: 6 desafíos iniciales para mayo 2026
-- Ejecutar en Supabase SQL Editor

-- 1. Desafío de salud
INSERT INTO challenges (title, description, category, difficulty, duration_days, max_participants, reward, is_public, is_premium_required, start_date)
VALUES (
    'Desafío Salud Total',
    '30 días de hábitos saludables: ejercicio, alimentación consciente y buen descanso. Transforma tu cuerpo y mente.',
    'SALUD',
    'hard',
    30,
    1000,
    '🏆 Premium Gratis 1 Mes',
    true,
    false,
    '2026-05-01T00:00:00Z'
);

-- 2. Maratón de Productividad
INSERT INTO challenges (title, description, category, difficulty, duration_days, max_participants, reward, is_public, is_premium_required, start_date)
VALUES (
    'Maratón de Productividad',
    '30 días de máxima productividad. Despierta temprano, organiza tu día y cumple tus objetivos sin excusas.',
    'PRODUCTIVIDAD',
    'extreme',
    30,
    1000,
    '💎 Badge Productividad Extrema',
    true,
    false,
    '2026-05-01T00:00:00Z'
);

-- 3. Reto fitness
INSERT INTO challenges (title, description, category, difficulty, duration_days, max_participants, reward, is_public, is_premium_required, start_date)
VALUES (
    'Reto Fitness 30',
    'Ejercitate al menos 30 minutos cada día durante 30 días. Sin días de descanso, sin excusas.',
    'EJERCICIO',
    'hard',
    30,
    500,
    '💪 Badge Guerrero Fitness',
    true,
    false,
    '2026-05-01T00:00:00Z'
);

-- 4. Desafío mindfulness
INSERT INTO challenges (title, description, category, difficulty, duration_days, max_participants, reward, is_public, is_premium_required, start_date)
VALUES (
    'Desafío Mindfulness',
    'Medita al menos 10 minutos cada día y registra tu reflexión. Conecta con tu interior durante 30 días.',
    'MINDFULNESS',
    'medium',
    30,
    1000,
    '🧘 Badge Calma Interior',
    true,
    false,
    '2026-05-01T00:00:00Z'
);

-- 5. Reto social
INSERT INTO challenges (title, description, category, difficulty, duration_days, max_participants, reward, is_public, is_premium_required, start_date)
VALUES (
    'Reto Conexión Social',
    'Fortalece tus vínculos. Contacta a alguien, envía un mensaje positivo o participa en comunidad cada día.',
    'SOCIAL',
    'easy',
    30,
    1000,
    '🤝 Badge Conexión Social',
    true,
    false,
    '2026-05-01T00:00:00Z'
);

-- 6. Desafío Premium Élite (SOLO PREMIUM)
INSERT INTO challenges (title, description, category, difficulty, duration_days, max_participants, reward, reward_description, is_public, is_premium_required, start_date, end_date)
VALUES (
    'Desafío Premium Élite',
    'SOLO PREMIUM: El reto definitivo. 30 días de exigencia máxima. El ganador recibe 1 AÑO DE PREMIUM GRATIS.',
    'SALUD',
    'extreme',
    30,
    100,
    '👑 1 AÑO PREMIUM GRATIS',
    'El primer lugar del ranking recibe 1 año de suscripción Premium gratis',
    true,
    true,
    '2026-05-01T00:00:00Z',
    '2026-05-31T23:59:59Z'
);

-- 2. Maratón de productividad
INSERT INTO challenges (title, description, category, difficulty, duration_days, max_participants, reward, is_public, start_date)
VALUES (
    'Maratón de Productividad',
    '30 días de máxima productividad. Despierta temprano, organiza tu día y cumple tus objetivos sin excusas.',
    'PRODUCTIVIDAD',
    'extreme',
    30,
    1000,
    '💎 Badge Productividad Extrema',
    true,
    '2026-05-01T00:00:00Z'
);

-- 3. Reto fitness
INSERT INTO challenges (title, description, category, difficulty, duration_days, max_participants, reward, is_public, start_date)
VALUES (
    'Reto Fitness 30',
    'Ejercítate al menos 30 minutos cada día durante 30 días. Sin días de descanso, sin excusas.',
    'EJERCICIO',
    'hard',
    30,
    500,
    '💪 Badge Guerrero Fitness',
    true,
    '2026-05-01T00:00:00Z'
);

-- 4. Desafío mindfulness
INSERT INTO challenges (title, description, category, difficulty, duration_days, max_participants, reward, is_public, start_date)
VALUES (
    'Desafío Mindfulness',
    'Medita al menos 10 minutos cada día y registra tu reflexión. Conecta con tu interior durante 30 días.',
    'MINDFULNESS',
    'medium',
    30,
    1000,
    '🧘 Badge Calma Interior',
    true,
    '2026-05-01T00:00:00Z'
);

-- 5. Reto social
INSERT INTO challenges (title, description, category, difficulty, duration_days, max_participants, reward, is_public, start_date)
VALUES (
    'Reto Conexión Social',
    'Fortalece tus vínculos. Contacta a alguien, envía un mensaje positivo o participa en comunidad cada día.',
    'SOCIAL',
    'easy',
    30,
    1000,
    '🤝 Badge Conexión Social',
    true,
    '2026-05-01T00:00:00Z'
);
