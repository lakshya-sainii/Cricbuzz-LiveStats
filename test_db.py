from database.connection import get_connection

try:
    conn = get_connection()
    print("Database Connection Successful ✅")
    conn.close()

except Exception as error:
    print("Database Connection Failed ❌")
    print(error)