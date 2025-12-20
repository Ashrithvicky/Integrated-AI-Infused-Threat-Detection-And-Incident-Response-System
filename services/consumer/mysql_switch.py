# mysql_switch.py - example: connect to MySQL and create schema like SQLite
''' import mysql.connector, os
host=os.getenv("MYSQL_HOST","localhost"); user=os.getenv("MYSQL_USER","root"); pw=os.getenv("MYSQL_PASS","")
conn = mysql.connector.connect(host=host, user=user, password=pw)
c=conn.cursor()
c.execute("CREATE DATABASE IF NOT EXISTS threatsys")
c.execute("USE threatsys")
c.execute("""
CREATE TABLE IF NOT EXISTS alerts (
 id VARCHAR(128) PRIMARY KEY,
 entity_id TEXT,
 score DOUBLE,
 event_json LONGTEXT,
 ts DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")
conn.commit()
print("MySQL schema ready")
'''