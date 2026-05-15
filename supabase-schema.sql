-- 在 Supabase SQL Editor 中执行此脚本

CREATE TABLE survey_results (
    id              BIGSERIAL PRIMARY KEY,
    user_id         TEXT NOT NULL,
    device_type     TEXT,
    survey_timestamp TIMESTAMPTZ,
    age             TEXT,
    gender          TEXT,
    listening_frequency TEXT,
    training_years  TEXT,
    instrument      TEXT,
    test_results    JSONB NOT NULL,
    difference_perception TEXT,
    issues          TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 开启行级安全（不启用 RLS 会让 anon key 无法写入）
ALTER TABLE survey_results ENABLE ROW LEVEL SECURITY;

-- 允许匿名写入
CREATE POLICY "allow_insert" ON survey_results
    FOR INSERT
    WITH CHECK (true);
