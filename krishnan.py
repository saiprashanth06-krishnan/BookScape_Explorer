import streamlit as st
import pandas as pd
import requests
import pymysql

# Set Streamlit title
st.title("📚 BookScape Explorer")

# Database connection function
def get_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='books_db',
        cursorclass=pymysql.cursors.DictCursor
    )

# Function to fetch books from Google API
def fetch_books(search_key):
    url = f"https://www.googleapis.com/books/v1/volumes?q={search_key}"
    response = requests.get(url)
    return response.json()

# Function to replace NULL values with 'Not Available'
def clean_value(value):
    return value if value else "Not Available"

# Function to ensure numerical values are stored as 0 if missing
def get_numeric_value(value):
    return value if isinstance(value, (int, float)) else 0  # Convert invalid values to 0

# Function to store books in the database and count the number of books stored
def store_books(books, search_key):
    conn = get_db_connection()
    cursor = conn.cursor()
    stored_count = 0
    
    for book in books.get("items", []):
        book_info = book.get("volumeInfo", {})
        
        book_id = book.get("id", "Not Available")

        # Check if book already exists
        cursor.execute("SELECT book_id FROM books WHERE book_id = %s", (book_id,))
        existing_book = cursor.fetchone()

        if existing_book:
            continue  # Skip this book if already exists

        # Replace NULL values with "Not Available" for text fields
        book_title = book_info.get("title", "Not Available")
        book_subtitle = book_info.get("subtitle", "Not Available")
        book_authors = ", ".join(book_info.get("authors", ["Not Available"]))
        book_description = book_info.get("description", "Not Available")
        industryIdentifiers = str(book_info.get("industryIdentifiers", "Not Available"))
        text_readingModes = book_info.get("readingModes", {}).get("text", "Not Available")
        image_readingModes = book_info.get("readingModes", {}).get("image", "Not Available")
        categories = ", ".join(book_info.get("categories", ["Not Available"]))
        language = book_info.get("language", "Not Available")
        imageLinks = str(book_info.get("imageLinks", "Not Available"))
        country = book_info.get("saleInfo", {}).get("country", "Not Available")
        saleability = book_info.get("saleInfo", {}).get("saleability", "Not Available")
        buyLink = book_info.get("saleInfo", {}).get("buyLink", "Not Available")
        year = book_info.get("publishedDate", "Not Available")
        publisher = book_info.get("publisher", "Not Available")

        # Fill numerical columns with 0 if missing
        pageCount = get_numeric_value(book_info.get("pageCount"))
        ratingsCount = get_numeric_value(book_info.get("ratingsCount"))
        averageRating = get_numeric_value(book_info.get("averageRating"))
        amount_listPrice = get_numeric_value(book_info.get("saleInfo", {}).get("listPrice", {}).get("amount"))
        amount_retailPrice = get_numeric_value(book_info.get("saleInfo", {}).get("retailPrice", {}).get("amount"))

        # Ensure currency code fields are stored correctly
        currencyCode_listPrice = book_info.get("saleInfo", {}).get("listPrice", {}).get("currencyCode", "Not Available")
        currencyCode_retailPrice = book_info.get("saleInfo", {}).get("retailPrice", {}).get("currencyCode", "Not Available")

        # Convert `isEbook` to integer (0 = False, 1 = True)
        isEbook = book_info.get("saleInfo", {}).get("isEbook")
        isEbook = 1 if isEbook is True else 0  # Default to 0 if missing

        # Insert into MySQL
        cursor.execute("""
            INSERT INTO books (book_id, search_key, book_title, book_subtitle, book_authors, book_description,
                              industryIdentifiers, text_readingModes, image_readingModes, pageCount, categories,
                              language, imageLinks, ratingsCount, averageRating, country, saleability, isEbook,
                              amount_listPrice, currencyCode_listPrice, amount_retailPrice, currencyCode_retailPrice,
                              buyLink, year, publisher)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            book_id, search_key, book_title, book_subtitle, book_authors, book_description,
            industryIdentifiers, text_readingModes, image_readingModes, pageCount, categories,
            language, imageLinks, ratingsCount, averageRating, country, saleability, isEbook,
            amount_listPrice, currencyCode_listPrice, amount_retailPrice, currencyCode_retailPrice,
            buyLink, year, publisher
        ))
        
        stored_count += 1

    conn.commit()
    conn.close()
    return stored_count



# Streamlit UI
st.sidebar.header("Search Books")
search_key = st.sidebar.text_input("Enter search key:")
if st.sidebar.button("Search & Store"):
    books = fetch_books(search_key)
    stored_count = store_books(books, search_key)
    st.sidebar.success(f"Books stored successfully! Total books stored: {stored_count}")

# Sidebar for Queries
st.sidebar.header("Query Selection")
queries = {
    "Highest Average Rating Publisher": "SELECT publisher FROM books WHERE averageRating=5.00;",
    "Publisher with Most Books Published": "SELECT publisher, COUNT(book_title) AS total_book_counts FROM books GROUP BY publisher ORDER BY total_book_counts DESC;",
    "Top 5 Most Expensive Books": "SELECT book_title, amount_retailPrice FROM books ORDER BY amount_retailPrice DESC LIMIT 5;",
    "Books After 2010 with at Least 500 Pages": "SELECT book_title FROM books WHERE year > 2010 AND pageCount > 500;",
    "Books with Discounts Greater than 20%": "SELECT book_title, ((amount_listPrice - amount_retailPrice) / amount_listPrice) * 100 AS discount_percentage FROM books WHERE ((amount_listPrice - amount_retailPrice) / amount_listPrice) * 100 > 20;",
    "Average Page Count for eBooks vs Physical Books": "SELECT CASE WHEN isEbook = 1 THEN 'eBook' ELSE 'Physical' END AS book_type, AVG(pageCount) AS average_page_count FROM books WHERE pageCount IS NOT NULL GROUP BY isEbook;",
    "Availability of eBooks vs Physical Books": "SELECT CASE WHEN isEbook = 1 THEN 'eBook' ELSE 'Physical' END AS book_type, COUNT(*) AS book_count FROM books GROUP BY isEbook;",
    "Top 3 Authors with Most Books": "SELECT book_authors, COUNT(*) AS book_count FROM books GROUP BY book_authors ORDER BY book_count DESC LIMIT 3;",
    "Publishers with More than 10 Books": "SELECT publisher, COUNT(*) AS book_count FROM books GROUP BY publisher HAVING COUNT(*) > 10;",
    "Average Page Count for Each Category": "SELECT categories, AVG(pageCount) AS average_page_count FROM books GROUP BY categories;",
    "Books with More than 3 Authors": "SELECT book_title, book_authors FROM books WHERE LENGTH(book_authors) - LENGTH(REPLACE(book_authors, ',', '')) + 1 > 3;",
    "Books with Ratings Count Greater than Average": "SELECT book_title, ratingsCount FROM books WHERE ratingsCount > (SELECT AVG(ratingsCount) FROM books);",
    "Books with the Same Author Published in Same Year": "SELECT book_title, book_authors, year FROM books WHERE (book_authors, year) IN (SELECT book_authors, year FROM books GROUP BY book_authors, year HAVING COUNT(*) > 1);",
    "Books with Specific Keyword in Title": "SELECT book_title FROM books WHERE book_title LIKE '%keyword%';",
    "Year with Highest Average Book Price": "SELECT year, AVG(amount_listPrice) AS average_price FROM books GROUP BY year ORDER BY average_price DESC LIMIT 1;",
    "Authors Published 3 Consecutive Years": "SELECT book_authors FROM books GROUP BY book_authors HAVING COUNT(DISTINCT year) = 3;",
    "Authors with Books Under Different Publishers in Same Year": "SELECT book_authors, year, COUNT(*) AS book_count FROM books GROUP BY book_authors, year HAVING COUNT(DISTINCT publisher) > 1;",
    "Average Price of eBooks vs Physical Books": "SELECT AVG(CASE WHEN isEbook = 1 THEN amount_retailPrice ELSE NULL END) AS avg_ebook_price, AVG(CASE WHEN isEbook = 0 THEN amount_retailPrice ELSE NULL END) AS avg_physical_price FROM books;",
    "To find average rating is more than the standard deviation": "SELECT book_title, averageRating, ratingsCount FROM books WHERE ABS(averageRating - (SELECT AVG(averageRating) FROM books)) > (2 * (SELECT STDDEV(averageRating) FROM books));",
    "Identity which publisher have highest average rating": "SELECT publisher, AVG(averageRating) AS average_rating, COUNT(*) AS number_of_books FROM books GROUP BY publisher HAVING COUNT(*) > 10 ORDER BY average_rating DESC LIMIT 1;"
}

query_selection = st.sidebar.selectbox("Select a query", list(queries.keys()))

if st.sidebar.button("Run Query"):
    conn = get_db_connection()  # ✅ Ensure connection is established here
    cursor = conn.cursor()
    
    try:
        cursor.execute(queries[query_selection])
        df = pd.DataFrame(cursor.fetchall())  # Fetch results and store in DataFrame
        st.write(f"**Results for: {query_selection}**")
        st.dataframe(df)  # Display results
    
    except Exception as e:
        st.error(f"Error running query: {e}")  # Handle errors gracefully

    finally:
        cursor.close()
        conn.close()  # ✅ Ensure connection is closed properly
