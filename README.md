# FYP Buddy

An AI-powered academic assistant that guides undergraduate Computing students through their final year project (FYP), built for students at Nnamdi Azikiwe University (UNIZIK), Awka, Nigeria.

FYP Buddy tracks a student's progress through each project chapter, adapts its guidance to the kind of difficulty the student is having, and keeps a separate history for every conversation.

**Live demo:** [https://fyp-buddy-phot.onrender.com](https://fyp-buddy-phot.onrender.com)

---

## Features

- **Guided FYP support:** helps students choose a topic, then walks them through Chapters 1 to 5 using the UNIZIK project structure (sections, sub-sections, preliminary pages, and back matter).
- **Struggle-aware responses:** each message is categorised as `conceptual`, `structural`, `technical`, `motivational`, or `none`, and the reply style changes to match (for example, a motivational message gets an empathetic reply before any academic content).
- **Chapter progress tracking:** every student has a progress record for each of the five chapters (`not_started`, `in_progress`, `completed`) that updates as the conversation moves forward and feeds back into the assistant's guidance.
- **Multiple conversations:** students can start new chats, switch between them, and delete old ones. Each chat gets an automatically generated short title.
- **Authentication:** signup and login with hashed passwords and session management.
- **Casual chat supported:** the assistant also handles general conversation without forcing the topic back to the project.

## Tech Stack

| Area | Technology |
|---|---|
| Backend | Python, Flask |
| Database | SQLAlchemy ORM with SQLite (local) and PostgreSQL (production) |
| Authentication | Flask-Login, Werkzeug password hashing |
| AI | Groq API (LLM) |
| Deployment | Docker, Render |
| Frontend | HTML, CSS, JavaScript (Jinja2 templates) |

## How It Works

1. A student signs up, optionally entering a project topic. Five chapter-progress records are created for them automatically.
2. When the student sends a message, the app builds a system prompt containing the student's name, project topic, current chapter progress, the UNIZIK chapter structure, and behaviour rules.
3. The recent chat history (last 10 messages) and the new message are sent to the LLM, which is instructed to return structured JSON: the reply, the struggle type, and any topic or chapter-status updates.
4. The app parses the response, updates the student's topic and chapter progress when applicable, saves the messages, and returns the reply to the chat window.

## Data Models

- **Student:** account details, password hash, and project topic. Owns chapters, interactions, and conversations.
- **Conversation:** one chat session, with a title and creation time. Deleting a conversation deletes its messages (`cascade='all, delete-orphan'`).
- **Interaction:** a single message (user or assistant) belonging to a conversation.
- **ChapterProgress:** the status of one chapter for one student.

## Getting Started

### Prerequisites

- Python 3.10 or later
- A [Groq API key](https://console.groq.com/)

### Installation

```bash
# Clone the repository
git clone https://github.com/Anita-muna/fyp-buddy.git
cd fyp-buddy

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# Install dependencies
pip install flask flask-sqlalchemy flask-login groq "psycopg[binary]"
```

### Environment variables

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Your Groq API key (required) |
| `SECRET_KEY` | Secret used to sign sessions. Set a long random value in production. |
| `DATABASE_URL` | Database connection string. Defaults to a local SQLite file if not set. |

Example (macOS/Linux):

```bash
export GROQ_API_KEY="your-key-here"
export SECRET_KEY="a-long-random-string"
```

### Run locally

```bash
python app.py
```

Then open `http://127.0.0.1:5000`. The database tables are created automatically on first run.

## Main Routes

| Route | Method | Description |
|---|---|---|
| `/signup` | GET, POST | Create an account |
| `/login` | GET, POST | Log in |
| `/logout` | GET | Log out |
| `/chat` | GET, POST | Chat page and message endpoint |
| `/new_chat` | POST | Start a new conversation |
| `/switch_chat/<id>` | POST | Load a previous conversation |
| `/delete_chat/<id>` | POST | Delete a conversation |
| `/update_topic` | POST | Update the project topic |
| `/clear_history` | POST | Clear the current conversation's messages |

## Deployment

The app is deployed on Render using Docker with a PostgreSQL database. Set the three environment variables above in the Render dashboard. The app converts `postgres://` and `postgresql://` URLs to the `postgresql+psycopg://` format automatically.

## Limitations and Future Improvements

- Move password hashing into methods on the `Student` model so the logic lives in one place.
- Add automated tests (for example, with pytest) for the routes and models.
- Add rate limiting on the chat endpoint.
- Let students export their chapter progress.

## Author

**Anita Uzoka**
[GitHub](https://github.com/Anita-muna) | [LinkedIn](https://linkedin.com/in/anita-uzoka-a63844323) | princessanitau@gmail.com
