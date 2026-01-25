from flask import Flask, render_template, request, redirect, url_for, flash, abort, Response
import json
from datetime import datetime
from dotenv import load_dotenv
from functools import wraps
import os

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret")


POSTS_FILE = "instance/posts.json"


def load_posts():
    try:
        with open(POSTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except Exception:
        return []


def save_posts(posts):
    os.makedirs(os.path.dirname(POSTS_FILE), exist_ok=True)
    with open(POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, indent=2)

@app.route("/")
def home():
    # Use latest post as preview if available
    blog_preview = "No blog posted today."
    posts = load_posts()
    if posts:
        latest = sorted(posts, key=lambda p: p.get("timestamp", ""), reverse=True)[0]
        content = latest.get("content", "")
        # Use first line or first 150 chars as preview
        blog_preview = (content.splitlines()[0][:150] + ("..." if len(content) > 150 else "")) if content else "No blog posted today."

    config = get_config()
    config['blog_preview'] = blog_preview
    return render_template("index.html", **config)

@app.route("/about")
def about():
    config = get_config()
    return render_template("about.html", **config)
@app.route('/practice')
def practice():
    config = get_config()
    practice_areas = [
        {"name": "Criminal Law", "icon": "fa-gavel"},
        {"name": "Family Law", "icon": "fa-people-roof"},
        {"name": "Corporate Law", "icon": "fa-building"},
        {"name": "Civil Litigation", "icon": "fa-scale-balanced"},
        {"name": "Intellectual Property", "icon": "fa-lightbulb"},
        {"name": "Real Estate", "icon": "fa-house"},
        {"name": "Consumer Protection", "icon": "fa-shield-halved"},
        {"name": "Employment Law", "icon": "fa-briefcase"},
        {"name": "Tax Law", "icon": "fa-coins"},
        {"name": "Cyber Law", "icon": "fa-shield-virus"},
        {"name": "Environmental Law", "icon": "fa-leaf"},
        {"name": "Immigration Law", "icon": "fa-passport"},
        {"name": "Banking & Finance", "icon": "fa-piggy-bank"},
        {"name": "Constitutional Law", "icon": "fa-landmark"},
        {"name": "Contract Law", "icon": "fa-file-signature"},
        {"name": "Insurance Law", "icon": "fa-file-invoice-dollar"}
    ]
    config['practice_areas'] = practice_areas
    return render_template('practice.html', **config)

@app.route("/contact")
def contact():
    config = get_config()
    return render_template("contact.html", **config)


@app.route('/blog')
def blog():
    # List all posts (most recent first)
    posts = load_posts()
    posts_sorted = sorted(posts, key=lambda p: p.get("timestamp", ""), reverse=True)
    config = get_config()
    config['posts'] = posts_sorted
    return render_template('blog.html', **config)


@app.route('/blog/<int:post_id>')
def view_post(post_id):
    posts = load_posts()
    post = next((p for p in posts if p.get("id") == post_id), None)
    config = get_config()
    config['post'] = post
    return render_template('post.html', **config) if post else (render_template('post.html', **config), 404)


@app.route('/latest_blog')
def latest_blog():
    posts = load_posts()
    if not posts:
        return redirect(url_for('blog'))
    latest = sorted(posts, key=lambda p: p.get('timestamp', ''), reverse=True)[0]
    return redirect(url_for('view_post', post_id=latest.get('id')))


def check_credentials(username, password):
    expected_user = os.getenv("PUBLISH_USER")
    expected_pass = os.getenv("PUBLISH_PASS")
    return bool(expected_user and expected_pass and username == expected_user and password == expected_pass)


@app.route("/admin/write", methods=["GET", "POST"])
def admin_write():
    # In-page credential flow: GET shows login form; POST can be 'login' to show write form
    # or 'publish' to save a post. No server-side session; user must re-authenticate each visit.
    message = None
    if request.method == "POST":
        action = request.form.get("action")
        if action == "login":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if check_credentials(username, password):
                # Show write form; include username/password as hidden fields so publish can re-check
                return render_template("admin_write.html", firm_name=os.getenv("FIRM_NAME"), mode="write", username=username, password=password)
            else:
                flash("Invalid credentials", "danger")
                return render_template("admin_write.html", firm_name=os.getenv("FIRM_NAME"), mode="login")

        if action == "publish":
            # Validate credentials again from the form
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            if not check_credentials(username, password):
                flash("Invalid credentials", "danger")
                return render_template("admin_write.html", firm_name=os.getenv("FIRM_NAME"), mode="login")

            title = request.form.get("title", "").strip()
            content = request.form.get("blog_content", "").strip()
            if not title or not content:
                flash("Title and content are required", "danger")
                return render_template("admin_write.html", firm_name=os.getenv("FIRM_NAME"), mode="write", username=username)

            try:
                posts = load_posts()
                next_id = max((p.get("id", 0) for p in posts), default=0) + 1
                post = {
                    "id": next_id,
                    "title": title,
                    "content": content,
                    "author": os.getenv("FIRM_NAME", "Admin"),
                    "timestamp": datetime.utcnow().isoformat()
                }
                posts.append(post)
                save_posts(posts)
                message = "Post published successfully."
            except Exception as e:
                message = f"Failed to save post: {e}"

            return redirect(url_for("view_post", post_id=post.get("id")))

    # Default: show login form
    return render_template("admin_write.html", firm_name=os.getenv("FIRM_NAME"), mode="login")


def get_config():
    return {
        'firm_name': os.getenv('FIRM_NAME', 'Lexway Solutions'),
        'lawyer_name': os.getenv('LAWYER_NAME', 'Advocate Ashish Patil'),
        'hero_tagline': os.getenv('HERO_TAGLINE', ''),
        'hero_button_1': os.getenv('HERO_BUTTON_1', 'Consult Now'),
        'hero_button_2': os.getenv('HERO_BUTTON_2', 'Practice Areas'),
        'about_title': os.getenv('ABOUT_TITLE', 'About'),
        'about_description': os.getenv('ABOUT_DESCRIPTION', ''),
        'about_description_2': os.getenv('ABOUT_DESCRIPTION_2', ''),
        'contact_address': os.getenv('CONTACT_ADDRESS', ''),
        'contact_phone': os.getenv('CONTACT_PHONE', ''),
        'contact_email': os.getenv('CONTACT_EMAIL', ''),
        'color_primary': os.getenv('COLOR_PRIMARY', '#20200c'),
        'color_secondary': os.getenv('COLOR_SECONDARY', '#e3e3d6'),
        'color_background': os.getenv('COLOR_BACKGROUND', '#d6d6c1'),
        'color_accent': os.getenv('COLOR_ACCENT', '#84846f'),
        'color_white': os.getenv('COLOR_WHITE', '#ffffff'),
        'color_about_bg': os.getenv('COLOR_ABOUT_BG', '#f5f5f5'),
        'image_logo': os.getenv('IMAGE_LOGO', 'images/logo.png'),
        'image_about': os.getenv('IMAGE_ABOUT', 'images/about_lawyer.png'),
        'image_hero_bg': os.getenv('IMAGE_HERO_BG', 'images/law-office-bg.jpg'),
        'homepage_bg': os.getenv('HOMEPAGE_BG', 'images/homepage_bg.png'),
    }

@app.route('/static/css/style.css')
def dynamic_style():
    config = get_config()
    response = Response(render_template('style.css', **config), mimetype='text/css')
    return response

if __name__ == "__main__":
    app.run(debug=True)
