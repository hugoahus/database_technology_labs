import psycopg2

from tabulate import tabulate
from datetime import datetime, timedelta
from constraints import *

"""
Note: It's essential never to include database credentials in code pushed to GitHub. 
Instead, sensitive information should be stored securely and accessed through environment variables or similar. 
However, in this particular exercise, we are allowing it for simplicity, as the focus is on a different aspect.
Remember to follow best practices for secure coding in production environments.
"""

# Acquire a connection to the database by specifying the credentials.
conn = psycopg2.connect(
    host="psql-dd1368-ht23.sys.kth.se",
    database="hugolw",
    user="hugolw",
    password="6bNhTn1M",
)
print(conn)

# Create a cursor. The cursor allows you to execute database queries.
cur = conn.cursor()


# Simple function to get all books with a specific genre.
# def get_book_title_by_genre():
#   genre = input("Please enter a genre: ")
#   query = "SELECT books.title FROM books LEFT JOIN genre ON books.bookid = genre.bookid WHERE genre.genre = %s"
#   cur.execute(query, (genre,))
#   result = cur.fetchall()
#   titles = [row[0] for row in result]

#   print(titles)


# Function that retrieves all physical books given a title
def get_physical_books_by_title():
    title = input("Please enter a book title: ")
    query = "SELECT books.bookid, books.title, books.pages, resources.physicalid, resources.damaged FROM books LEFT JOIN resources ON books.bookid = resources.bookid WHERE books.title = %s AND resources.physicalid IS NOT NULL"
    cur.execute(query, (title,))

    # Fetch all rows from the result set
    rows = cur.fetchall()
    table = rows
    headers = ["Book ID", "Title", "# Pages", "Physical ID", "Damaged"]

    # Print the result using the tabulate library, formatted as a PostgreSQL table
    print(
        tabulate(
            table,
            headers=headers,
            tablefmt="psql",
        )
    )


# Show a list of titles and how many physical copies are available (i.e. all copies
# that are not borrowed
def show_number_of_available_books():
    query = """SELECT b.title, COALESCE(COUNT(DISTINCT CASE WHEN (br.DoB IS NULL OR (br.DoB = sub.max_borrow_date AND br.DoR IS NOT NULL)) THEN r.physicalID END), 0) as available_copies
                FROM Books b
                LEFT JOIN Resources r ON b.bookID = r.bookID
                LEFT JOIN Borrowing br ON r.physicalID = br.physicalID
                LEFT JOIN (
                    SELECT physicalID, MAX(dob) as max_borrow_date
                    FROM Borrowing
                    GROUP BY physicalID
                ) sub ON r.physicalID = sub.physicalID
                GROUP BY b.title
                ORDER BY b.title"""
    cur.execute(query)

    # Fetch all rows from the result set
    rows = cur.fetchall()
    table = rows
    headers = ["Title", "# Available Copies"]

    # Print the result
    print(
        tabulate(
            table,
            headers=headers,
            tablefmt="psql",
        )
    )


# Generates an incremented borrowing id
def generate_borrowing_id():
    query = """SELECT borrowingID FROM borrowing"""
    cur.execute(query)
    rows = cur.fetchall()

    # Retrieve the largest borrowing id value (max), incremented by 1
    max_borrowing_id = max(rows, key=lambda x: x[0])[0]

    return max_borrowing_id + 1


# Insert a borrowing of a book
def insert_borrowing(borrowing_id, physical_id, user_id):
    if physical_id is None:
        print("A physical copy does not exist")
        return 

    # Get the current date and time
    current_date_time = datetime.now()

    dob = current_date_time.date()
    doe = dob + timedelta(days=7)

    # Prepare the data for insertion
    data = (borrowing_id, physical_id, user_id, dob, None, doe)

    query = """ INSERT INTO Borrowing(BorrowingID,physicalID,userID,DoB,DoR,DoE) 
                VALUES(%s, %s, %s, %s, %s, %s)"""
    cur.execute(query, data)

    # Tell the user the return date
    print("You are expected to return the book at this date:", doe)
    # Save permanently in the database
    conn.commit()


# Check availability of a book given an isbn
def check_availability(isbn):
    query = """SELECT r.physicalID
                FROM Books b
                LEFT JOIN Resources r ON b.bookID = r.bookID
                LEFT JOIN Edition e ON b.bookID = e.bookID
                LEFT JOIN (
                    SELECT physicalID, MAX(DoB) AS max_borrow_date
                    FROM Borrowing
                    GROUP BY physicalID
                ) AS latest_borrowings ON r.physicalID = latest_borrowings.physicalID
                LEFT JOIN Borrowing bor ON latest_borrowings.physicalID = bor.physicalID AND latest_borrowings.max_borrow_date = bor.DoB
                WHERE e.isbn = %s AND (bor.DoR IS NOT NULL OR latest_borrowings.physicalID IS NULL) AND r.physicalID IS NOT NULL"""
    cur.execute(query, (isbn,))
    rows = cur.fetchall()

    # Check length of created table
    if len(rows) < 1:
        return []
    return rows


# Check if a user is a student
def is_student(user_id):
    query = """SELECT userID FROM students WHERE userID = %s"""
    cur.execute(query, (user_id,))
    rows = cur.fetchall()

    if len(rows) == 0:
        return False
    return True


# Fetch data for insert
def retrieve_values_for_insert(user_id, isbn):
    # Check if physical copies are available
    available_books = check_availability(isbn)

    # If available, insert a borrowing for the first book
    if available_books:
        borrowing_id = generate_borrowing_id()
        physical_id = available_books[0]
        insert_borrowing(borrowing_id, physical_id, user_id)
    else:
        print("The book is not available!")


# Borrow a book using a given email of an existing user in the database.
def borrow_book():
    # Check if the email exists in the users table
    email = input("Please enter email: ")
    cur.execute("SELECT userID FROM users WHERE email = %s", (email,))
    user_id = cur.fetchone()

    if user_id:
        # Check constraints
        # For students
        if is_student(user_id):
            if check_fine(cur, user_id) and check_nr_of_borrowed_books(cur, user_id):
                isbn = input("Please enter the ISBN of the book you want to borrow: ")
                if check_isbn(cur, user_id, isbn):
                    retrieve_values_for_insert(user_id, isbn)

        # For Admins
        else:
            isbn = input("Please enter the ISBN of the book you want to borrow: ")
            retrieve_values_for_insert(user_id, isbn)
    else:
        print("Invalid Email")


# Function displays a text menu
def show_menu():
    print("\n\033[1mLMS\033[0m")
    print("\n1. Show all physical books")
    print("2. Show all books and their available copies")
    print("3. Borrow a book")
    print("4. Quit")


if __name__ == "__main__":
    # Example:
    # # Execute a query which returns all genres including the genre id.
    # cur.execute("SELECT * from genre ")

    # # Print the first row returned.
    # print(cur.fetchone())

    # # Print the next row returned.
    # print(cur.fetchone())

    # # Print all the remaining rows returned.
    # print(cur.fetchall())

    # Switch case
    menu_options = {
        1: get_physical_books_by_title,
        2: show_number_of_available_books,
        3: borrow_book,
    }

    user_option = 1  # Initiate user_option
    while user_option != 4:
        show_menu()
        try:
            user_option = int(input("\nEnter your choice (1-4): "))
            if user_option == 4:
                break
            elif 1 <= user_option <= 3:
                # Call the selected function
                menu_options[user_option]()
            else:
                print("Invalid input. Please enter a number between 1 and 4.")
        except ValueError:
            print("Invalid input. Please enter a number.")

    # Close the connection to the database.
    conn.close()
