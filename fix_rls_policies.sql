-- Fix RLS Policies for Blog Posts Creation
-- Run this in your Supabase SQL Editor to fix the RLS policy error

-- Drop existing problematic policies
DROP POLICY IF EXISTS "Authors can insert own posts" ON blog_posts;
DROP POLICY IF EXISTS "Authors can update own posts" ON blog_posts;
DROP POLICY IF EXISTS "Authors can delete own posts" ON blog_posts;

-- Create new working policies for blog_posts
CREATE POLICY "Authenticated users can insert posts"
    ON blog_posts FOR INSERT
    TO authenticated
    WITH CHECK (auth.uid() = author_id);

CREATE POLICY "Authors can update own posts"
    ON blog_posts FOR UPDATE
    TO authenticated
    USING (auth.uid() = author_id)
    WITH CHECK (auth.uid() = author_id);

CREATE POLICY "Authors can delete own posts"
    ON blog_posts FOR DELETE
    TO authenticated
    USING (auth.uid() = author_id);

-- Also ensure storage policies work for authenticated users
DROP POLICY IF EXISTS "Authenticated users can upload blog images" ON storage.objects;

CREATE POLICY "Authenticated users can upload blog images"
    ON storage.objects FOR INSERT
    TO authenticated
    WITH CHECK (bucket_id = 'blog-images');

-- Add OTP table for email verification
CREATE TABLE IF NOT EXISTS user_otp (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    otp_code TEXT NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc', now())
);

-- Enable RLS on OTP table
ALTER TABLE user_otp ENABLE ROW LEVEL SECURITY;

-- OTP policies
CREATE POLICY "Users can view own OTP"
    ON user_otp FOR SELECT
    TO authenticated
    USING (auth.uid() = user_id);

CREATE POLICY "Anyone can insert OTP for registration"
    ON user_otp FOR INSERT
    TO anon, authenticated
    WITH CHECK (true);

CREATE POLICY "Users can update own OTP"
    ON user_otp FOR UPDATE
    TO authenticated
    USING (auth.uid() = user_id);

-- Index for OTP lookup
CREATE INDEX IF NOT EXISTS idx_user_otp_email_code ON user_otp(email, otp_code);
CREATE INDEX IF NOT EXISTS idx_user_otp_expires ON user_otp(expires_at);

-- Function to clean expired OTPs
CREATE OR REPLACE FUNCTION cleanup_expired_otps()
RETURNS void AS $$
BEGIN
    DELETE FROM user_otp WHERE expires_at < timezone('utc', now());
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE user_otp IS 'OTP codes for email verification during registration';
