from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
import pandas as pd
import time
import random

# Initialize data structure to track user reports
reported_users = pd.DataFrame(columns=['User ID', 'Violation Count', 'Reason', 'Last Report Time'])

# Set reporting threshold
REPORT_THRESHOLD = 100

# Initialize the WebDriver for Chrome
service = Service("/usr/local/bin/chromedriver")  # Path where Chromedriver is installed in Docker
driver = webdriver.Chrome(service=service)

def login_to_clubhouse(username, password):
    """Login to Clubhouse using Selenium"""
    driver.get("https://www.joinclubhouse.com")
    time.sleep(5)  # Allow time for the page to load

    # Locate the login elements and log in (you may need to adjust these based on the site structure)
    login_button = driver.find_element(By.XPATH, "//button[text()='Log In']")
    login_button.click()
    time.sleep(2)

    username_field = driver.find_element(By.NAME, 'username')
    password_field = driver.find_element(By.NAME, 'password')

    username_field.send_keys(username)
    password_field.send_keys(password)
    password_field.send_keys(Keys.RETURN)
    time.sleep(5)  # Wait for login to complete

def search_user_by_username(username):
    """Search for a user by username on Clubhouse and extract their user ID"""
    # Use the search feature on the site to locate the user by their username
    search_box = driver.find_element(By.XPATH, "//input[@placeholder='Search']")
    search_box.send_keys(username)
    search_box.send_keys(Keys.RETURN)
    time.sleep(5)  # Allow time for search results to appear

    try:
        # Dynamically extract the user ID by finding the relevant profile element in the HTML
        user_profile_element = driver.find_element(By.XPATH, f"//a[contains(@href, '/@{username}')]")
        user_profile_element.click()
        time.sleep(3)  # Wait for the profile to load
        
        # Extract user ID from the URL (if available)
        current_url = driver.current_url
        if '@' in current_url:
            user_id = current_url.split('/')[-1]
        else:
            user_id = None
        
        return user_id
    except Exception as e:
        print(f"Error while searching for {username}: {e}")
        return None

def report_user(user_id, username, reason):
    """Report a user with a specified reason"""
    print(f"Reporting user {user_id or username} for {reason}")

    # Update the violation count for the user
    global reported_users
    if user_id in reported_users['User ID'].values:
        reported_users.loc[reported_users['User ID'] == user_id, 'Violation Count'] += 1
    else:
        new_user = pd.DataFrame({'User ID': [user_id], 'Violation Count': [1], 'Reason': [reason], 'Last Report Time': [time.time()]})
        reported_users = pd.concat([reported_users, new_user], ignore_index=True)

    # If the user has been reported enough times, stop reporting
    user_data = reported_users[reported_users['User ID'] == user_id]
    if user_data['Violation Count'].values[0] >= REPORT_THRESHOLD:
        print(f"User {user_id or username} has reached the report threshold ({REPORT_THRESHOLD} reports).")
        # Trigger suspension or notify admin
        notify_suspension(user_id)

def notify_suspension(user_id):
    """Notify about user suspension after threshold is reached"""
    print(f"User {user_id} has been reported {REPORT_THRESHOLD} times. User should be suspended now.")

def report_multiple_times(user_id, username, reason, remaining_reports):
    """Automate the process of reporting a user multiple times until suspension with delay"""
    for _ in range(remaining_reports):
        time.sleep(random.randint(5, 10))  # Random sleep to avoid spamming
        report_user(user_id, username, reason)

def handle_report_command(command):
    """Parse and handle a command for reporting a user"""
    command_parts = command.split(" ", 2)
    if len(command_parts) < 3:
        print("Invalid command. Please use: @report <username> <reason>")
        return

    username = command_parts[1]
    reason = command_parts[2]

    # First try to get the user ID by searching for the username
    user_id = search_user_by_username(username)

    if user_id:
        print(f"Found user {username} with ID {user_id}.")
    else:
        print(f"User {username} ID not found, proceeding with the username for reporting.")
        user_id = username  # If no user ID, use the username directly.

    print(f"Initiating report for {username} with reason '{reason}'...")

    # Calculate the remaining reports needed to reach the threshold
    user_data = reported_users[reported_users['User ID'] == user_id]
    current_report_count = user_data['Violation Count'].values[0] if not user_data.empty else 0
    remaining_reports = max(REPORT_THRESHOLD - current_report_count, 0)

    if remaining_reports > 0:
        print(f"User {username} has {remaining_reports} reports left to reach the threshold.")
        report_multiple_times(user_id, username, reason, remaining_reports)
    else:
        print(f"User {username} has already reached the reporting threshold.")

# Main Function to continuously read input
if __name__ == "__main__":
    # Log into Clubhouse (replace with your actual credentials)
    login_to_clubhouse('your_username', 'your_password')
    
    print("Bot is running...")

    # Continuously accept commands from the terminal
    while True:
        command = input("Enter command (e.g., @report <username> <reason>): ")
        
        # Break if exit command is entered
        if command.lower() == "exit":
            print("Exiting bot...")
            driver.quit()
            break
        
        handle_report_command(command)
