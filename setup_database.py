#!/usr/bin/env python3
"""
Database setup script for AI-BlogPlatform
Creates the necessary tables and storage buckets in Supabase
"""

from dotenv import load_dotenv
import os
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def setup_database():
    """Set up the database tables and storage buckets"""
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env file")
        return False
    
    supabase: Client = create_client(supabase_url, supabase_key)
    
    print("🚀 Setting up AI-BlogPlatform database...")
    
    try:
        # Note: Tables should be created in Supabase dashboard
        print("📝 Checking database connection...")
        
        # Test connection by trying to access a table
        try:
            supabase.table('users').select('count', count='exact').execute()
            print("✅ Users table exists and is accessible")
        except Exception as e:
            print(f"⚠️  Users table may not exist. Please create it in Supabase dashboard.")
            print("SQL to create users table:")
            print("""
            CREATE TABLE users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR UNIQUE NOT NULL,
                first_name VARCHAR NOT NULL,
                last_name VARCHAR NOT NULL,
                is_admin BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """)
        
        try:
            supabase.table('blog_posts').select('count', count='exact').execute()
            print("✅ Blog posts table exists and is accessible")
        except Exception as e:
            print(f"⚠️  Blog posts table may not exist. Please create it in Supabase dashboard.")
            print("SQL to create blog_posts table:")
            print("""
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
            """)
        
        print("✅ Database tables created successfully!")
        
        # Create storage bucket for blog images
        print("📁 Creating storage bucket for blog images...")
        try:
            supabase.storage.create_bucket('blog-images', {'public': True})
            print("✅ Storage bucket 'blog-images' created successfully!")
        except Exception as e:
            if "already exists" in str(e).lower():
                print("ℹ️  Storage bucket 'blog-images' already exists")
            else:
                print(f"⚠️  Warning: Could not create storage bucket: {e}")
        
        # Note: Indexes should be created in Supabase dashboard for better performance
        print("ℹ️  For better performance, consider creating these indexes in Supabase dashboard:")
        print("- CREATE INDEX idx_blog_posts_author_id ON blog_posts(author_id);")
        print("- CREATE INDEX idx_blog_posts_published ON blog_posts(is_published);")
        print("- CREATE INDEX idx_blog_posts_created_at ON blog_posts(created_at DESC);")
        
        print("\n🎉 Database setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Make sure your .env file has all required variables")
        print("2. Run 'python app.py' to start the application")
        print("3. Visit http://localhost:5000 to access the platform")
        print("\n💡 Tips:")
        print("- Register the first user and manually set is_admin=true in Supabase to create an admin")
        print("- Configure Row Level Security (RLS) policies in Supabase for production")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check your Supabase URL and API key in .env")
        print("2. Ensure your Supabase project has the necessary permissions")
        print("3. Try running the SQL commands manually in Supabase SQL editor")
        return False

def create_sample_admin():
    """Create a sample admin user (optional)"""
    print("\n👤 Would you like to create a sample admin user? (y/n): ", end="")
    choice = input().lower().strip()
    
    if choice == 'y':
        email = input("Enter admin email: ").strip()
        first_name = input("Enter first name: ").strip()
        last_name = input("Enter last name: ").strip()
        password = input("Enter password: ").strip()
        
        if all([email, first_name, last_name, password]):
            print("ℹ️  To create an admin user:")
            print("1. Register normally through the web interface")
            print("2. Go to your Supabase dashboard")
            print("3. Find the user in the 'users' table")
            print("4. Set 'is_admin' to true")
            print(f"5. Use these credentials: {email} / {password}")
        else:
            print("❌ All fields are required for admin creation")

if __name__ == "__main__":
    print("🏗️  AI-BlogPlatform Database Setup")
    print("=" * 40)
    
    success = setup_database()
    
    if success:
        create_sample_admin()
    else:
        print("\n❌ Setup failed. Please check the errors above and try again.")
        exit(1)
