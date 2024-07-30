import streamlit as st
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import bcrypt
import random
import urllib
import string
from datetime import datetime

# Load MongoDB credentials from secrets.toml
username = urllib.parse.quote_plus(st.secrets["mongodb"]["username"])
password = urllib.parse.quote_plus(st.secrets["mongodb"]["password"])
cluster = st.secrets["mongodb"]["cluster"]
dbname = st.secrets["mongodb"]["dbname"]

# MongoDB setup
uri = f"mongodb+srv://{username}:{password}@{cluster}/{dbname}?retryWrites=true&w=majority"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client[dbname]  # Use the dbname from secrets.toml

# UserManager Class: Manages user-related operations
class UserManager:
    def __init__(self):
        # Connect to user Database
        self.users_collection = db.users

    # Method to create a new user
    def create_user(self, username, password):
        if self.users_collection.find_one({"username": username}):
            return "Username already exists"

        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        self.users_collection.insert_one({"username": username, "password": hashed})
        return "User created successfully"

    # Method to authenticate a user
    def authenticate_user(self, username, password):
        user = self.users_collection.find_one({"username": username})
        if user and bcrypt.checkpw(password.encode("utf-8"), user["password"]):
            return True
        return False

    # Method to delete a user
    def delete_user(self, username, password):
        user = self.users_collection.find_one({"username": username})
        if user and bcrypt.checkpw(password.encode("utf-8"), user["password"]):
            # Delete user's passwords
            db.passwords.delete_many({"username": username})
            # Delete user
            self.users_collection.delete_one({"username": username})
            return "User and all associated passwords deleted successfully"
        return "Authentication failed or user does not exist"


# PasswordManager Class: Manages password-related operations
class PasswordManager:
    def __init__(self, username):
        self.username = username
        self.passwords_collection = db.passwords

    # Method to generate a random password
    def generate_password(self, length=10):
        characters = string.ascii_letters + string.digits + "@$"
        password = "".join(random.choice(characters) for i in range(length))
        return password

    # Method to save a password entry
    def save_password(self, service_name, use, platform, password=None):
        if not password:
            password = self.generate_password()
        self.passwords_collection.insert_one(
            {
                "username": self.username,
                "service_name": service_name,
                "use": use,
                "platform": platform,
                "password": password,
                "timestamp": datetime.now(),
            }
        )

    # Method to update a password entry
    def update_password(self, service_name, new_password):
        result = self.passwords_collection.update_one(
            {"username": self.username, "service_name": service_name},
            {"$set": {"password": new_password, "timestamp": datetime.now()}},
        )
        return result.modified_count > 0

    # Method to delete a password entry
    def delete_password(self, service_name):
        result = self.passwords_collection.delete_one(
            {"username": self.username, "service_name": service_name}
        )
        return result.deleted_count > 0

    # Method to view all password entries
    def view_all_passwords(self):
        passwords = self.passwords_collection.find({"username": self.username})
        return list(passwords)


# Main function: Entry point of the program
def main():
    user_manager = UserManager()
    st.set_page_config(page_title="Password Manager", page_icon="🔐")
    # Welcome page with image
    st.title("Welcome to the Password Manager")
    st.image("myimage.jpeg", width=150)  # Update this to the path of your image

    # Check if user is logged in
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.username = None

    # Show login/signup options if not logged in
    if not st.session_state.logged_in:
        # Login and Signup options
        option = st.sidebar.selectbox("Select an option", ["Login", "Signup"])

        if option == "Signup":
            st.subheader("Create a new account")
            username = st.text_input("Enter username")
            password = st.text_input("Enter password", type="password")
            if st.button("Signup"):
                if username and password:
                    message = user_manager.create_user(username, password)
                    st.success(message)
                    if "successfully" in message:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                else:
                    st.error("Please provide both username and password")

        if option == "Login":
            st.subheader("Login to your account")
            username = st.text_input("Enter username")
            password = st.text_input("Enter password", type="password")
            if st.button("Login"):
                if user_manager.authenticate_user(username, password):
                    st.success("Authentication successful")
                    st.session_state.logged_in = True
                    st.session_state.username = username
                else:
                    st.error("Authentication failed")

    # If user is logged in, show the password manager options
    if st.session_state.logged_in:
        st.subheader(f"Welcome, {st.session_state.username}")

        password_manager = PasswordManager(st.session_state.username)

        # Options after login
        option = st.sidebar.selectbox("Select an option", ["Create password entry", "Update password entry", "Delete password entry", "View all password entries", "Logout"])

        if option == "Create password entry":
            st.subheader("Create a new password entry")
            service_name = st.text_input("Enter service or user name")
            use = st.text_input("Enter use of the password")
            platform = st.text_input("Enter platform")
            custom_password = st.text_input("Enter custom password (leave blank to generate)")
            if st.button("Save"):
                password_manager.save_password(service_name, use, platform, custom_password)
                st.success("Password entry saved.")

        if option == "Update password entry":
            st.subheader("Update an existing password entry")
            service_name = st.text_input("Enter service or user name to update")
            new_password = st.text_input("Enter new password")
            if st.button("Update"):
                if password_manager.update_password(service_name, new_password):
                    st.success("Password updated.")
                else:
                    st.error("Service not found.")

        if option == "Delete password entry":
            st.subheader("Delete a password entry")
            service_name = st.text_input("Enter service or user name to delete")
            if st.button("Delete"):
                if password_manager.delete_password(service_name):
                    st.success("Password entry deleted.")
                else:
                    st.error("Service not found.")

        if option == "View all password entries":
            st.subheader("All Password Entries")
            passwords = password_manager.view_all_passwords()
            if passwords:
                import pandas as pd
                df = pd.DataFrame(passwords)
                df = df.drop(columns=["_id", "username"])
                st.dataframe(df)
            else:
                st.info("No password entries found.")

        if option == "Logout":
            st.session_state.logged_in = False
            st.session_state.username = None
            st.success("Logged out successfully")
            st.experimental_rerun()  # Rerun the script to reset the interface

        if st.sidebar.button("Delete User"):
            st.subheader("Delete User")
            username = st.session_state.username
            password = st.text_input("Enter your password to confirm", type="password")
            if st.button("Delete"):
                message = user_manager.delete_user(username, password)
                if "successfully" in message:
                    st.success(message)
                    st.session_state.logged_in = False
                    st.session_state.username = None
                    st.experimental_rerun()  # Rerun the script to reset the interface
                else:
                    st.error(message)

if __name__ == "__main__":
    main()
