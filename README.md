# AI-Powered Blog Platform

A modern Flask-based blog platform with AI-powered content assistance, user authentication, and admin management capabilities.

## Features

### 🚀 Core Features
- **User Authentication**: Secure signup/login with Supabase Auth
- **Blog Management**: Full CRUD operations for blog posts
- **Rich Content Editor**: Support for images, videos, and text formatting
- **AI-Powered Assistance**: Content suggestions, headlines, summaries, and SEO keywords
- **Admin Dashboard**: User and content management for administrators
- **Modern UI**: Beautiful, responsive design with TailwindCSS

### 🤖 AI Features (Gemini Integration)
- **Smart Headlines**: AI-generated catchy and SEO-friendly headlines
- **Content Summaries**: Automatic summary generation
- **SEO Keywords**: Intelligent keyword suggestions
- **Content Improvement**: AI-powered content enhancement suggestions

### 👥 User Management
- **User Registration**: First name, last name, email, password
- **Role-based Access**: Regular users and administrators
- **Profile Management**: User dashboard with post management

### 📝 Blog Features
- **Rich Text Editor**: Bold, italic, underline, font size controls
- **Media Support**: Cover image uploads and video embedding
- **Draft/Publish System**: Save drafts or publish immediately
- **Public/Private Posts**: Control post visibility

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Supabase Auth
- **File Storage**: Supabase Storage
- **AI Integration**: Google Gemini API
- **Frontend**: HTML5, TailwindCSS, Alpine.js
- **Icons**: Font Awesome

## Prerequisites

- Python 3.8+
- Supabase account and project
- Google Gemini API key

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AI-Powered-Blog-Website
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   # source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Setup**
   - Copy `.env.example` to `.env`
   - Fill in your configuration values:
   ```env
   SUPABASE_URL=your_supabase_project_url
   SUPABASE_ANON_KEY=your_supabase_anon_key
   GEMINI_API_KEY=your_gemini_api_key
   SECRET_KEY=your_secret_key
   FLASK_ENV=development
   ```

5. **Database Setup**
   Run the database setup script to create required tables:
   ```bash
   python setup_database.py
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

The application will be available at `http://localhost:5000`

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR NOT NULL,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Blog Posts Table
```sql
CREATE TABLE blog_posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    content TEXT NOT NULL,
    cover_image_url VARCHAR,
    video_url VARCHAR,
    author_id UUID REFERENCES users(id),
    is_published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### Storage Buckets
- `blog-images`: For storing cover images

## API Endpoints

### Authentication
- `GET /` - Home page with published posts
- `GET /register` - User registration form
- `POST /register` - Process registration
- `GET /login` - Login form
- `POST /login` - Process login
- `GET /logout` - Logout user

### Blog Management
- `GET /dashboard` - User dashboard
- `GET /create-post` - Create new post form
- `POST /create-post` - Process new post
- `GET /edit-post/<id>` - Edit post form
- `POST /edit-post/<id>` - Process post update
- `POST /delete-post/<id>` - Delete post
- `GET /post/<id>` - View single post

### AI Features (Authenticated users only)
- `POST /ai/suggest-headline` - Get AI headline suggestions
- `POST /ai/generate-summary` - Generate content summary
- `POST /ai/suggest-keywords` - Get SEO keywords
- `POST /ai/improve-content` - Get content improvements

### Admin Features
- `GET /admin` - Admin dashboard
- `POST /admin/delete-user/<id>` - Delete user
- `POST /admin/toggle-admin/<id>` - Toggle admin status

## Usage

### For Regular Users
1. **Register**: Create an account with your details
2. **Login**: Access your dashboard
3. **Create Posts**: Use the rich editor with AI assistance
4. **Manage Content**: Edit, delete, or publish your posts
5. **AI Features**: Get suggestions for headlines, summaries, and improvements

### For Administrators
1. **Access Admin Panel**: Available in navigation for admin users
2. **User Management**: View, promote, or delete users
3. **Content Moderation**: Delete any blog posts
4. **Platform Overview**: View statistics and activity

## AI Features Usage

### Getting AI Suggestions
1. Write your content in the editor
2. Click on AI buttons for:
   - **AI Suggest**: Get headline suggestions
   - **AI Summary**: Generate content summary
   - **AI Improve**: Get content improvement suggestions
   - **SEO Keywords**: Get keyword recommendations

### Content Editor Features
- **Text Formatting**: Bold, italic, underline
- **Font Sizes**: Multiple size options
- **Media**: Upload cover images, embed videos
- **Draft System**: Save work in progress

## Deployment

### Environment Variables for Production
```env
FLASK_ENV=production
SECRET_KEY=your_secure_secret_key
SUPABASE_URL=your_production_supabase_url
SUPABASE_ANON_KEY=your_production_supabase_key
GEMINI_API_KEY=your_gemini_api_key
```

### Security Considerations
- Use strong secret keys in production
- Enable HTTPS
- Configure proper CORS settings
- Set up proper database security rules in Supabase
- Implement rate limiting for AI API calls

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support or questions, please open an issue in the repository or contact the development team.

---

**Built with ❤️ using Flask, Supabase, and AI technology**
