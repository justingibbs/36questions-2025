from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import firebase_admin
from firebase_admin import auth, credentials
from app.auth.firebase_auth import require_auth
from app.routes.chat import router as chat_router
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Firebase only if it hasn't been initialized
if not firebase_admin._apps:  # Check if no Firebase app exists
    service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH')
    print(f"Looking for service account at: {service_account_path}")
    cred = credentials.Certificate(service_account_path)
    firebase_admin.initialize_app(cred)

app = FastAPI()

# Mount static files (for any additional static assets)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Include routes
app.include_router(chat_router, prefix="")  # No prefix if you want /dashboard directly

@app.get("/", response_class=HTMLResponse)
async def home():
    return FileResponse("app/static/index.html")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return FileResponse("app/static/dashboard.html")

@app.get("/login-form", response_class=HTMLResponse)
async def login_form():
    return """
        <div id="login-form">
            <h2>Login</h2>
            <form id="login-form" onsubmit="handleLogin(event)">
                <div>
                    <label for="email">Email:</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <div>
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit">Login</button>
            </form>
            <p>
                <a href="#" hx-get="/signup-form" hx-target="#auth-container">
                    Need an account? Sign up
                </a>
            </p>

            <script>
                async function handleLogin(event) {
                    event.preventDefault();
                    const email = document.getElementById('email').value;
                    const password = document.getElementById('password').value;
                    
                    try {
                        const userCredential = await firebase.auth().signInWithEmailAndPassword(email, password);
                        const idToken = await userCredential.user.getIdToken();
                        
                        // Use HTMX to load protected content with the ID token
                        htmx.ajax('GET', '/protected', {
                            headers: {
                                'Authorization': 'Bearer ' + idToken
                            },
                            target: '#auth-container'
                        });
                    } catch (error) {
                        alert('Login failed: ' + error.message);
                    }
                }
            </script>
        </div>
    """

@app.get("/signup-form", response_class=HTMLResponse)
async def signup_form():
    return """
        <div id="signup-form">
            <h2>Sign Up</h2>
            <form hx-post="/signup" hx-target="#auth-container">
                <div>
                    <label for="email">Email:</label>
                    <input type="email" id="email" name="email" required>
                </div>
                <div>
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit">Sign Up</button>
            </form>
            <p>
                <a href="#" hx-get="/login-form" hx-target="#auth-container">
                    Already have an account? Login
                </a>
            </p>
        </div>
    """

@app.post("/signup", response_class=HTMLResponse)
async def signup(request: Request):
    form_data = await request.form()
    email = form_data.get('email')
    password = form_data.get('password')
    
    try:
        user = auth.create_user(
            email=email,
            password=password,
            email_verified=False
        )
        # Send verification email
        link = auth.generate_email_verification_link(email)
        # Here you would typically send the link via your email service
        
        return """
            <div>
                <h2>Verify Your Email</h2>
                <p>Please check your email to verify your account.</p>
                <a href="#" hx-get="/login-form" hx-target="#auth-container">
                    Return to login
                </a>
            </div>
        """
    except Exception as e:
        return f"""
            <div>
                <h2>Error</h2>
                <p>Could not create account: {str(e)}</p>
                <a href="#" hx-get="/signup-form" hx-target="#auth-container">
                    Try again
                </a>
            </div>
        """

@app.get("/protected", response_class=HTMLResponse)
@require_auth
async def protected_route(request: Request):
    user = request.state.user
    return f"""
        <div id="protected-content">
            <h2>Protected Content</h2>
            <p>Welcome, {user['email']}!</p>
            <button onclick="handleLogout()">Logout</button>

            <script>
                function handleLogout() {{
                    firebase.auth().signOut().then(() => {{
                        htmx.ajax('GET', '/login-form', {{
                            target: '#auth-container'
                        }});
                    }});
                }}
            </script>
        </div>
    """

@app.post("/logout", response_class=HTMLResponse)
async def logout():
    return """
        <div id="auth-container">
            <h1>Welcome</h1>
            <div hx-get="/login-form" 
                 hx-trigger="load"
                 hx-swap="innerHTML">
            </div>
            <script>
                // Clear the stored token
                localStorage.removeItem('authToken');
            </script>
        </div>
    """

@app.get("/api/user-info", response_class=HTMLResponse)
@require_auth
async def user_info(request: Request):
    user = request.state.user
    return f"""
        <div>
            <h2>Welcome, {user['email']}!</h2>
            <p>User ID: {user['uid']}</p>
        </div>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
