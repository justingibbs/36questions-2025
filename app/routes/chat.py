from fastapi import APIRouter, Depends, HTTPException, Header, Form, Request
from fastapi.responses import HTMLResponse
import firebase_admin
from firebase_admin import auth, credentials
import os
from dotenv import load_dotenv
import json
from ..agents.question_agent import question_agent, QuestionDependencies

router = APIRouter()

# Load environment variables
load_dotenv()

# Get Firebase configuration from serviceAccount.json
service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY_PATH')
with open(service_account_path) as f:
    service_account = json.load(f)

@router.get("/", response_class=HTMLResponse)
async def login():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login</title>
        <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-app-compat.js"></script>
        <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-auth-compat.js"></script>
        <script src="https://www.gstatic.com/firebasejs/ui/6.0.1/firebase-ui-auth.js"></script>
        <link type="text/css" rel="stylesheet" href="https://www.gstatic.com/firebasejs/ui/6.0.1/firebase-ui-auth.css" />
    </head>
    <body>
        <h1>Login</h1>
        <div id="debug"></div>
        <div id="firebaseui-auth-container"></div>

        <script>
            function debug(message) {{
                console.log(message);
                const debugDiv = document.getElementById('debug');
                debugDiv.innerHTML += `<p>${{message}}</p>`;
            }}

            const firebaseConfig = {{
                projectId: '{service_account["project_id"]}',
                apiKey: '{os.getenv("FIREBASE_WEB_API_KEY")}',
                authDomain: '{service_account["project_id"]}.firebaseapp.com'
            }};

            debug('Firebase config: ' + JSON.stringify(firebaseConfig));

            try {{
                if (!firebase.apps.length) {{
                    debug('Initializing Firebase...');
                    firebase.initializeApp(firebaseConfig);
                }}

                const ui = new firebaseui.auth.AuthUI(firebase.auth());
                ui.start('#firebaseui-auth-container', {{
                    signInOptions: [
                        firebase.auth.GoogleAuthProvider.PROVIDER_ID,
                        firebase.auth.EmailAuthProvider.PROVIDER_ID
                    ],
                    callbacks: {{
                        signInSuccessWithAuthResult: function(authResult, redirectUrl) {{
                            debug('Sign in successful: ' + authResult.user.email);
                            return true;
                        }}
                    }},
                    signInSuccessUrl: '/dashboard'
                }});
            }} catch (error) {{
                debug('Error: ' + error.message);
            }}
        </script>
    </body>
    </html>
    """

async def get_current_user(request: Request, authorization: str = Header(None)):
    print(f"Authorization header: {authorization}")  # Debug print
    
    if not authorization or not authorization.startswith('Bearer '):
        raise HTTPException(status_code=401, detail="No token provided")
    
    token = authorization.split(' ')[1]
    try:
        user = auth.verify_id_token(token)
        print(f"Verified user: {user['uid']}")  # Debug print
        return user
    except Exception as e:
        print(f"Token verification error: {str(e)}")  # Debug print
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dashboard</title>
        <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-app-compat.js"></script>
        <script src="https://www.gstatic.com/firebasejs/10.8.0/firebase-auth-compat.js"></script>
        <style>
            #debug {{ 
                background: #f0f0f0; 
                padding: 10px; 
                margin: 10px 0; 
                border: 1px solid #ccc; 
            }}
            textarea {{
                width: 100%;
                min-height: 100px;
                margin: 10px 0;
            }}
            .button-group {{ margin: 10px 0; }}
            button {{ margin-right: 10px; padding: 5px 10px; }}
        </style>
    </head>
    <body>
        <div id="chat-container">
            <div id="user-info">Welcome <span id="user-email"></span></div>
            <button onclick="signOut()">Sign Out</button>
            
            <h1>36 Questions</h1>
            <div id="debug">Debug messages will appear here</div>
            <div id="chat-messages">Loading next question...</div>
        </div>

        <script>
            function debugLog(message) {{
                console.log(message);
                const debug = document.getElementById('debug');
                debug.innerHTML += `<div>${{new Date().toISOString()}}: ${{message}}</div>`;
            }}

            const firebaseConfig = {{
                projectId: '{service_account["project_id"]}',
                apiKey: '{os.getenv("FIREBASE_WEB_API_KEY")}',
                authDomain: '{service_account["project_id"]}.firebaseapp.com'
            }};

            debugLog('Initializing Firebase...');
            if (!firebase.apps.length) {{
                firebase.initializeApp(firebaseConfig);
            }}

            // Global function to submit answer
            async function submitAnswer(questionId) {{
                debugLog('Submit button clicked for question ' + questionId);
                try {{
                    const answer = document.querySelector('textarea[name="answer"]').value;
                    if (!answer) {{
                        debugLog('No answer provided');
                        alert('Please enter an answer');
                        return;
                    }}

                    debugLog('Getting auth token...');
                    const token = await firebase.auth().currentUser.getIdToken();
                    debugLog('Got token, submitting answer...');

                    const response = await fetch(`/submit-answer/${{questionId}}`, {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'Authorization': `Bearer ${{token}}`
                        }},
                        body: `answer=${{encodeURIComponent(answer)}}`
                    }});

                    debugLog('Response status: ' + response.status);
                    if (response.ok) {{
                        const html = await response.text();
                        document.getElementById('chat-messages').innerHTML = html;
                        debugLog('Answer submitted successfully');
                    }} else {{
                        debugLog('Error submitting answer: ' + response.statusText);
                    }}
                }} catch (error) {{
                    debugLog('Error: ' + error.message);
                }}
            }}

            // Global function to skip question
            async function skipQuestion(questionId) {{
                debugLog('Skip button clicked for question ' + questionId);
                try {{
                    const token = await firebase.auth().currentUser.getIdToken();
                    const response = await fetch(`/skip-question/${{questionId}}`, {{
                        method: 'POST',
                        headers: {{
                            'Authorization': `Bearer ${{token}}`
                        }}
                    }});

                    if (response.ok) {{
                        const html = await response.text();
                        document.getElementById('chat-messages').innerHTML = html;
                        debugLog('Question skipped successfully');
                    }}
                }} catch (error) {{
                    debugLog('Error: ' + error.message);
                }}
            }}

            firebase.auth().onAuthStateChanged(async function(user) {{
                if (user) {{
                    debugLog('User authenticated: ' + user.email);
                    document.getElementById('user-email').textContent = user.email;
                    
                    try {{
                        const token = await user.getIdToken();
                        debugLog('Got auth token');
                        
                        const response = await fetch('/next-question', {{
                            headers: {{
                                'Authorization': 'Bearer ' + token
                            }}
                        }});
                        
                        if (response.ok) {{
                            const html = await response.text();
                            document.getElementById('chat-messages').innerHTML = html;
                            debugLog('Loaded first question');
                        }}
                    }} catch (error) {{
                        debugLog('Error: ' + error.message);
                    }}
                }} else {{
                    window.location.href = '/';
                }}
            }});

            function signOut() {{
                debugLog('Signing out...');
                firebase.auth().signOut().then(() => {{
                    window.location.href = '/';
                }});
            }}
        </script>
    </body>
    </html>
    """

@router.post("/test-htmx", response_class=HTMLResponse)
async def test_htmx():
    return """
    <div class="test-box" style="border-color: green;">
        <p>HTMX is working! The box changed color and this is new content.</p>
        <button hx-post="/test-htmx" 
                hx-target="#htmx-test">
            Click Again
        </button>
    </div>
    """

@router.get("/next-question", response_class=HTMLResponse)
async def next_question(user=Depends(get_current_user)):
    return """
        <div class="question">
            <h3>Question 1</h3>
            <p>Describe a time when you identified a problem or opportunity that others hadn't noticed yet. 
               What actions did you take without being asked?</p>
            <div class="guidance">
                <strong>Guidance:</strong> Look for examples that demonstrate proactive problem identification 
                and autonomous action. Strong answers show foresight, self-motivation, and willingness to go 
                beyond defined responsibilities.
            </div>
            <div>
                <textarea name="answer" 
                          placeholder="Type your answer here..."
                          required></textarea>
                <div class="button-group">
                    <button onclick="submitAnswer(1)">Submit Answer</button>
                    <button onclick="skipQuestion(1)">Skip for now</button>
                </div>
            </div>
        </div>
    """

@router.post("/submit-answer/{question_id}", response_class=HTMLResponse)
async def submit_answer(
    question_id: int, 
    answer: str = Form(...),  # This captures the form data
    user=Depends(get_current_user)
):
    print(f"Received answer for question {question_id} from user {user['uid']}: {answer}")  # Debug print
    
    # TODO: Save the answer to userID-answers.json
    # For now, just return the next question
    return """
        <div class="question">
            <h3>Question 2</h3>
            <p>Tell me about a situation where you implemented a significant improvement to a process or system on your own initiative. 
               What was your approach and what results did you achieve?</p>
            <div class="guidance">
                <strong>Guidance:</strong> Evaluate whether the candidate can identify inefficiencies, 
                develop solutions independently, and drive implementation. Strong answers include measurable 
                outcomes and demonstrate persistence through challenges.
            </div>
            <form hx-post="/submit-answer/2" hx-target="#chat-messages">
                <textarea name="answer" 
                          placeholder="Type your answer here..."
                          required></textarea>
                <div class="button-group">
                    <button type="submit" class="submit-btn">Submit Answer</button>
                    <button type="button" 
                            class="skip-btn"
                            hx-post="/skip-question/2"
                            hx-target="#chat-messages">
                        Skip for now
                    </button>
                </div>
            </form>
        </div>
    """

@router.post("/skip-question/{question_id}", response_class=HTMLResponse)
async def skip_question(question_id: int, user=Depends(get_current_user)):
    print(f"User {user['uid']} skipped question {question_id}")  # Debug print
    
    # TODO: Mark question as skipped in userID-answers.json
    # For now, just return the next question
    return """
        <div class="question">
            <h3>Question 2</h3>
            <p>Tell me about a situation where you implemented a significant improvement to a process or system on your own initiative. 
               What was your approach and what results did you achieve?</p>
            <div class="guidance">
                <strong>Guidance:</strong> Evaluate whether the candidate can identify inefficiencies, 
                develop solutions independently, and drive implementation. Strong answers include measurable 
                outcomes and demonstrate persistence through challenges.
            </div>
            <form hx-post="/submit-answer/2" hx-target="#chat-messages">
                <textarea name="answer" 
                          placeholder="Type your answer here..."
                          required></textarea>
                <div class="button-group">
                    <button type="submit" class="submit-btn">Submit Answer</button>
                    <button type="button" 
                            class="skip-btn"
                            hx-post="/skip-question/2"
                            hx-target="#chat-messages">
                        Skip for now
                    </button>
                </div>
            </form>
        </div>
    """ 