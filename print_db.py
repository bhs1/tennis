import shelve
with shelve.open('notified_db') as db:
    for key, value in db.items():
        print(f"Key: {key}, Value: {value}")
