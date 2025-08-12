# 🚀 AI-BlogPlatform Setup Guide

This guide will help you set up and run the AI-BlogPlatform successfully.

## 📋 Prerequisites

- Python 3.8 or higher
- Supabase account (free tier works)
- Google Gemini API key (optional, for AI features)

## 🔧 Step-by-Step Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

1. Copy the example environment file:
   ```bash
   copy .env.example .env
   ```

2. Edit `.env` file with your credentials:
   ```env
   # Supabase Configuration (REQUIRED)
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your_anon_key_here

   # Gemini AI Configuration (OPTIONAL - for AI features)
   GEMINI_API_KEY=your_gemini_api_key_here

   # Flask Configuration
   SECRET_KEY=your_secret_key_here
   FLASK_ENV=development
   ```

### 3. Supabase Database Setup

#### Option A: Using Supabase Dashboard (Recommended)

1. Go to your Supabase project dashboard
2. Navigate to SQL Editor
3. Run these SQL commands:

```sql
-- Create users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR UNIQUE NOT NULL,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create blog_posts table
CREATE TABLE blog_posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    content TEXT NOT NULL,
    cover_image_url VARCHAR,
    video_url VARCHAR,
    author_id UUID REFERENCES users(id) ON DELETE CASCADE,
    is_published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_blog_posts_author_id ON blog_posts(author_id);
CREATE INDEX idx_blog_posts_published ON blog_posts(is_published);
CREATE INDEX idx_blog_posts_created_at ON blog_posts(created_at DESC);
```

4. Create storage bucket:
   - Go to Storage in Supabase dashboard
   - Create a new bucket named `blog-images`
   - Make it public

#### Option B: Using Setup Script

```bash
python setup_database.py
```

### 4. Run the Application

#### Option A: Using the startup script (Recommended)
```bash
python run.py
```

#### Option B: Direct Flask run
```bash
python app.py
```

The application will be available at: http://localhost:5000

## 🔑 Getting API Keys

### Supabase Setup

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Go to Settings → API
4. Copy your Project URL and anon/public key

### Gemini API Key (Optional)

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file

## 🎯 First Steps After Setup

### 1. Create Your First Admin User

1. Register normally through the web interface
2. Go to your Supabase dashboard
3. Navigate to Table Editor → users
4. Find your user and set `is_admin` to `true`

### 2. Test the Features

- ✅ User registration and login
- ✅ Create blog posts with rich editor
- ✅ Upload cover images
- ✅ AI suggestions (if Gemini API key is configured)
- ✅ Admin dashboard (for admin users)

## 🐛 Troubleshooting

### Common Issues

#### "Database connection not available"
- Check your Supabase URL and API key in `.env`
- Ensure your Supabase project is active

#### "AI service not available"
- Add your Gemini API key to `.env`
- AI features are optional and the app works without them

#### "Table does not exist"
- Run the SQL commands in Supabase dashboard
- Or use `python setup_database.py`

#### Import errors
- Run `pip install -r requirements.txt`
- Make sure you're in the correct directory

### Error Messages and Solutions

| Error | Solution |
|-------|----------|
| `ModuleNotFoundError: No module named 'supabase'` | Run `pip install -r requirements.txt` |
| `Database connection not available` | Check Supabase credentials in `.env` |
| `AI service not available` | Add Gemini API key to `.env` (optional) |
| `Table 'users' doesn't exist` | Create tables in Supabase dashboard |

## 🔒 Security Notes

### For Development
- The app includes default security settings
- Secret key is auto-generated if not provided

### For Production
- Use strong secret keys
- Enable HTTPS
- Configure proper CORS settings
- Set up Row Level Security (RLS) in Supabase

## 📱 Features Overview

### User Features
- ✅ User registration and authentication
- ✅ Rich blog post editor
- ✅ Image and video support
- ✅ Draft and publish system
- ✅ AI-powered content suggestions

### Admin Features
- ✅ User management
- ✅ Content moderation
- ✅ Platform statistics
- ✅ Role management

### AI Features (Optional)
- ✅ Headline suggestions
- ✅ Content summaries
- ✅ SEO keyword generation
- ✅ Content improvement suggestions

## 🆘 Getting Help

If you encounter issues:

1. Check this setup guide
2. Review the error messages in the console
3. Verify your `.env` configuration
4. Check Supabase dashboard for table creation
5. Ensure all dependencies are installed

## 🎉 You're Ready!

Once setup is complete, you'll have a fully functional AI-powered blog platform with:
- Modern, responsive UI
- User authentication
- Rich content creation
- AI assistance
- Admin management

Happy blogging! 🚀
