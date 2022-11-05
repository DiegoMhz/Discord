import sqlite3
con = sqlite3.connect("bot.db")
cur = con.cursor()
# Creacion de tablas SQL
cur.execute('''
    CREATE TABLE IF NOT EXISTS users (
        discord_id TEXT PRIMARY KEY,
        name TEXT,
        email TEXT,
        password TEXT,
        token TEXT
    )
''')

con.commit()