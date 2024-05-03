# Check ISBN all-time constraint
def check_isbn(cur, user_id, isbn):
    query = """SELECT e.ISBN
                FROM Books b
                JOIN Edition e ON b.bookID = e.bookID
                JOIN Resources r ON b.bookID = r.bookID
                JOIN Borrowing bor ON r.physicalID = bor.physicalID
                WHERE bor.userID = %s AND e.isbn = %s"""
    cur.execute(query, (user_id, isbn))
    rows = cur.fetchall()

    if len(rows) >= 6:
        print(f"You cant borrow any more books with this ISBN {rows[0]}")
        return False
    return True


# Checks the nr of borrowed books a specific user has
def check_nr_of_borrowed_books(cur, user_id):
    # Check all non returned books
    query = "SELECT borrowingID FROM borrowing WHERE userID = %s AND dor IS NULL"
    cur.execute(query, (user_id,))
    rows = cur.fetchall()

    if len(rows) >= 4:
        print("You cant borrow any more books!")
        return False

    return True


# Checks if a user has a fine that is not paid
def check_fine(cur, user_id):
    query = """SELECT Fines.borrowingID
                FROM Fines
                JOIN Borrowing ON Fines.borrowingID = Borrowing.borrowingID
                WHERE Fines.Amount > 0 AND Borrowing.userID = %s"""
    cur.execute(query, (user_id,))
    rows = cur.fetchall()

    if len(rows) > 0:
        # Display one fines (implement more)
        print("You cant borrow a book when you have a these unpaid fines: ")
        print("\nBorrowing IDs With Fines")
        for fine in rows:
            print(f"{fine[0]}")
        return False
    return True
