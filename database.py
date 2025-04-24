import sqlite3
from datetime import datetime

def init_db():
    conn = sqlite3.connect('phone_db.sqlite')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS phones
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  phone_number TEXT UNIQUE,
                  owner_name TEXT,
                  expire_date TEXT,
                  notes TEXT)''')
    conn.commit()
    conn.close()

def add_phone(phone_number, owner_name, expire_date, notes=""):
    conn = sqlite3.connect('phone_db.sqlite')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO phones (phone_number, owner_name, expire_date, notes) VALUES (?, ?, ?, ?)",
                  (phone_number, owner_name, expire_date, notes))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Số điện thoại đã tồn tại
    finally:
        conn.close()

def get_all_phones():
    conn = sqlite3.connect('phone_db.sqlite')
    c = conn.cursor()
    c.execute("SELECT * FROM phones")
    phones = c.fetchall()
    conn.close()
    return phones

def get_expiring_phones(days=7):
    conn = sqlite3.connect('phone_db.sqlite')
    c = conn.cursor()
    
    today = datetime.now().strftime('%Y-%m-%d')
    c.execute("SELECT * FROM phones WHERE expire_date BETWEEN ? AND date(?, ?)", 
             (today, today, f"+{days} days"))
    
    phones = c.fetchall()
    conn.close()
    return phones

def delete_phone(phone_number):
    conn = sqlite3.connect('phone_db.sqlite')
    c = conn.cursor()
    c.execute("DELETE FROM phones WHERE phone_number=?", (phone_number,))
    conn.commit()
    conn.close()