from flask import Flask, request, redirect, render_template_string
import uuid
import requests

app = Flask(__name__)

# ذخیره موقتی state و code برای شبیه‌سازی فرآیند OAuth
tokens = {}

@app.route("/")
def home():
    return """
    <h2>🚀 Open Redirect Vulnerable App</h2>
     <img src="https://raw.githubusercontent.com/b23c123/open-redirect-types-/main/static/xss.png" alt="XSS Example" width="300">
    <ul>
         <li><a href="/header_redirect?next=https://evil.com">Header-Based Redirect</a></li>
        <li><a href="/host_redirect"> Header-Based Redirect (x-forward)</a></li> 
        <li><a href="/js_redirect#https://evil.com">JavaScript-Based Redirect</a></li>
        <li><a href="/meta_redirect?next=https://evil.com">Meta Refresh Redirect</a></li>
        <li><a href="/parameter_redirect?url=https://evil.com">Parameter-Based Redirect</a></li>
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

    # تولید کد احراز هویت
    auth_code = str(uuid.uuid4())
    tokens[state] = auth_code

    # هدایت کاربر به redirect_uri (اینجا به سرور مهاجم 8081 هدایت می‌شود)
    return redirect(f"{redirect_uri}?state={state}&code={auth_code}", code=302)



if __name__ == "__main__":
    app.run(port=5000, debug=True)
