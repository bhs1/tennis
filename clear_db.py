import shelve

def clear_db():
    with shelve.open('notified_db') as db:
        db.clear()
        print("Database cleared.")

if __name__ == "__main__":
    clear_db()


