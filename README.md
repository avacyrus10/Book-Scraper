
# Book Scraper Bot 

## Table of Contents
- [Introduction](#introduction)
- [Installation](#installation)
- [Usage](#usage)
  - [Starting the Bot](#starting-the-bot)
  - [Search Methods](#search-methods)
- [Functions Overview](#functions-overview)
  - [initialize_driver](#initialize_driver)
  - [extract_isbn_from_image](#extract_isbn_from_image)
  - [search_amazon](#search_amazon)
  - [fetch_book_info_amazon](#fetch_book_info_amazon)
  - [save_to_google_sheet](#save_to_google_sheet)
  - [start](#start)
  - [choose_search_method](#choose_search_method)
  - [receive_isbn_image](#receive_isbn_image)
  - [receive_keyword](#receive_keyword)
  - [format_book_info](#format_book_info)
  - [cancel](#cancel)
  - [main](#main)

## Introduction
This project is a Telegram bot that helps users search for book information using either an ISBN image or keywords. The bot retrieves book details from Amazon and saves the information to a Google Sheet.

## Installation
To set up the bot, follow these steps:

1. **Download and install Google Chrome:**
   ```bash
   wget https://mirror.cs.uchicago.edu/google-chrome/pool/main/g/google-chrome-stable/google-chrome-stable_114.0.5735.106-1_amd64.deb
   dpkg -i google-chrome-stable_114.0.5735.106-1_amd64.deb
   apt-get -f install
   ```

2. **Download and install ChromeDriver:**
   ```bash
   wget https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_linux64.zip
   unzip chromedriver_linux64.zip
   mv chromedriver /usr/bin/chromedriver
   chmod +x /usr/bin/chromedriver
   ```

3. **Install required libraries:**
   ```bash
   apt-get install -y libzbar0
   pip install pyzbar
   pip install python-telegram-bot==13.7
   pip install requests pillow selenium webdriver_manager beautifulsoup4 pandas gspread oauth2client
   ```

## Usage

### Starting the Bot
To start the bot, run the `main` function in the script:
```python
if __name__ == "__main__":
    main()
```

### Search Methods
Users can search for book information using:
1. **ISBN Image:** Upload an image of the book's ISBN.
2. **Keyword:** Enter a book title, author, or keyword.

## Functions Overview

### initialize_driver
Initializes and configures the Selenium WebDriver.
```python
def initialize_driver():
    ...
```

### extract_isbn_from_image
Extracts ISBN from an image of a barcode.
```python
def extract_isbn_from_image(image_path):
    ...
```

### search_amazon
Searches Amazon for a book using the given query.
```python
def search_amazon(query):
    ...
```

### fetch_book_info_amazon
Fetches detailed information about a book from its Amazon page.
```python
def fetch_book_info_amazon(book_link):
    ...
```

### save_to_google_sheet
Saves extracted book data to Google Sheets.
```python
def save_to_google_sheet(books_dict):
    ...
```

### start
Starts the bot and asks the user to choose a search method.
```python
def start(update: Update, context: CallbackContext) -> int:
    ...
```

### choose_search_method
Handles the user's search method selection.
```python
def choose_search_method(update: Update, context: CallbackContext) -> int:
    ...
```

### receive_isbn_image
Receives and processes the ISBN image sent by the user.
```python
def receive_isbn_image(update: Update, context: CallbackContext) -> int:
    ...
```

### receive_keyword
Receives and processes the keyword sent by the user.
```python
def receive_keyword(update: Update, context: CallbackContext) -> int:
    ...
```

### format_book_info
Formats book information for display.
```python
def format_book_info(book_info):
    ...
```

### cancel
Cancels the current operation.
```python
def cancel(update: Update, context: CallbackContext) -> int:
    ...
```

### main
Main function to start the bot.
```python
def main():
    ...
```

## Acknowledgments
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/)
- [Selenium](https://www.selenium.dev/)
- [Google Sheets API](https://developers.google.com/sheets/api)
