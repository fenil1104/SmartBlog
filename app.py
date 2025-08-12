from dotenv import load_dotenv

# Load environment variables from .env file FIRST
load_dotenv()

import os

import uuid
import json
import random
import smtplib
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps

import requests
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.utils import secure_filename
from supabase import create_client, Client
import google.generativeai as genai

from config import Config

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize Supabase client
supabase_url = app.config.get('SUPABASE_URL')
supabase_key = app.config.get('SUPABASE_KEY')

supabase = None
supabase_admin = None

if not supabase_url or not supabase_key:
    logging.critical("Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_KEY in your .env file.")
else:
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # Initialize admin client with service role key
    supabase_service_key = app.config.get('SUPABASE_SERVICE_KEY')
    if supabase_service_key:
        supabase_admin: Client = create_client(supabase_url, supabase_service_key)
    else:
        logging.warning("SUPABASE_SERVICE_KEY not found. Admin operations may be restricted by RLS.")
        supabase_admin = supabase # Fallback to regular client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create static directories if they don't exist
os.makedirs('static/uploads', exist_ok=True)

# Gemini AI configuration
gemini_api_key = os.getenv('GEMINI_API_KEY')
if gemini_api_key:
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    logger.warning("Gemini API key not found. AI features will be disabled.")
    model = None

# Upload configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_otp():
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp_code, first_name):
    """Send OTP via email with detailed error logging."""
    smtp_username = os.getenv('SMTP_USERNAME')
    smtp_password = os.getenv('SMTP_PASSWORD')

    if not smtp_username or not smtp_password:
        logger.critical("SMTP_USERNAME or SMTP_PASSWORD environment variables are not set. Cannot send emails.")
        return False

    try:
        smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        smtp_port = int(os.getenv('SMTP_PORT', '587'))
        
        msg = MIMEMultipart()
        msg['From'] = smtp_username
        msg['To'] = email
        msg['Subject'] = "Your OTP for AI Blog Platform Registration"
        
        body = f"""Hi {first_name}, your OTP is: {otp_code}"""
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(smtp_username, email, msg.as_string())
        
        logger.info(f"OTP email sent successfully to {email}")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Failed for user {smtp_username}. Check credentials. Error: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to send OTP email to {email}. Server: {smtp_server}:{smtp_port}. Error: {e}")
        return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('You must be logged in to view this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def generate_content_suggestions(blog_content):
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    if not GEMINI_API_KEY:
        return "Error: Gemini API key not configured. Please add GEMINI_API_KEY to your .env file."
    
    if not blog_content or len(blog_content.strip()) < 10:
        return "Error: Please provide more content (at least 10 characters) for AI analysis."
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": f"Analyze this blog content and suggest:\n1. A catchy headline\n2. A short summary (max 30 words)\n3. 5 SEO keywords\n\nContent:\n{blog_content[:1000]}..."
                    }
                ]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            suggestions = response.json()
            try:
                ai_text = suggestions['candidates'][0]['content']['parts'][0]['text']
                return ai_text
            except (KeyError, IndexError) as e:
                return f"Error parsing AI response: {e}\nResponse: {suggestions}"
        else:
            return f"Error: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as e:
        return f"Network error: {e}"



@app.route('/')
def home():
    try:
        if not supabase:
            flash('Database connection not available. Please check configuration.', 'error')
            return render_template('home.html', posts=[])
        
        # Fetch published blog posts and their authors from the 'profiles' table
        response = supabase.table('blog_posts').select('*, profiles(first_name, last_name)').eq('published', True).order('created_at', desc=True).execute()
        posts = response.data if response.data else []
        
        # Rename 'profiles' to 'author' for template compatibility
        for post in posts:
            if 'profiles' in post and post['profiles']:
                post['author'] = post['profiles']
            else:
                post['author'] = {'first_name': 'Unknown', 'last_name': 'User'}
            # del post['profiles']  # Optional: clean up original key
        
        return render_template('home.html', posts=posts)
    except Exception as e:
        flash(f'Error loading posts: {str(e)}', 'error')
        return render_template('home.html', posts=[])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        password = request.form.get('password')

        if not all([first_name, last_name, email, password]):
            flash('All fields are required.', 'error')
            return render_template('auth/register.html')

        try:
            # Bypassing OTP, directly creating user
            auth_response = supabase.auth.sign_up({
                'email': email,
                'password': password,
                'options': {
                    'user_metadata': {
                        'first_name': first_name,
                        'last_name': last_name
                    }
                }
            })

            if auth_response.user:
                # The database trigger 'on_auth_user_created' now handles profile creation.
                flash('Registration successful! Please log in.', 'success')
                return redirect(url_for('login'))
            else:
                # This part might not be reached if sign_up throws an exception for existing users
                flash('Failed to create user. The email may already be registered.', 'error')

        except Exception as e:
            error_message = str(e)
            logger.error(f"Direct registration failed for {email}. Error: {error_message}")
            if 'user already registered' in error_message.lower():
                flash('This email is already registered. Please log in.', 'error')
            else:
                flash(f'An unexpected error occurred during registration: {error_message}', 'error')

    return render_template('auth/register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # First, check for static admin credentials
        if email == 'admin@gmail.com' and password == 'admin@1234':
            session['user_id'] = 'admin_user'  # Use a special identifier for the static admin
            session['is_admin'] = True
            session['user_email'] = email
            session['user_name'] = 'Admin'
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))

        # If not admin, proceed with Supabase authentication for regular users
        try:
            auth_response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            
            if auth_response.user:
                session['user_id'] = auth_response.user.id
                session['user_email'] = auth_response.user.email

                # For all non-static-admin users, is_admin is ALWAYS False
                session['is_admin'] = False
                
                # We still need to get their name from the profile
                profile_response = supabase.table('profiles').select('first_name').eq('id', auth_response.user.id).single().execute()
                if profile_response.data:
                    # Use the first name, or default to 'User' if it's None or empty
                    session['user_name'] = profile_response.data.get('first_name') or 'User'
                else:
                    session['user_name'] = 'User'
                
                flash('Login successful!', 'success')
                return redirect(url_for('dashboard'))

        except Exception as e:
            flash(f'Login failed. Please check your credentials.', 'error')
            return redirect(url_for('login'))

    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    try:
        supabase.auth.sign_out()
    except:
        pass
    
    session.clear()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('home'))

@app.route('/delete-account', methods=['GET', 'POST'])
@login_required
def delete_account():
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_delete = request.form.get('confirm_delete')
        
        if not password:
            flash('Password is required to delete your account.', 'error')
            return render_template('auth/delete_account.html')
        
        if confirm_delete != 'DELETE':
            flash('Please type "DELETE" to confirm account deletion.', 'error')
            return render_template('auth/delete_account.html')
        
        try:
            user_id = session['user_id']
            user_email = session['user_email']
            
            # Verify password by attempting to sign in
            try:
                verify_response = supabase.auth.sign_in_with_password({
                    "email": user_email,
                    "password": password
                })
                
                if not verify_response.user:
                    flash('Invalid password. Account deletion cancelled.', 'error')
                    return render_template('auth/delete_account.html')
            except Exception as auth_error:
                flash('Invalid password. Account deletion cancelled.', 'error')
                return render_template('auth/delete_account.html')
            
            # Delete user's blog posts first (cascade will handle this, but let's be explicit)
            supabase.table('blog_posts').delete().eq('author_id', user_id).execute()
            
            # Delete user's OTP records
            supabase.table('user_otp').delete().eq('user_id', user_id).execute()
            
            # Delete user profile (this will cascade to auth.users due to foreign key)
            supabase.table('profiles').delete().eq('id', user_id).execute()
            
            # Clear session
            session.clear()
            
            flash('Your account has been permanently deleted. We\'re sorry to see you go!', 'success')
            return redirect(url_for('home'))
            
        except Exception as e:
            flash(f'Error deleting account: {str(e)}', 'error')
            print(f"Account deletion error: {e}")
    
    return render_template('auth/delete_account.html')

@app.route('/dashboard')
@login_required
def dashboard():
    try:
        # Get user's blog posts
        response = supabase.table('blog_posts').select('*').eq('author_id', session['user_id']).order('created_at', desc=True).execute()
        posts = response.data if response.data else []
        
        return render_template('dashboard.html', posts=posts)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('dashboard.html', posts=[])

@app.route('/create-post', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        video_url = request.form.get('video_url', '')
        action = request.form.get('action', 'draft')

        if not title or not content:
            flash('Title and content are required.', 'error')
            return render_template('blog/create.html', title=title, content=content, video_url=video_url)

        # Determine the published state based on the action
        is_published = (action == 'publish')

        cover_image_url = None
        try:
            if 'cover_image' in request.files:
                file = request.files['cover_image']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    # Ensure a unique path for each user's uploads
                    user_id = session['user_id']
                    unique_path = f"{user_id}/{uuid.uuid4()}_{filename}"
                    
                    file.seek(0) # Reset file pointer before reading
                    file_data = file.read()
                    
                    supabase.storage.from_('blog-images').upload(path=unique_path, file=file_data)
                    cover_image_url = supabase.storage.from_('blog-images').get_public_url(unique_path)
        except Exception as storage_error:
            logger.error(f"Cover image upload failed: {storage_error}")
            flash('Cover image failed to upload, but you can add it later by editing the post.', 'warning')

        try:
            post_data = {
                'author_id': session['user_id'],
                'title': title,
                'content': content,
                'video_links': [video_url.strip()] if video_url and video_url.strip() else [],
                'cover_image_url': cover_image_url,
                'published': is_published
            }

            response = supabase.table('blog_posts').insert(post_data).execute()

            if response.data:
                status = 'published' if post_data['published'] else 'saved as a draft'
                flash(f'Blog post successfully {status}!', 'success')
                return redirect(url_for('dashboard'))
            else:
                # This path may not be hit if an exception is raised, but is a good fallback.
                logger.error("Post creation failed with no data and no exception.")
                flash('An unknown error occurred while creating the post.', 'error')

        except Exception as e:
            error_message = str(e)
            logger.error(f"Failed to create post for user '{session['user_id']}'. Error: {error_message}")
            if 'permission denied' in error_message.lower():
                flash('Error: You do not have permission to create a post. Please check the RLS policies.', 'error')
            elif 'duplicate key value' in error_message.lower():
                flash('A post with this title may already exist.', 'error')
            else:
                flash('An unexpected database error occurred. Please try again.', 'error')

        # If we reach here, an error occurred, so render the form again with entered data
        return render_template('blog/create.html', title=title, content=content, video_url=video_url)

    return render_template('blog/create.html')

@app.route('/edit-post/<uuid:post_id>', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    try:
        response = supabase.table('blog_posts').select('*').eq('id', str(post_id)).eq('author_id', session['user_id']).single().execute()
        post = response.data

        if not post:
            flash('Post not found or you do not have permission to edit it.', 'error')
            return redirect(url_for('dashboard'))

        if request.method == 'POST':
            post_data = {
                'title': request.form.get('title'),
                'content': request.form.get('content'),
                'published': request.form.get('action') == 'publish',
                'updated_at': datetime.utcnow().isoformat()
            }
            
            supabase.table('blog_posts').update(post_data).eq('id', str(post_id)).execute()
            flash('Blog post updated successfully!', 'success')
            return redirect(url_for('dashboard'))

        return render_template('blog/edit.html', post=post)
    except Exception as e:
        flash(f'An error occurred: {e}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/delete-post/<post_id>', methods=['POST'])
@login_required
def delete_post(post_id):
    try:
        post_response = supabase_admin.table('blog_posts').select('author_id').eq('id', post_id).single().execute()

        is_author = post_response.data and post_response.data['author_id'] == session.get('user_id')
        is_admin = session.get('is_admin')

        if is_author or is_admin:
            supabase_admin.table('blog_posts').delete().eq('id', post_id).execute()
            flash('Post deleted successfully.', 'success')
        else:
            flash('You are not authorized to delete this post.', 'error')
    except Exception as e:
        flash(f'Error deleting post: {str(e)}', 'error')
    
    # Redirect back to the user's dashboard or the admin dashboard
    if is_admin and request.referrer and 'admin' in request.referrer:
        return redirect(url_for('admin_dashboard'))
    return redirect(url_for('dashboard'))

@app.route('/post/<uuid:post_id>')
def view_post(post_id):
    try:
        response = supabase.table('blog_posts').select('*, profiles(first_name, last_name)').eq('id', str(post_id)).single().execute()
        post = response.data

        if not post or (not post['published'] and (not session.get('user_id') or session['user_id'] != post['author_id'])):
            flash('Post not found or you do not have permission to view it.', 'error')
            return redirect(url_for('home'))

        if 'profiles' in post and post['profiles']:
            post['author'] = post['profiles']
        else:
            post['author'] = {'first_name': 'Unknown', 'last_name': 'User'}

        return render_template('blog/view.html', post=post)
    except Exception as e:
        flash(f'Error loading post: {e}', 'error')
        return redirect(url_for('home'))

# AI-powered features
def _call_gemini_api(prompt, content):
    """Helper function to call the Gemini API with robust error handling."""
    if not model:
        return jsonify({'error': 'AI service is not configured. Please check your GEMINI_API_KEY.'}), 503
    if not content:
        return jsonify({'error': 'Content is required.'}), 400

    try:
        full_prompt = f"{prompt}\n\n---\n\n{content}"
        response = model.generate_content(full_prompt)
        # It's good practice to check if the response has the expected text attribute.
        if hasattr(response, 'text'):
            return response.text
        else:
            logger.error(f"Gemini API response was empty or malformed. Response: {response}")
            return None
    except Exception as e:
        logger.error(f"Gemini API call failed. Error: {str(e)}")
        # Check for common, specific API errors to give better feedback
        error_msg = str(e).lower()
        if 'api_key' in error_msg:
            user_message = 'AI service authentication failed. Please check your API key.'
        elif 'permission_denied' in error_msg or 'quota' in error_msg:
            user_message = 'You have exceeded your API quota or lack permissions.'
        elif 'model' in error_msg and 'not found' in error_msg:
            user_message = 'The configured AI model is not available. Please contact support.'
        else:
            user_message = 'An unexpected error occurred with the AI service.'
        return jsonify({'error': user_message}), 500

@app.route('/ai/suggest-headline', methods=['POST'])
@login_required
def suggest_headline():
    content = request.json.get('content', '')
    prompt = "Generate 5 engaging, concise, and SEO-friendly blog post headlines for the following content. Return only the headlines, each on a new line."
    result = _call_gemini_api(prompt, content)
    if isinstance(result, str):
        headlines = [h.strip() for h in result.strip().split('\n') if h.strip()]
        return jsonify({'headlines': headlines})
    return result # Returns the JSON error response from the helper

@app.route('/ai/generate-summary', methods=['POST'])
@login_required
def generate_summary():
    content = request.json.get('content', '')
    prompt = "Summarize this blog post in 2-3 concise sentences, capturing the main points."
    result = _call_gemini_api(prompt, content)
    if isinstance(result, str):
        return jsonify({'summary': result.strip()})
    return result

@app.route('/ai/suggest-keywords', methods=['POST'])
@login_required
def suggest_keywords():
    content = request.json.get('content', '')
    prompt = "Suggest 5-7 relevant SEO keywords for this blog post. Return them as a single, comma-separated list."
    result = _call_gemini_api(prompt, content)
    if isinstance(result, str):
        keywords = [k.strip() for k in result.strip().split(',') if k.strip()]
        return jsonify({'keywords': keywords})
    return result

@app.route('/ai/improve-content', methods=['POST'])
@login_required
def improve_content():
    content = request.json.get('content', '')
    prompt = "Improve this blog content for better readability, engagement, and clarity. Fix any grammatical errors and enhance the flow, but retain the original meaning."
    result = _call_gemini_api(prompt, content)
    if isinstance(result, str):
        return jsonify({'improved_content': result.strip()})
    return result

# AI Chatbot Route
@app.route('/ai/chatbot', methods=['POST'])
@login_required
def ask_chatbot():
    """Enhanced AI chatbot with context awareness and personalized responses."""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Message is required.'}), 400

        if not model:
            return jsonify({'error': 'AI service is not available right now. Please try again later.'}), 503

        # Get user context for personalized responses
        user_name = session.get('user_name', 'User')
        user_email = session.get('user_email', '')
        is_admin = session.get('is_admin', False)
        
        # Create context-aware prompt
        context_prompt = f"""
You are an AI assistant for a blog platform called "AI BlogPlatform". You are helping {user_name}.

User Context:
- Name: {user_name}
- Email: {user_email}
- Role: {'Admin' if is_admin else 'Regular User'}

Platform Features Available:
- Create and edit blog posts with AI assistance
- AI-powered content suggestions (headlines, summaries, SEO keywords)
- Dashboard to manage posts and profile
- Admin features (if admin): user management, post moderation

Your Role:
- Be helpful, friendly, and concise
- Provide specific guidance about using the platform
- Offer writing tips and content creation advice
- Help with navigation and feature discovery
- Keep responses under 150 words unless detailed explanation is needed
- Use emojis sparingly but appropriately
- If asked about technical issues, provide practical solutions

User's message: {user_message}

Provide a helpful, personalized response:
"""

        try:
            response = model.generate_content(context_prompt)
            
            if hasattr(response, 'text') and response.text:
                bot_response = response.text.strip()
                
                # Log the interaction for debugging
                logger.info(f"Chatbot interaction - User: {user_email}, Message: {user_message[:50]}...")
                
                return jsonify({
                    'response': bot_response,
                    'status': 'success'
                })
            else:
                logger.error("Gemini API returned empty response")
                return jsonify({
                    'response': "I'm having trouble processing your request right now. Could you please try rephrasing your question?",
                    'status': 'fallback'
                })
                
        except Exception as api_error:
            logger.error(f"Gemini API error: {str(api_error)}")
            
            # Provide intelligent fallback responses based on common queries
            fallback_responses = {
                'help': f"Hi {user_name}! I can help you with:\n\n• Writing better blog posts\n• Using AI features for content creation\n• Navigating the platform\n• Tips for engaging content\n\nWhat would you like to know more about?",
                'write': "Here are some writing tips:\n\n• Start with a compelling headline\n• Use short paragraphs for readability\n• Include relevant images\n• End with a call-to-action\n• Use our AI suggestions for improvement!",
                'dashboard': "Your dashboard shows:\n\n• Your published and draft posts\n• Writing statistics\n• Profile management\n• AI writing tools\n\nNeed help with any specific feature?",
                'ai': "Our AI features include:\n\n• Headline suggestions\n• Content improvement\n• SEO keyword generation\n• Content summaries\n\nTry them when creating or editing posts!"
            }
            
            # Simple keyword matching for fallback
            message_lower = user_message.lower()
            for keyword, response in fallback_responses.items():
                if keyword in message_lower:
                    return jsonify({
                        'response': response,
                        'status': 'fallback'
                    })
            
            # Generic fallback
            return jsonify({
                'response': f"Thanks for your message, {user_name}! I'm having some technical difficulties right now, but I'm here to help with writing, platform navigation, and content creation. What specific area would you like assistance with?",
                'status': 'fallback'
            })
            
    except Exception as e:
        logger.error(f"Chatbot error: {str(e)}")
        return jsonify({
            'error': 'Sorry, I encountered an unexpected error. Please try again.',
            'status': 'error'
        }), 500

# Admin routes
@app.route('/admin', methods=['GET', 'POST'])
@admin_required
def admin_dashboard():
    try:
        if not supabase:
            flash('Database connection not available.', 'error')
            return render_template('admin/dashboard.html', users=[], posts=[])
            
        if request.method == 'POST':
            # Handle the 'Create User' form submission
            email = request.form.get('email')
            password = request.form.get('password')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            is_admin = 'is_admin' in request.form

            try:
                # Create the user in Supabase Auth
                auth_response = supabase_admin.auth.create_user({
                    "email": email,
                    "password": password,
                })

                if auth_response.user:
                    user_id = auth_response.user.id
                    # Create the user's profile
                    supabase_admin.table('profiles').insert({
                        'id': user_id,
                        'email': email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'is_admin': is_admin
                    }).execute()
                    flash('User created successfully!', 'success')
                else:
                    flash('Failed to create user in Auth.', 'error')
            except Exception as e:
                flash(f'Error creating user: {str(e)}', 'error')
            
            return redirect(url_for('admin_dashboard'))

        # GET request: Display the dashboard. Use admin client to bypass RLS.
        users_response = supabase_admin.table('profiles').select('*', count='exact').execute()
        posts_response = supabase_admin.table('blog_posts').select('*, profiles(first_name, last_name)').order('created_at', desc=True).execute()
        
        users = users_response.data if users_response.data else []
        posts = posts_response.data if posts_response.data else []

        total_users = users_response.count
        admin_count = sum(1 for user in users if user.get('is_admin'))

        return render_template('admin/dashboard.html', users=users, posts=posts, total_users=total_users, admin_count=admin_count)
        
    except Exception as e:
        flash(f'Error loading admin dashboard: {str(e)}', 'error')
        return render_template('admin/dashboard.html', users=[], posts=[])

@app.route('/admin/delete-user/<user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    try:
        # Use the service role client to delete the user
        supabase_admin.auth.admin.delete_user(user_id)
        flash('User deleted successfully.', 'success')
    except Exception as e:
        flash(f'Failed to delete user: {e}', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/ai-suggest', methods=['POST'])
@login_required
def ai_suggest():
    try:
        blog_content = request.form.get('content', '')
        if not blog_content:
            flash('Please write some blog content first.', 'error')
            return redirect(request.referrer)

        ai_suggestions = generate_content_suggestions(blog_content)

        flash('AI Suggestions generated successfully!', 'success')
        return render_template('blog/create.html', suggestions=ai_suggestions, content=blog_content)

    except Exception as e:
        flash(f'Error generating AI suggestions: {str(e)}', 'error')
        return redirect(request.referrer)

@app.route('/profile')
@login_required
def profile():
    try:
        user_id = session['user_id']
        
        # Fetch user profile data
        profile_response = supabase.table('profiles').select('*').eq('id', user_id).single().execute()
        user_profile = profile_response.data
        
        # Fetch user's blog posts
        posts_response = supabase.table('blog_posts').select('*').eq('author_id', user_id).order('created_at', desc=True).execute()
        posts = posts_response.data if posts_response.data else []
        
        if not user_profile:
            flash('User profile not found.', 'error')
            return redirect(url_for('dashboard'))
            
        return render_template('auth/profile.html', user=user_profile, posts=posts)
        
    except Exception as e:
        flash(f'Error loading profile: {str(e)}', 'error')
        return redirect(url_for('dashboard'))



if __name__ == '__main__':
    app.run(debug=True, port=5000)
