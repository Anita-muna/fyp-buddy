import sqlite3
conn = sqlite3.connect('instance/fyp_buddy.db')
conn.execute("DELETE FROM interaction WHERE content LIKE '%markdown formatted response%'")
conn.commit()
print('Done')
conn.close()
