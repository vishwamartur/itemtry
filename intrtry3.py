# Import the required libraries
import streamlit as st
import pandas as pd
import sqlite3
import datetime

# Create a connection to the SQLite database
conn = sqlite3.connect("users.db")
c = conn.cursor()

# Create a table for storing user profiles
c.execute("""CREATE TABLE IF NOT EXISTS users (
    name TEXT,
    email TEXT,
    password TEXT
    )""")

# Create a table for storing reservations
c.execute("""CREATE TABLE IF NOT EXISTS reservations (
    user TEXT,
    item TEXT,
    location TEXT,
    start_date TEXT,
    end_date TEXT
    )""")

# Commit the changes to the database
conn.commit()

# Load the item details from the csv file
items = pd.read_csv("items.csv")

# Define a function to check if an item is available for a given date range
def is_available(item, location, start_date, end_date):
    # Query the reservations table for the item and location
    c.execute("""SELECT * FROM reservations WHERE item = ? AND location = ?""", (item, location))
    # Fetch all the records
    records = c.fetchall()
    # Loop through the records
    for record in records:
        # Parse the start and end dates of the reservation
        record_start = datetime.datetime.strptime(record[3], "%Y-%m-%d")
        record_end = datetime.datetime.strptime(record[4], "%Y-%m-%d")
        # Check if the date range overlaps with the reservation
        if (start_date <= record_end) and (end_date >= record_start):
            # Return False if there is an overlap
            return False
    # Return True if there is no overlap
    return True

# Define a function to reserve an item for a user
def reserve_item(user, item, location, start_date, end_date):
    # Check if the item is available for the date range
    if is_available(item, location, start_date, end_date):
        # Insert the reservation into the table
        c.execute("""INSERT INTO reservations VALUES (?, ?, ?, ?, ?)""", (user, item, location, start_date, end_date))
        # Commit the changes to the database
        conn.commit()
        # Return a success message
        return f"Reservation successful for {user} for {item} at {location} from {start_date} to {end_date}"
    else:
        # Return a failure message
        return f"Reservation failed for {user} for {item} at {location} from {start_date} to {end_date}. The item is already reserved by someone else."

# Define a function to request a reservation for an item that is already reserved
def request_reservation(user, item, location, start_date, end_date):
    # Query the reservations table for the item and location
    c.execute("""SELECT * FROM reservations WHERE item = ? AND location = ?""", (item, location))
    # Fetch all the records
    records = c.fetchall()
    # Loop through the records
    for record in records:
        # Parse the start and end dates of the reservation
        record_start = datetime.datetime.strptime(record[3], "%Y-%m-%d")
        record_end = datetime.datetime.strptime(record[4], "%Y-%m-%d")
        # Check if the date range overlaps with the reservation
        if (start_date <= record_end) and (end_date >= record_start):
            # Get the user who made the reservation
            reserved_by = record[0]
            # Return a message with the option to request the reservation
            return f"The item is already reserved by {reserved_by} from {record_start} to {record_end}. Do you want to request the reservation from them? (Y/N)"

# Define a function to create a user profile
def create_user(name, email, password):
    # Check if the email already exists in the users table
    c.execute("""SELECT * FROM users WHERE email = ?""", (email,))
    # Fetch the record
    record = c.fetchone()
    # If the record is not None, the email is already taken
    if record is not None:
        # Return a failure message
        return f"User creation failed. The email {email} is already taken."
    else:
        # Insert the user into the users table
        c.execute("""INSERT INTO users VALUES (?, ?, ?)""", (name, email, password))
        # Commit the changes to the database
        conn.commit()
        # Return a success message
        return f"User creation successful. Welcome, {name}!"

# Define a function to log in a user
def login_user(email, password):
    # Query the users table for the email and password
    c.execute("""SELECT * FROM users WHERE email = ? AND password = ?""", (email, password))
    # Fetch the record
    record = c.fetchone()
    # If the record is not None, the login is successful
    if record is not None:
        # Return the user name
        return record[0]
    else:
        # Return None
        return None

# Define a function to display the availability status of each item
def display_availability():
    # Create a data frame to store the availability status
    availability = pd.DataFrame(columns=["Item", "Location", "Available"])
    # Loop through the items
    for index, row in items.iterrows():
        # Get the item and location
        item = row["Item"]
        location = row["Location"]
        # Get the current date
        today = datetime.date.today()
        # Check if the item is available for today
        available = is_available(item, location, today, today)
        # Append the availability status to the data frame
        availability = availability.append({"Item": item, "Location": location, "Available": available}, ignore_index=True)
    # Display the data frame as a table
    st.table(availability)

# Create a title for the app
st.title("Item Reservation App")

# Create a sidebar for the user options
sidebar = st.sidebar
# Create a radio button for the user to choose between creating a profile, logging in, or viewing availability
user_option = sidebar.radio("Choose an option:", ["Create a profile", "Log in", "View availability"])

# If the user chooses to create a profile
if user_option == "Create a profile":
    # Display a header
    st.header("Create a profile")
    # Create input fields for the name, email, and password
    name = st.text_input("Enter your name:")
    email = st.text_input("Enter your email:")
    password = st.text_input("Enter your password:", type="password")
    # Create a button to submit the user details
    submit = st.button("Submit")
    # If the button is clicked
    if submit:
        # Call the create_user function and display the result
        result = create_user(name, email, password)
        st.write(result)

# If the user chooses to log in
elif user_option == "Log in":
    # Display a header
    st.header("Log in")
    # Create input fields for the email and password
    email = st.text_input("Enter your email:")
    password = st.text_input("Enter your password:", type="password")
    # Create a button to submit the user details
    submit = st.button("Submit")
    # If the button is clicked
    if submit:
        # Call the login_user function and store the result
        user = login_user(email, password)
        # If the result is not None, the login is successful
        if user is not None:
            # Display a welcome message
            st.write(f"Welcome, {user}!")
            # Create a radio button for the user to choose between reserving an item or requesting a reservation
            reservation_option = st.radio("Choose an option:", ["Reserve an item", "Request a reservation"])
            # If the user chooses to reserve an item
            if reservation_option == "Reserve an item":
                # Display a header
                st.header("Reserve an item")
                # Create a select box for the user to choose an item
                item = st.selectbox("Choose an item:", items["Item"].unique())
                # Create a select box for the user to choose a location
                location = st.selectbox("Choose a location:", items["Location"].unique())
                # Create a date input for the user to choose a start date
                start_date = st.date_input("Choose a start date:")
                # Create a date input for the user to choose an end date
                end_date = st.date_input("Choose an end date:")
                # Create a button to submit the reservation details
                submit = st.button("Submit")
                # If the button is clicked
                if submit:
                    # Call the reserve_item function and display the result
                    result = reserve_item(user, item, location, start_date, end_date)
                    st.write(result)
            # If the user chooses to request a reservation
            elif reservation_option == "Request a reservation":
                # Display a header
                st.header("Request a reservation")
                # Create a select box for the user to choose an item
                item = st.selectbox("Choose an item:", items["Item"].unique())
                # Create a select box for the user to choose a location
                location = st.selectbox("Choose a location:", items["Location"].unique())
# Create a date input for the user to choose an end date
end_date = st.date_input("Choose an end date:")
# Create a button to submit the reservation details
submit = st.button("Submit")
# If the button is clicked
if submit:
    # Call the request_reservation function and store the result
    result = request_reservation(user, item, location, start_date, end_date)
    # If the result is not None, the item is already reserved
    if result is not None:
        # Display the result
        st.write(result)
        # Get the user input for requesting the reservation
        request = st.text_input("Enter Y or N:")
        # If the user enters Y
        if request == "Y":
            # Display a message that the request is sent
            st.write("Your request is sent to the user who reserved the item. Please wait for their response.")
            # TODO: Implement the logic for sending and receiving the request
        # If the user enters N
        elif request == "N":
            # Display a message that the request is cancelled
            st.write("Your request is cancelled. You can try to reserve another item or date.")
        # If the user enters anything else
        else:
            # Display a message that the input is invalid
            st.write("Invalid input. Please enter Y or N.")
    # If the result is None, the item is available
    else:
        # Display a message that the item is available
        st.write("The item is available for the date range you selected. You can reserve it by choosing the 'Reserve an item' option.")
