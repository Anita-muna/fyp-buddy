from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from groq import Groq
import os
import json
import re

app = Flask(__name__)

uri = os.environ.get('DATABASE_URL', 'sqlite:///fyp_buddy.db')
if uri.startswith('postgres://'):
    uri = uri.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'anita')

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'

groq_client = Groq(api_key=os.environ.get('GROQ_API_KEY'))

CHAPTER_STRUCTURE = """
Preliminary Pages (before Chapter 1):
  - Cover Page
  - Title Page
  - Certification
  - Acknowledgements
  - Abstract
  - Table of Contents
  - List of Tables
  - List of Figures

CHAPTER ONE: INTRODUCTION
  1.1  Background of the Study
  1.2  Statement of the Problem
  1.3  Aim and Objectives of the Study
  1.4  Significance of the Study
  1.5  Scope of the Study
  1.6  Limitations of the Study
  1.7  Definition of Terms

CHAPTER TWO: LITERATURE REVIEW
  2.1  Theoretical Review
  2.2  Review of Related Works
  2.3  Summary of Literature Review and Research Gaps

CHAPTER THREE: METHODOLOGY AND SYSTEM ANALYSIS

  (For a Project WITH a Case Study)
  3.1    Methodology Adopted
  3.2    The Organization and Its Environment
  3.3    Organizational Structure of [Name of Case Study Organization]
  3.4    Analysis of the Existing System
  3.4.1  Data Flow of the Existing System
  3.4.2  Weaknesses of the Existing System
  3.5    Analysis of the Proposed System
  3.5.1  Advantages of the Proposed System
  3.6    High Level Model of the Proposed System

  (For a Project WITHOUT a Case Study)
  3.1    Methodology Adopted
  3.2    Analysis of the Existing System
  3.2.1  Data Flow of the Existing System
  3.2.2  Weaknesses of the Existing System
  3.3    Analysis of the Proposed System
  3.3.1  Advantages of the Proposed System
  3.4    High Level Model of the Proposed System

CHAPTER FOUR: DESIGN AND IMPLEMENTATION
  4.1    Objectives of the Design
  4.2    Control Centre / Main Menu
  4.3    Submenus / Subsystems
  4.4    System Specification
  4.4.1  Development Tool
  4.4.2  Database Design and Structure
  4.4.3  Mathematical Specification (if any)
  4.4.4  Program Module Specification (if any)
  4.4.5  Input / Output Format
  4.4.6  Algorithm
  4.4.7  Data Dictionary
  4.5    System Flowchart (if any)
  4.6    Object Diagram (if any)
  4.7    System Implementation
  4.7.1  Proposed System Requirements
  4.7.1.1  Hardware Requirements
  4.7.1.2  Software Requirements
  4.7.2  Program Development
  4.7.2.1  Choice of Programming Language
  4.7.3  System Testing
  4.7.3.1  Test Plan
  4.7.3.2  Test Data
  4.7.3.3  Actual Test Results Versus Expected Test Results
  4.7.3.4  Performance Evaluation
  4.7.4  System Security
  4.7.4.1  Password Protection (if any)
  4.7.4.2  Authentication (if any)
  4.7.4.3  Digital Signature (if any)
  4.7.5  Results and Discussions

CHAPTER FIVE: SUMMARY, CONCLUSION AND RECOMMENDATION
  5.1    Summary
  5.2    Conclusion
  5.3    Recommendation
  5.3.1  Application Areas
  5.3.2  Suggestion for Further Research
  5.3.3  Contribution to Knowledge

Back Matter:
  - References
  - Appendix A: Program Listing
  - Appendix B: Sample Output
"""

def build_system_prompt(student):
    if student.project_topic:
        topic_line = f"Project Topic: {student.project_topic}"
    else:
        topic_line = "Project Topic: Not yet decided — see behaviour instructions below."

    chapters = ChapterProgress.query.filter_by(student_id=student.id).all()
    chapter_status = '\n'.join([f"  - {c.chapter_label}: {c.status}" for c in chapters])

    return f"""You are FYP Buddy, an intelligent academic assistant and friendly companion for undergraduate Computing students at Nnamdi Azikiwe University (UNIZIK), Awka, Nigeria. Your primary purpose is to help students complete their final year projects (FYP), but you are also happy to have normal, friendly conversations about anything — just like a knowledgeable friend would.


STUDENT CONTEXT:
- Name: {student.fullname}
- {topic_line}

CURRENT CHAPTER PROGRESS:
{chapter_status}


CHAPTER STRUCTURE KNOWLEDGE:
Use this to guide students on what belongs in each chapter.
{CHAPTER_STRUCTURE}


UNIZIK ACADEMIC CONTEXT:
- Students follow the UNIZIK FYP format as approved by their respective Computing department
- Projects are assessed by a supervisor and an external examiner
- Common project categories: web systems, mobile apps, database systems, AI/ML systems, network systems, security systems, information systems
- Students often struggle with: choosing a unique topic, writing Chapter 2, justifying their methodology, and producing proper diagrams in Chapter 4
- For Chapter 3, the structure depends on whether the project has a case study or not — always ask the student which applies before guiding them through Chapter 3
- If a student mentions what their supervisor told them, respect that instruction even if it differs from general guidance


STRUGGLE TYPE DEFINITIONS:
- conceptual — student does not understand a concept, term, or idea
- structural — student is confused about what goes where or how to organise their work
- technical — student has a coding, tool, diagram, or implementation problem
- motivational — student is stressed, discouraged, stuck, or overwhelmed
- none — general conversation, greetings, casual chat, or anything unrelated to the FYP


HOW TO RESPOND BASED ON STRUGGLE TYPE:
- conceptual — explain clearly with a simple definition, then give a concrete example tied to their project topic
- structural — tell them exactly what the section needs, give a brief outline or checklist, ask what they have so far
- technical — diagnose step by step; ask clarifying questions if needed before giving a solution
- motivational — acknowledge their feelings first before any academic content; be warm and human; break the problem into one small next step
- none — respond naturally, warmly, and conversationally; do not force the topic back to their FYP


YOUR BEHAVIOUR:
1. Happy to chat about anything — be natural, warm, personable
2. If student has no topic and brings up their FYP — helping them choose a topic is first priority
3. Guide by default; write drafts only when explicitly asked
4. After every substantive FYP response, suggest one clear actionable next step
5. Always honour supervisor instructions
6. Set chapter_update "in_progress" when student begins discussing a chapter; "completed" only when student explicitly says they finished
7. Use markdown in replies


PROGRESSION GUIDANCE:
Step 1 — No topic → help choose one
Step 2 — Has topic, all chapters not_started → begin Chapter 1, section 1.1
Step 3 — Chapter 1 in_progress → walk through sections 1.1 to 1.7
Step 4 — Chapter 1 done → guide Chapter 2, start with 2.1
Step 5 — Chapter 2 done → ask about case study before guiding Chapter 3
Step 6 — Chapter 3 done → guide Chapter 4, start with 4.1
Step 7 — Chapter 4 done → guide Chapter 5
Step 8 — All done → remind about preliminary pages and back matter


RESPONSE FORMAT — CRITICAL:
Always respond with valid JSON only. No markdown fences, no text before or after. Do NOT wrap your response in markdown code fences. Return raw JSON only, no backtick blocks.

{{
  "reply": "markdown formatted response",
  "struggle_type": "conceptual|motivational|structural|technical|none",
  "chat_title": "only on the very first message of a conversation — a short 4-6 word title summarising what this chat is about",
  "confirmed_topic": "only if topic confirmed this turn",
  "chapter_update": {{
    "chapter_key": "chapter_1",
    "new_status": "in_progress|completed"
  }}
}}

Omit confirmed_topic if no topic confirmed.
Omit chapter_update if no status changed.
Omit chat_title on every message except the very first one in a new conversation."""


# MODELS

class Student(db.Model, UserMixin):
    id            = db.Column(db.Integer, primary_key=True)
    fullname      = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password      = db.Column(db.String(256), nullable=False)
    project_topic = db.Column(db.Text)
    chapters      = db.relationship('ChapterProgress', backref='student', lazy=True)
    interactions  = db.relationship('Interaction', backref='student', lazy=True)
    conversations = db.relationship('Conversation', backref='student', lazy=True)


class Conversation(db.Model):
    id           = db.Column(db.Integer, primary_key=True)
    student_id   = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    title        = db.Column(db.String(200), default='New chat')
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    interactions = db.relationship('Interaction', backref='conversation', lazy=True,
                                   cascade='all, delete-orphan')


class ChapterProgress(db.Model):
    id            = db.Column(db.Integer, primary_key=True)
    student_id    = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    chapter_key   = db.Column(db.String(50))
    chapter_label = db.Column(db.String(120))
    status        = db.Column(db.String(30), default='not_started')
    updated_at    = db.Column(db.DateTime, default=datetime.utcnow)


class Interaction(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    student_id      = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversation.id'), nullable=False)
    role            = db.Column(db.String(10))
    content         = db.Column(db.Text, nullable=False)
    timestamp       = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()


# HELPERS

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Student, int(user_id))


def get_or_create_conversation():
    """Return the active conversation for the current user, creating one if needed."""
    conv_id = session.get('conversation_id')
    if conv_id:
        conv = db.session.get(Conversation, conv_id)
        if conv and conv.student_id == current_user.id:
            return conv
    conv = Conversation(student_id=current_user.id, title='New chat')
    db.session.add(conv)
    db.session.commit()
    session['conversation_id'] = conv.id
    return conv


# AUTH ROUTES

@app.route('/')
@app.route('/signup', methods=['GET', 'POST'])
def signup_page():
    if request.method == 'POST':
        fullname         = request.form.get('fullname')
        email            = request.form.get('email')
        password         = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        project_topic    = request.form.get('project_topic')

        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('signup_page'))

        existing_user = Student.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered!', 'danger')
            return redirect(url_for('signup_page'))

        hashed_password = generate_password_hash(password)
        new_student = Student( fullname=fullname, email=email, password=hashed_password,
                               project_topic=project_topic if project_topic else None )
        db.session.add(new_student)
        db.session.flush()

        chapters = [
            ('chapter_1', 'Chapter 1 - Introduction'),
            ('chapter_2', 'Chapter 2 - Literature Review'),
            ('chapter_3', 'Chapter 3 - Methodology and System Analysis'),
            ('chapter_4', 'Chapter 4 - Design and Implementation'),
            ('chapter_5', 'Chapter 5 - Summary, Conclusion and Recommendation'),
        ]
        for key, label in chapters:
            chapter = ChapterProgress(
                student_id    = new_student.id,
                chapter_key   = key,
                chapter_label = label,
                status        = 'not_started'
            )
            db.session.add(chapter)

        db.session.commit()
        login_user(new_student)
        flash('Account created successfully!', 'success')
        return redirect(url_for('chat_page'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        email    = request.form.get('email')
        password = request.form.get('password')
        student  = Student.query.filter_by(email=email).first()
        if student and check_password_hash(student.password, password):
            login_user(student)
            return redirect(url_for('chat_page'))
        else:
            flash('Incorrect email or password!', 'danger')
            return redirect(url_for('login_page'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    session.pop('conversation_id', None)
    logout_user()
    return redirect(url_for('login_page'))


# CONVERSATION ROUTES

@app.route('/new_chat', methods=['POST'])
@login_required
def new_chat():
    conv = Conversation(student_id=current_user.id, title='New chat')
    db.session.add(conv)
    db.session.commit()
    session['conversation_id'] = conv.id
    return jsonify({'ok': True, 'conversation_id': conv.id})


@app.route('/switch_chat/<int:conv_id>', methods=['POST'])
@login_required
def switch_chat(conv_id):
    conv = db.session.get(Conversation, conv_id)
    if not conv or conv.student_id != current_user.id:
        return jsonify({'ok': False}), 403
    session['conversation_id'] = conv_id
    interactions = Interaction.query.filter_by(
        conversation_id=conv_id
    ).order_by(Interaction.timestamp.asc()).all()
    messages = [{'role': i.role, 'content': i.content} for i in interactions]
    return jsonify({'ok': True, 'messages': messages})


@app.route('/delete_chat/<int:conv_id>', methods=['POST'])
@login_required
def delete_chat(conv_id):
    conv = db.session.get(Conversation, conv_id)
    if not conv or conv.student_id != current_user.id:
        return jsonify({'ok': False}), 403
    db.session.delete(conv)
    db.session.commit()
    if session.get('conversation_id') == conv_id:
        session.pop('conversation_id', None)
    return jsonify({'ok': True})


# UTILITY ROUTES

@app.route('/update_topic', methods=['POST'])
@login_required
def update_topic():
    data  = request.get_json()
    topic = data.get('topic', '').strip()
    if not topic:
        return jsonify({'ok': False, 'error': 'Empty topic'}), 400
    current_user.project_topic = topic
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/clear_history', methods=['POST'])
@login_required
def clear_history():
    conv_id = session.get('conversation_id')
    if conv_id:
        Interaction.query.filter_by(
            student_id=current_user.id,
            conversation_id=conv_id
        ).delete()
        db.session.commit()
    return jsonify({'ok': True})


# CHAT ROUTE

@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat_page():
    if request.method == 'GET':
        conv = get_or_create_conversation()
        interactions = Interaction.query.filter_by(
            conversation_id=conv.id
        ).order_by(Interaction.timestamp.asc()).all()

        conversations = Conversation.query.filter_by(
            student_id=current_user.id
        ).order_by(Conversation.created_at.desc()).all()

        return render_template('chat.html',
                               interactions=interactions,
                               student=current_user,
                               conversations=conversations,
                               active_conv_id=conv.id)

    # POST
    data         = request.get_json()
    user_message = data.get('message', '').strip()

    if not user_message:
        return jsonify({'error': 'Empty message'}), 400

    conv = get_or_create_conversation()
    is_first_message = Interaction.query.filter_by(
        conversation_id=conv.id
    ).count() == 0

    db.session.add(Interaction(
        student_id      = current_user.id,
        conversation_id = conv.id,
        role            = 'user',
        content         = user_message
    ))
    db.session.commit()

    recent = Interaction.query.filter_by(conversation_id=conv.id) \
        .order_by(Interaction.timestamp.desc()) \
        .limit(11).all()
    recent = list(reversed(recent))
    history_interactions = recent[:-1]

    messages = [{"role": "system", "content": build_system_prompt(current_user)}]
    for interaction in history_interactions:
        role = "user" if interaction.role == "user" else "assistant"
        messages.append({"role": role, "content": interaction.content})
    messages.append({"role": "user", "content": user_message})

    try:
        response = groq_client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            temperature=0.7,
        )
        raw = response.choices[0].message.content.strip()

        parsed = None
        clean = re.sub(r'^```(?:json)?\s*', '', raw.strip(), flags=re.MULTILINE)
        clean = re.sub(r'```\s*$', '', clean.strip(), flags=re.MULTILINE).strip()
        try:
            parsed = json.loads(clean)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', clean, re.DOTALL)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
        if not parsed:
            parsed = {'reply': raw, 'struggle_type': 'none'}

        reply_text      = parsed.get('reply', 'Sorry, I could not generate a response.')
        struggle_type   = parsed.get('struggle_type', 'none')
        confirmed_topic = parsed.get('confirmed_topic')
        chapter_update  = parsed.get('chapter_update')
        chat_title      = parsed.get('chat_title')

        if is_first_message and chat_title:
            conv.title = chat_title
            db.session.commit()

        if confirmed_topic and not current_user.project_topic:
            current_user.project_topic = confirmed_topic
            db.session.commit()

        if chapter_update:
            chapter_key = chapter_update.get('chapter_key')
            new_status  = chapter_update.get('new_status')
            if chapter_key and new_status:
                chapter = ChapterProgress.query.filter_by(
                    student_id=current_user.id,
                    chapter_key=chapter_key
                ).first()
                if chapter:
                    chapter.status     = new_status
                    chapter.updated_at = datetime.utcnow()
                    db.session.commit()

        db.session.add(Interaction(
            student_id      = current_user.id,
            conversation_id = conv.id,
            role            = 'assistant',
            content         = reply_text
        ))
        db.session.commit()

        return jsonify({
            'reply':           reply_text,
            'struggle_type':   struggle_type,
            'confirmed_topic': confirmed_topic,
            'chapter_update':  chapter_update,
            'chat_title':      chat_title,
            'conversation_id': conv.id,
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
