import psycopg2
import os
from telegram import Update

PG_DATABASE = os.environ["PG_DATABASE"]
PG_HOST = os.environ["PG_HOST"]
PG_PORT = os.environ["PG_PORT"]
PG_USER = os.environ["PG_USER"]
PG_PASSWORD = os.environ["PG_PASSWORD"]

print("[persistence] Connecting to database...")
db = psycopg2.connect(
  database=PG_DATABASE,
  host=PG_HOST,
  port=PG_PORT,
  user=PG_USER,
  password=PG_PASSWORD
)
cur = db.cursor()

sessions = {}

class Session:
  def __init__(self, chatid, request_departures=False, request_arrivals=False):
    self.chatid = str(chatid)
    self.requested_departures = request_departures
    self.requested_arrivals = request_arrivals

  def reset_selections(self):
    self.requested_departures = False
    self.requested_arrivals = False

  def request_departures(self):
    self.reset_selections()
    self.requested_departures = True
    self.save()

  def request_arrivals(self):
    self.reset_selections()
    self.requested_arrivals = True
    self.save()

  def save(self):
    cur.execute("INSERT INTO sessions (chatid, requested_departures, requested_arrivals) VALUES (%s, %s, %s) ON CONFLICT (chatid) DO UPDATE SET requested_departures = %s, requested_arrivals = %s", (self.chatid, 1 if self.requested_departures else 0, 1 if self.requested_arrivals else 0, 1 if self.requested_departures else 0, 1 if self.requested_arrivals else 0))
    db.commit()

print("[persistence] Dropping table (remove in production)...")
cur.execute("DROP TABLE IF EXISTS sessions")

print("[persistence] Initializing database...")
cur.execute("CREATE TABLE IF NOT EXISTS sessions (chatid TEXT NOT NULL PRIMARY KEY, requested_departures INTEGER NOT NULL DEFAULT 0, requested_arrivals INTEGER NOT NULL DEFAULT 0)")
db.commit()

def retrieve_session(chatid):
  cur.execute("SELECT * FROM sessions WHERE chatid = %s", (str(chatid),))
  s = cur.fetchone()
  if not s:
    return None
  return Session(chatid, s[1] == 1, s[2] == 1)

def get_session(chatid):
  if chatid not in sessions:
    sessions[chatid] = retrieve_session(chatid)
  if not sessions[chatid]:
    sessions[chatid] = Session(chatid)
  return sessions[chatid]