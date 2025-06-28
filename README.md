Event Scheduler System
A simple Python Flask application to manage your events. It supports creating, viewing, updating, and deleting events. Events are saved locally, and you get real-time reminders for upcoming events.

Features
Event Management: Add, view, update, and delete events.

Data Saved: Events save to events.json.

Reminders: Get console reminders for events starting within the next hour.

Setup
Follow these steps to get started:

Project Folder: Create a folder named EventSchedulerSystem. Put your app.py file inside it.

mkdir EventSchedulerSystem
cd EventSchedulerSystem
# Place your app.py here

Virtual Environment: Create a Python virtual environment.

python -m venv venv

Activate Environment:

macOS/Linux: source venv/bin/activate

Windows (Command Prompt): .\venv\Scripts\activate

Windows (PowerShell): .\venv\Scripts\Activate.ps1

Install Libraries: Install Flask and Flask-APScheduler.

pip install Flask Flask-APScheduler

Running the Application
Activate your virtual environment.

Run:

python app.py

Your API will run on http://127.0.0.1:5000. Keep the terminal open for reminders.

API Endpoints
The API uses JSON data. Times must be in YYYY-MM-DDTHH:MM:SS format.

GET /: Checks if the API is running.

POST /events: Creates a new event.

GET /events: Lists all events.

PUT /events/<event_id>: Updates an event.

DELETE /events/<event_id>: Deletes an event.

Testing with Postman
Collection URL: https://www.postman.com/material-architect-44568090/event-handling-project/collection/zok11o0/event-scheduler-system
Use Postman. First, create an event (POST) to get its unique id. Then use this id for PUT (update) and DELETE actions. Use GET /events to see all events.

Testing Real-time Reminders
Run your Flask app.

Create an event using POST /events. Set its start time a few minutes in the future (within 60 minutes).

Wait: Watch your terminal.

Expect: A "REMINDER!" message should print in your terminal. It will only print once per event.
