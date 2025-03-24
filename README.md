# Project Build Steps
1. Complete
   1. `uv init`
   2. Set up `.env` according to `.env.template`
      1. Include link to serviceAccount.json which holds Firebase information
   3. Set up project on Firebase
2. To do
   1. View app in development
   2. Set up Firebase authentication

# Technology stack

### Technology To Use

* Backend Framework
  * **FastAPI**
* Frontend (simple)
  * **HTMX** (use as little JavaScript as possible)
* AI Integration
  * **Model Context Protocol (MCP)**
  * **PydanticAI** (for agent integration and cordination via MCP https://ai.pydantic.dev/mcp/)
  * **Google Gemini** (integrated via the MCP-Gemini connector)
* Dependency Management
  * **UV** (start by running `uv init` and then uv add as well as source `.venv/bin/activate`)
* Hosting & Services
  * **Firebase Hosting**
  * **Firebase Admin SDK for Python**
    * Authentication services for secure user session management
    * Firestore for NoSQL document database operations
    * Cloud Messaging for notifications

### Technologies To Avoid

* **No Frontend Frameworks**
  * No React, Vue, Angular, or Svelte
  * No jQuery or other JavaScript libraries
* **No Template Engines**
  * No Jinja2, Mako, or other template engines
  * Use direct HTML responses from FastAPI
* **No ORM**
  * No SQLAlchemy, Tortoise, or other ORMs
  * Use Firebase SDK directly for data operations
* **No Additional Authentication**
  * No OAuth libraries or custom auth systems
  * Rely solely on Firebase Authentication
* **No CSS Frameworks**
  * No Bootstrap, Tailwind, or other CSS frameworks
  * Use simple, custom CSS


# Run test server
1. Run `uv sync`
2. Activate virtual environment `source .venv/bin/activate`
3. Spin up server `uvicorn main:app --reload`
4. Click supplied link

## questions-1 Prompt

How would you extend this @codebase to leverage PydanticAI and MCP to:
1. Provide a logged in user with a chat window that would prompt the user to answer questions from 36questioins.json file
2. Guide user through answering that question in a satisfacory way
3. Save the user approved answer to a user specific userID-answers.json file
4. Then provide user the next question to answer until all have been answersed

Note:
- Pay attention to the Technology Stack in the README.md file
- Leverage MCP to provide tools, resources (36questions.json), and prompts.
- Feel free to modify 36questions.json to include any metadata to enable the LLM to know which questions have been answered per user