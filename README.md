# Smart Weighbridge v1

A simple first version of the remote weighbridge web app.

Features:
- Login
- Mobile-friendly operator page
- Camera/photo upload
- Plate number
- Weight entry
- Automatic ticket number
- SQLite database
- Records/history
- Record details
- Basic print-friendly ticket
- ESP32-ready endpoint for current weight

## Run on Windows

1. Install Python 3.11+.
2. Open Command Prompt in this folder.
3. Create a virtual environment:
   python -m venv .venv
4. Activate:
   .venv\Scripts\activate
5. Install:
   pip install -r requirements.txt
6. Set credentials (optional but recommended):
   set SWB_USERNAME=admin
   set SWB_PASSWORD=CHANGE_THIS_PASSWORD
   set SWB_SECRET=CHANGE_THIS_LONG_RANDOM_SECRET
   set SWB_DEVICE_TOKEN=CHANGE_THIS_DEVICE_TOKEN
7. Start:
   uvicorn app.main:app --reload
8. Open:
   http://127.0.0.1:8000

Default credentials if environment variables are not set:
username: admin
password: admin123

This is a development MVP. Before exposing it to the public Internet, use HTTPS,
strong credentials, a production database, proper reverse proxy/security, backups,
and restricted API access.
