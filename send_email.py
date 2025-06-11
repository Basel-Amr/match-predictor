import os
import smtplib
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from db import get_connection
from utils import fetch_all
from controllers.predictions_controllers import format_time_left, get_next_round_info, get_predicted_match_count

# Load environment variables
load_dotenv()

SMTP_SERVER = os.getenv('SMTP_SERVER')
SMTP_PORT = int(os.getenv('SMTP_PORT'))
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')

def get_all_player_emails():
    """Returns a list of all player emails and usernames."""
    query = "SELECT username, email FROM players"
    rows = fetch_all(query)
    return [(row["username"], row["email"]) for row in rows]


def send_reminder_email_to_all(round_name, deadline, match_time, match_count, level):
    """
    Send a customized reminder email based on level.
    Levels: "2days", "1day", "2hours", or "test"
    """
    now = datetime.now()

    if level == "2days":
        subject = f"⏳ Just 2 Days Left – Get Ready for {round_name}!"
        body_template = """
Hi {username} ⚽,

The excitement is building! The round **{round_name}** kicks off soon.

🗓 Match Time: {match_time}
⏰ Deadline to Predict: {deadline} (2 hours before kickoff)
📊 Matches in this Round: {match_count}

You've still got **2 full days** to make your predictions. Don’t miss out – the leaderboard is waiting!

🔥 Show us your football wisdom!
"""
    elif level == "1day":
        subject = f"⏰ Only 1 Day Left to Predict – {round_name} Awaits!"
        body_template = """
Hey {username} ⚽,

Only **1 day left** until the deadline for round **{round_name}**.

🗓 Match Time: {match_time}
⏰ Prediction Deadline: {deadline}
📊 Matches in Round: {match_count}

Your next big move could change the game. Submit your predictions now and stay ahead of the pack!

💪 Let’s make it count!
"""
    elif level == "2hours":
        subject = f"🚨 FINAL CALL, {round_name} Starts Soon!"
        body_template = """
Hi {username},

⏰ Time's almost up! This is your **FINAL REMINDER** to submit predictions for **{round_name}**.

Deadline: {deadline}

⚠️ If you've already predicted – you're awesome. If not, now's your last chance!

🏁 Let's kick off in style!
"""
    elif level.lower() == "test":
        # Dynamically calculate time left
        time_left = deadline - now
        days, seconds = time_left.days, time_left.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60

        subject = f"🛠️ TEST Reminder – {round_name}"
        body_template = f"""
Hello {{username}} 👋,

This is a **TEST EMAIL** to preview reminders for the round **{round_name}**.

📅 Match Time: {match_time.strftime('%Y-%m-%d %H:%M')}
⏰ Deadline: {deadline.strftime('%Y-%m-%d %H:%M')}
⌛ Time Left: {days} days, {hours} hours, and {minutes} minutes
🧮 Matches to Predict: {match_count}

🚀 Reminder system is working perfectly!
"""
    else:
        print("⚠️ Invalid reminder level provided.")
        return

    # Send Emails
    recipients = get_all_player_emails()

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)

            for username, email in recipients:
                formatted_body = body_template.format(
                    username=username,
                    round_name=round_name,
                    match_time=match_time.strftime('%Y-%m-%d %H:%M'),
                    deadline=deadline.strftime('%Y-%m-%d %H:%M'),
                    match_count=match_count
                )

                message = MIMEMultipart()
                message["From"] = SENDER_EMAIL
                message["To"] = email
                message["Subject"] = subject
                message.attach(MIMEText(formatted_body, "plain"))

                server.sendmail(SENDER_EMAIL, email, message.as_string())

        print(f"✅ {level.upper()} reminder sent to {len(recipients)} players.")
    except Exception as e:
        print(f"❌ Failed to send {level.upper()} reminder:", e)



