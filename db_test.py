import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",        # Your MySQL username
        password="your_password", # Your ACTUAL MySQL password
        database="GestureSystem"
    )
    if conn.is_connected():
        print("Successfully connected to the database!")
    conn.close()
except Exception as e:
    print(f"Connection failed: {e}")