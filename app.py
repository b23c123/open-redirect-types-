import requests
from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

# Allowed external domains for safe redirections (Modify for security testing)
ALLOWED_DOMAINS = ["example.com"]

def is_internal_url(url):
    """Check if the URL is internal (localhost, 127.0.0.1, AWS metadata, or internal network)."""
    from urllib.parse import urlparse
    parsed_url = urlparse(url)

    # Blocked internal hosts for preventing SSRF
    blocked_hosts = ["localhost", "127.0.0.1", "169.254.169.254"]
    
    # If hostname is in blocked list or in a private network range
    return parsed_url.hostname in blocked_hosts or parsed_url.netloc.startswith("192.168.")

@app.route("/")
def home():
    return """
    <h2>🚀 Open Redirect & SSRF Vulnerable App</h2>
    <ul>
         <li><a href="/header_redirect?next=https://evil.com">Header-Based Redirect</a></li>
         <li><a href="/host_redirect"> Header-Based Redirect (X-Forwarded-Host)</a></li> 
         <li><a href="/js_redirect#https://evil.com">JavaScript-Based Redirect</a></li>
         <li><a href="/meta_redirect?next=https://evil.com">Meta Refresh Redirect</a></li>
         <li><a href="/parameter_redirect?url=https://evil.com">Parameter-Based Redirect</a></li>
         <li><a href="/oauth_login?redirect_uri=https://evil.com">OAuth Redirect</a></li>
    </ul>
    """

### **1️⃣ Header-Based Redirect with SSRF**
@app.route("/header_redirect")
def header_redirect():
    next_page = request.args.get("next")

    if not next_page:
        return "No redirect specified.", 400

    # 🚨 If the target is an internal resource, perform SSRF
    if is_internal_url(next_page):
        try:
            response = requests.get(next_page, timeout=5)
            return f"🚨 SSRF Response from {next_page}:<br><pre>{response.text}</pre>"
        except requests.exceptions.RequestException as e:
            return f"❌ SSRF Failed: {str(e)}", 500

    # Otherwise, perform Open Redirect
    return redirect(next_page)

### **2️⃣ Header-Based Redirect via X-Forwarded-Host**
@app.route("/host_redirect")
def host_redirect():
    host = request.headers.get("X-Forwarded-Host", "example.com")
    return redirect(f"https://{host}/dashboard")

### **3️⃣ JavaScript-Based Redirect (Client-Side)**
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

### **4️⃣ Parameter-Based Redirect with SSRF**
@app.route("/parameter_redirect")
def parameter_redirect():
    url = request.args.get("url", "/")

    if is_internal_url(url):
        try:
            response = requests.get(url, timeout=5)
            return f"🚨 SSRF Response from {url}:<br><pre>{response.text}</pre>"
        except requests.exceptions.RequestException as e:
            return f"❌ SSRF Failed: {str(e)}", 500

    return redirect(url)

### **5️⃣ Meta Refresh Redirect (HTML-Based)**
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

### **6️⃣ OAuth/SSO-Style Redirect (Exploitable)**
@app.route("/oauth_login")
def oauth_login():
    """Simulated OAuth Login Page"""
    redirect_uri = request.args.get("redirect_uri", "/")

    login_form = f"""
    <html>
    <body>
        <h2>🔐 Fake OAuth Login</h2>
        <p>Simulating OAuth login page...</p>
        <form action="/oauth_callback" method="POST">
            <input type="hidden" name="redirect_uri" value="{redirect_uri}">
            <input type="text" name="username" placeholder="Username" required><br>
            <input type="password" name="password" placeholder="Password" required><br>
            <button type="submit">Login</button>
        </form>
    </body>
    </html>
    """
    return render_template_string(login_form)

@app.route("/oauth_callback", methods=["POST"])
def oauth_callback():
    """Simulated OAuth Callback - Vulnerable to Open Redirect"""
    redirect_uri = request.form.get("redirect_uri", "/")
    
    # 🚨 Exploitable Open Redirect Here
    return redirect(redirect_uri)

if __name__ == "__main__":
    app.run(debug=True)
