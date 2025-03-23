from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.auth.firebase_auth import require_auth

app = FastAPI()

# Public route
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
    <head>
        <title>Firebase Auth Demo</title>
        <!-- Firebase UI CSS -->
        <link type="text/css" rel="stylesheet" href="https://www.gstatic.com/firebasejs/ui/6.0.1/firebase-ui-auth.css" />
        
        <!-- Firebase App (compat) -->
        <script src="https://www.gstatic.com/firebasejs/11.5.0/firebase-app-compat.js"></script>
        <!-- Firebase Auth (compat) -->
        <script src="https://www.gstatic.com/firebasejs/11.5.0/firebase-auth-compat.js"></script>
        <!-- Firebase UI -->
        <script src="https://www.gstatic.com/firebasejs/ui/6.0.1/firebase-ui-auth.js"></script>
    </head>
    <body>
        <h1>Welcome</h1>
        <div id="firebaseui-auth-container"></div>
        <div id="loader">Loading...</div>
        <div id="message" style="display:none;"></div>

        <script>
            // Your web app's Firebase configuration
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

            // Check if user is already signed in
            firebase.auth().onAuthStateChanged((user) => {
                if (user) {
                    const messageDiv = document.getElementById('message');
                    messageDiv.style.display = 'block';
                    
                    if (!user.emailVerified) {
                        messageDiv.innerHTML = `
                            <p>Please verify your email address. 
                            <button onclick="sendVerificationEmail()">Resend verification email</button></p>
                        `;
                    } else {
                        // User is signed in and email is verified
                        firebase.auth().currentUser.getIdToken()
                            .then(token => {
                                fetch('/protected', {
                                    headers: {
                                        'Authorization': 'Bearer ' + token
                                    }
                                })
                                .then(response => response.text())
                                .then(html => {
                                    document.body.innerHTML = html;
                                });
                            });
                    }
                }
            });

            // Function to send verification email
            function sendVerificationEmail() {
                firebase.auth().currentUser.sendEmailVerification()
                    .then(() => {
                        document.getElementById('message').innerHTML = 
                            'Verification email sent! Please check your inbox.';
                    })
                    .catch((error) => {
                        document.getElementById('message').innerHTML = 
                            'Error sending verification email: ' + error.message;
                    });
            }

            // Initialize the FirebaseUI Widget using Firebase
            const ui = new firebaseui.auth.AuthUI(firebase.auth());

            // FirebaseUI config
            const uiConfig = {
                signInOptions: [
                    {
                        provider: firebase.auth.EmailAuthProvider.PROVIDER_ID,
                        requireDisplayName: false,
                        signInMethod: firebase.auth.EmailAuthProvider.EMAIL_PASSWORD_SIGN_IN_METHOD
                    }
                ],
                signInFlow: 'popup',
                callbacks: {
                    signInSuccessWithAuthResult: function(authResult, redirectUrl) {
                        const user = authResult.user;
                        if (!user.emailVerified) {
                            user.sendEmailVerification();
                            document.getElementById('message').innerHTML = 
                                'Please verify your email address. Check your inbox for a verification link.';
                        }
                        return false;
                    }
                }
            };

            // Start FirebaseUI
            ui.start('#firebaseui-auth-container', uiConfig);
        </script>
    </body>
    </html>
    """

# Protected route example
@app.get("/protected", response_class=HTMLResponse)
@require_auth
async def protected_route(request: Request):
    user = request.state.user
    return f"Hello {user['email']}, this is a protected route!"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
