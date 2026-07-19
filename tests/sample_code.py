import os

password = "admin123"

user = input("Enter username: ")

query = "SELECT * FROM users WHERE username='" + user + "'"

cursor.execute(query)

result = eval(user)

exec("print('Hello')")

os.system(user)