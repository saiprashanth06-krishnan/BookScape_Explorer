import streamlit as st
import pymysql
import pandas as pd
import altair as alt

# MySQL Database Connection
def get_db_connection():
    return pymysql.connect(
        host="localhost",    # Replace with your MySQL host
        user="root",         # Replace with your MySQL username
        password="", # Replace with your MySQL password
        database="books_db"  # Replace with your database name
    )

# Function to execute a query and return the result as a DataFrame
def execute_query(query):
    connection = get_db_connection()
    try:
        df = pd.read_sql(query, connection)
    finally:
        connection.close()
    return df

# List of Queries
queries = {
    "Identify the Publisher with the Highest Average Rating":
        "SELECT publisher FROM books WHERE averageRating=5.00;",
    "Find the Publisher with the Most Books Published":
        "SELECT publisher, COUNT(book_title) AS total_book_counts FROM books GROUP BY publisher ORDER BY COUNT(book_title) DESC;",
    "Get the Top 5 Most Expensive Books by Retail Price":
        "SELECT book_title, amount_retailPrice AS most_expensive_retailbooks FROM books ORDER BY amount_retailPrice DESC LIMIT 5;",
    "Find Books Published After 2010 with at Least 500 Pages":
        "SELECT book_title FROM books WHERE year > 2010 AND pageCount > 500;",
    "List Books with Discounts Greater than 20%":
        """
        SELECT book_title, 
               ((amount_listPrice - amount_retailPrice) / amount_listPrice) * 100 AS discount_percentage 
        FROM books 
        WHERE ((amount_listPrice - amount_retailPrice) / amount_listPrice) * 100 > 20;
        """,
    "Find the Average Page Count for eBooks vs Physical Books":
        """
        SELECT CASE WHEN isEbook = 1 THEN 'eBook' ELSE 'Physical' END AS book_type, 
               AVG(pageCount) AS average_page_count 
        FROM books 
        WHERE pageCount IS NOT NULL 
        GROUP BY isEbook;
        """,
    "Check Availability of eBooks vs Physical Books":
        """
        SELECT CASE WHEN isEbook = 1 THEN 'eBook' ELSE 'Physical' END AS book_type, 
               COUNT(*) AS book_count 
        FROM books 
        GROUP BY isEbook;
        """,
    "Find the Top 3 Authors with the Most Books":
        "SELECT book_authors, COUNT(*) AS book_count FROM books GROUP BY book_authors ORDER BY book_count DESC LIMIT 3;",
    "List Publishers with More than 10 Books":
        "SELECT publisher, COUNT(*) AS book_count FROM books GROUP BY publisher HAVING COUNT(*) > 10;",
    "Find the Average Page Count for Each Category":
        "SELECT categories, AVG(pageCount) AS average_page_count FROM books GROUP BY categories;",
    "Retrieve Books with More than 3 Authors":
        """
        SELECT book_title, book_authors 
        FROM books 
        WHERE LENGTH(book_authors) - LENGTH(REPLACE(book_authors, ',', '')) + 1 > 3;
        """,
    "Books with Ratings Count Greater Than the Average":
        """
        SELECT book_title, ratingsCount 
        FROM books 
        WHERE ratingsCount > (SELECT AVG(ratingsCount) FROM books);
        """,
    "Books with the Same Author Published in the Same Year":
        """
        SELECT b1.book_title, b1.book_authors, b1.year
        FROM books b1
        JOIN (
            SELECT book_authors, year
            FROM books
            GROUP BY book_authors, year
            HAVING COUNT(*) > 1
        ) b2
        ON b1.book_authors = b2.book_authors AND b1.year = b2.year;
        """,
    "Books with a Specific Keyword in the Title":
        "SELECT book_title FROM books WHERE book_title LIKE '%keyword%';",
    "Year with the Highest Average Book Price":
        """
        SELECT year, AVG(amount_listPrice) AS average_price 
        FROM books 
        GROUP BY year 
        ORDER BY average_price DESC 
        LIMIT 1;
        """,
    "Count Authors Who Published 3 Consecutive Years":
        """
        SELECT book_authors, COUNT(DISTINCT year) AS consecutive_years 
        FROM books 
        GROUP BY book_authors 
        HAVING COUNT(DISTINCT year) = 3;
        """,
    "Authors with Books Published in the Same Year Under Different Publishers":
        """
        SELECT book_authors, year, COUNT(*) AS book_count 
        FROM books 
        GROUP BY book_authors, year 
        HAVING COUNT(DISTINCT publisher) > 1;
        """,
    "Average Retail Price of eBooks and Physical Books":
        """
        SELECT 
            AVG(CASE WHEN isEbook = 1 THEN amount_retailPrice ELSE NULL END) AS avg_ebook_price,
            AVG(CASE WHEN isEbook = 0 THEN amount_retailPrice ELSE NULL END) AS avg_physical_price 
        FROM books;
        """,
    "Books with Ratings More Than Two Standard Deviations Away":
        """
        SELECT book_title, averageRating, ratingsCount 
        FROM books 
        WHERE ABS(averageRating - (SELECT AVG(averageRating) FROM books)) > 
              (2 * (SELECT STDDEV(averageRating) FROM books));
        """,
    "Publisher with Highest Average Rating (More Than 10 Books)":
        """
        SELECT publisher, AVG(averageRating) AS average_rating, COUNT(*) AS number_of_books 
        FROM books 
        GROUP BY publisher 
        HAVING COUNT(*) > 10 
        ORDER BY average_rating DESC 
        LIMIT 1;
        """
}

# Streamlit App
st.title("Bookstore Data Analysis and Visualization")

st.sidebar.header("Please find the below 20 Queries")
selected_query = st.sidebar.selectbox("Select a query to run", list(queries.keys()))

if selected_query:
    st.subheader(selected_query)
    query = queries[selected_query]
    try:
        # Execute the query
        result = execute_query(query)

        # Display the raw data
        st.write("Query Result:")
        st.dataframe(result)

        # Visualization based on the query result
        if result.shape[1] == 2:  # Two columns: suitable for bar chart
            col1, col2 = result.columns
            chart = alt.Chart(result).mark_bar().encode(
                x=col1,
                y=col2,
                tooltip=[col1, col2]
            ).interactive()
            st.altair_chart(chart, use_container_width=True)

        elif result.shape[1] == 3:  # Three columns: suitable for grouped bar or line chart
            col1, col2, col3 = result.columns
            chart = alt.Chart(result).mark_bar().encode(
                x=col1,
                y=col3,
                color=col2,
                tooltip=[col1, col2, col3]
            ).interactive()
            st.altair_chart(chart, use_container_width=True)

        else:
            st.write("Visualization is not applicable for this query.")

    except Exception as e:
        st.error(f"Error executing query: {e}")
