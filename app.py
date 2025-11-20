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

    return render_template("index.html",
                           firm_name=os.getenv("FIRM_NAME"),
                           tagline=os.getenv("TAGLINE"),
                           blog_preview=blog_preview)

@app.route("/about")
def about():
    return render_template(
        "about.html",
        firm_name=os.getenv("FIRM_NAME"),
        tagline=os.getenv("TAGLINE")
    )
@app.route('/practice')
def practice():
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
    return render_template('practice.html', firm_name=os.getenv("FIRM_NAME"), practice_areas=practice_areas)

@app.route("/contact")
def contact():
    return render_template("contact.html", firm_name=os.getenv("FIRM_NAME"), tagline=os.getenv("TAGLINE"))


@app.route('/blog')
def blog():
    # List all posts (most recent first)
    posts = load_posts()
    posts_sorted = sorted(posts, key=lambda p: p.get("timestamp", ""), reverse=True)
    return render_template('blog.html', firm_name=os.getenv("FIRM_NAME"), tagline=os.getenv("TAGLINE"), posts=posts_sorted)


@app.route('/blog/<int:post_id>')
def view_post(post_id):
    posts = load_posts()
    post = next((p for p in posts if p.get("id") == post_id), None)
    if not post:
        return render_template('post.html', firm_name=os.getenv("FIRM_NAME"), tagline=os.getenv("TAGLINE"), post=None), 404
    return render_template('post.html', firm_name=os.getenv("FIRM_NAME"), tagline=os.getenv("TAGLINE"), post=post)


def check_basic_auth(username, password):
    expected_user = os.getenv("PUBLISH_USER")
    expected_pass = os.getenv("PUBLISH_PASS")
    return expected_user and expected_pass and username == expected_user and password == expected_pass


def authenticate():
    return Response('Authentication required', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_basic_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_basic_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.route("/admin/write", methods=["GET", "POST"])
@requires_basic_auth
def admin_write():
    message = None
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        content = request.form.get("blog_content", "").strip()
        if not title or not content:
            flash("Title and content are required", "danger")
            return redirect(url_for("admin_write"))

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

    return render_template("admin_write.html", firm_name=os.getenv("FIRM_NAME"), message=message)


if __name__ == "__main__":
    app.run(debug=True)
