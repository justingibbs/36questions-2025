from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import HTMLResponse
import firebase_admin
from firebase_admin import auth
from app.auth.firebase_auth import require_auth

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
    <head>
        <title>Auth Demo</title>
        <script src="https://unpkg.com/htmx.org@1.9.10"></script>
        <!-- Add Firebase SDK -->
        <script src="https://www.gstatic.com/firebasejs/9.6.1/firebase-app-compat.js"></script>
        <script src="https://www.gstatic.com/firebasejs/9.6.1/firebase-auth-compat.js"></script>
    </head>
    <body>
        <div id="auth-container">
            <h1>Welcome</h1>
            <div hx-get="/login-form" 
                 hx-trigger="load"
                 hx-swap="innerHTML">
            </div>
        </div>

        <script>
            // Your Firebase config
            const firebaseConfig = {
                apiKey: "AIzaSyC3mwZOTbEuhV168RCd_Jrq23RMGLMa8Ss",
                authDomain: "questions-2025.firebaseapp.com",
                projectId: "questions-2025",
                storageBucket: "questions-2025.firebasestorage.app",
                messagingSenderId: "734601910603",
                appId: "1:734601910603:web:69de58411c480d8b9c70ce",
                measurementId: "G-WZVP0NNP0N"
            };

            // Initialize Firebase
            firebase.initializeApp(firebaseConfig);
        </script>
    </body>
    </html>
    """

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
