-- AI-BlogPlatform Database Setup Script
-- Run this in your Supabase SQL Editor

-- Create profiles table (matches app expectations)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    first_name TEXT,
    last_name TEXT,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create blog_posts table with UUID primary key
CREATE TABLE IF NOT EXISTS blog_posts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    seo_keywords TEXT[],
    cover_image_url TEXT,
    video_links TEXT[],
    author_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
    published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_blog_posts_author_id ON blog_posts(author_id);
CREATE INDEX IF NOT EXISTS idx_blog_posts_published ON blog_posts(published);
CREATE INDEX IF NOT EXISTS idx_blog_posts_created_at ON blog_posts(created_at DESC);

-- Create trigger function for handling new users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
  INSERT INTO public.profiles (id, first_name, last_name)
  VALUES (new.id, new.raw_user_meta_data->>'first_name', new.raw_user_meta_data->>'last_name');
  RETURN new;
END;
$$;

-- Create trigger for new user registration
CREATE OR REPLACE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE PROCEDURE public.handle_new_user();

-- Disable RLS for easier development (as per user's friend's setup)
ALTER TABLE blog_posts DISABLE ROW LEVEL SECURITY;
ALTER TABLE profiles DISABLE ROW LEVEL SECURITY;

-- Create policies for profiles table
CREATE POLICY "Allow user to manage own profile" ON profiles
    FOR ALL USING (auth.uid() = id);

-- Create policies for blog_posts table
CREATE POLICY "Allow user to manage own blog posts" ON blog_posts
    FOR ALL USING (auth.uid() = author_id);

CREATE POLICY "Public can view published blogs" ON blog_posts
    FOR SELECT USING (published = true);

CREATE POLICY "Authors can create posts" ON blog_posts
    FOR INSERT WITH CHECK (auth.uid() = author_id);

CREATE POLICY "Authors can update their own posts" ON blog_posts
    FOR UPDATE USING (auth.uid() = author_id);

CREATE POLICY "Authors can delete their own posts" ON blog_posts
    FOR DELETE USING (auth.uid() = author_id);

-- Create storage bucket for blog images
INSERT INTO storage.buckets (id, name, public) 
VALUES ('blog-images', 'blog-images', true)
ON CONFLICT (id) DO NOTHING;

-- Create storage policy for blog images
CREATE POLICY "Anyone can view blog images" ON storage.objects
    FOR SELECT USING (bucket_id = 'blog-images');

CREATE POLICY "Authenticated users can upload blog images" ON storage.objects
    FOR INSERT WITH CHECK (bucket_id = 'blog-images' AND auth.role() = 'authenticated');

CREATE POLICY "Users can update their own blog images" ON storage.objects
    FOR UPDATE USING (bucket_id = 'blog-images' AND auth.uid()::text = (storage.foldername(name))[1]);

CREATE POLICY "Users can delete their own blog images" ON storage.objects
    FOR DELETE USING (bucket_id = 'blog-images' AND auth.uid()::text = (storage.foldername(name))[1]);

-- Create a function to automatically update the updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_blog_posts_updated_at 
    BEFORE UPDATE ON blog_posts 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert a sample admin user (optional)
-- You can uncomment and modify this after running the script
-- INSERT INTO auth.users (id, email, encrypted_password, email_confirmed_at, created_at, updated_at)
-- VALUES (gen_random_uuid(), 'admin@blogplatform.com', crypt('admin123', gen_salt('bf')), NOW(), NOW(), NOW());

COMMENT ON TABLE users IS 'User profiles and authentication data';
COMMENT ON TABLE blog_posts IS 'Blog posts with content and metadata';
COMMENT ON COLUMN blog_posts.is_published IS 'Whether the post is visible to public';
COMMENT ON COLUMN users.is_admin IS 'Whether the user has admin privileges';
