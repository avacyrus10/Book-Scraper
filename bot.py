from dotenv import load_dotenv
import os
import requests
from pyzbar.pyzbar import decode
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import re
import pandas as pd
import time
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler, CallbackQueryHandler
load_dotenv() 
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
# Define stages for the conversation handler
SEARCH_METHOD, RECEIVE_ISBN_IMAGE, RECEIVE_KEYWORD = range(3)

def initialize_driver():
    """
    Initialize and configure the Selenium WebDriver.
    :return: Configured WebDriver instance.
    """
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--remote-debugging-port=9222')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

driver = initialize_driver()

# Dictionary to store book information
books_dict = {
    'Title': [],
    'ISBN': [],
    'Author': [],
    'Translator': [],
    'Publisher': [],
    'Publish Year': [],
    'Publishing Turn': [],
    'Language': [],
    'Pages': [],
    'Dimensions': [],
    'Best Sellers Rank': [],
    'Customer Reviews': []
}

def extract_isbn_from_image(image_path):
    """
    Extract ISBN from an image of a barcode.
    :param image_path: Path to the image file.
    :return: Extracted ISBN if found, else None.
    """
    image = Image.open(image_path)
    barcodes = decode(image)
    for barcode in barcodes:
        barcode_data = barcode.data.decode('utf-8')
        if re.match(r'^\d{10,13}$', barcode_data):
            return barcode_data
    return None

def search_amazon(query):
    """
    Search Amazon for a book using the given query.
    :param query: Search query (ISBN or keyword).
    :return: URL of the first search result, or None if not found.
    """
    global driver
    search_url = f"https://www.amazon.co.uk/s?k={query}"
    try:
        print(f"Searching for {query} at {search_url}")
        driver.get(search_url)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div.s-main-slot div[data-component-type="s-search-result"]'))
        )

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        result = soup.select_one('div.s-main-slot div[data-component-type="s-search-result"] a.a-link-normal')
        if result:
            book_link = "https://www.amazon.co.uk" + result['href']
            return book_link
        else:
            return None
    except Exception as e:
        print(f"Error during search: {e}")
        driver.quit()
        time.sleep(5)
        driver = initialize_driver()
        return None

def fetch_book_info_amazon(book_link):
    """
    Fetch detailed information about a book from its Amazon page.
    :param book_link: URL of the Amazon book page.
    :return: Dictionary of book information, or None if an error occurs.
    """
    global driver
    try:
        print(f"Fetching book information from {book_link}")
        driver.get(book_link)

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "productTitle"))
        )

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # Extract book details
        title = soup.find(id='productTitle').text.strip() if soup.find(id='productTitle') else "N/A"
        author_elem = soup.select_one('span.author a.a-link-normal')
        author = author_elem.text.strip() if author_elem else "N/A"
        translator = "N/A"

        # Initialize default values
        publisher = publish_year = publishing_turn = language = pages = dimensions = best_sellers_rank = "N/A"
        customer_reviews = "N/A"

        details_elem = soup.find(id='detailBullets_feature_div')
        if details_elem:
            details_text = details_elem.get_text(separator="\n")
            publisher_match = re.search(r'Publisher:\s*(.+)', details_text)
            publish_year_match = re.search(r'Publication date:\s*(.+)', details_text)
            language_match = re.search(r'Language:\s*(.+)', details_text)
            pages_match = re.search(r'(\d+)\s*pages', details_text)
            dimensions_match = re.search(r'Dimensions:\s*(.+)', details_text)
            best_sellers_rank_match = re.search(r'Best Sellers Rank:\s*(.+)', details_text)
            publishing_turn_match = re.search(r'Publishing turn:\s*(.+)', details_text)

            # Update book details if found
            if publisher_match:
                publisher = publisher_match.group(1).strip()
            if publish_year_match:
                publish_year = publish_year_match.group(1).strip()
            if language_match:
                language = language_match.group(1).strip()
            if pages_match:
                pages = pages_match.group(1).strip()
            if dimensions_match:
                dimensions = dimensions_match.group(1).strip()
            if best_sellers_rank_match:
                best_sellers_rank = best_sellers_rank_match.group(1).strip()
            if publishing_turn_match:
                publishing_turn = publishing_turn_match.group(1).strip()

        # Extract ISBN
        isbn_10 = isbn_13 = "N/A"
        if details_elem:
            details_text = details_elem.get_text(separator="\n")
            isbn_10_match = re.search(r'ISBN-10:\s*(\d{10})', details_text)
            isbn_13_match = re.search(r'ISBN-13:\s*(\d{13})', details_text)
            if isbn_10_match:
                isbn_10 = isbn_10_match.group(1).strip()
            if isbn_13_match:
                isbn_13 = isbn_13_match.group(1).strip()

        customer_reviews_elem = soup.select_one('span#acrCustomerReviewText')
        if customer_reviews_elem:
            customer_reviews = customer_reviews_elem.text.strip()

        # Append book details to dictionary
        books_dict['Title'].append(title)
        books_dict['ISBN'].append(isbn_13 if isbn_13 != "N/A" else isbn_10)
        books_dict['Author'].append(author)
        books_dict['Translator'].append(translator)
        books_dict['Publisher'].append(publisher)
        books_dict['Publish Year'].append(publish_year)
        books_dict['Publishing Turn'].append(publishing_turn)
        books_dict['Language'].append(language)
        books_dict['Pages'].append(pages)
        books_dict['Dimensions'].append(dimensions)
        books_dict['Best Sellers Rank'].append(best_sellers_rank)
        books_dict['Customer Reviews'].append(customer_reviews)

        return {
            'Title': title,
            'ISBN': isbn_13 if isbn_13 != "N/A" else isbn_10,
            'Author': author,
            'Translator': translator,
            'Publisher': publisher,
            'Publish Year': publish_year,
            'Publishing Turn': publishing_turn,
            'Language': language,
            'Pages': pages,
            'Dimensions': dimensions,
            'Best Sellers Rank': best_sellers_rank,
            'Customer Reviews': customer_reviews
        }

    except Exception as e:
        print(f"Error during fetching book info: {e}")
        driver.quit()
        time.sleep(5)
        driver = initialize_driver()
        return None

def save_to_google_sheet(books_dict):
    """
    Save extracted book data to Google Sheets.
    :param books_dict: Dictionary of book information.
    :return: None
    """
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('f.json', scope)
    client = gspread.authorize(creds)
    sheet = client.open('scraper')
    worksheet = sheet.get_worksheet(0)

    books_df = pd.DataFrame(books_dict)
    worksheet.clear()
    worksheet.update([books_df.columns.values.tolist()] + books_df.values.tolist())

    print("Data has been successfully saved to the Google Sheet")

def start(update: Update, context: CallbackContext) -> int:
    """
    Start the bot and ask the user to choose a search method.
    :param update: Telegram update object.
    :param context: CallbackContext object.
    :return: Conversation state.
    """
    keyboard = [
        [
            InlineKeyboardButton("Search by ISBN", callback_data='isbn'),
            InlineKeyboardButton("Search by Keyword", callback_data='keyword'),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "Welcome to the Book Scraper Bot! Choose how you want to search for a book:",
        reply_markup=reply_markup
    )
    return SEARCH_METHOD

def choose_search_method(update: Update, context: CallbackContext) -> int:
    """
    Handle the user's search method selection.
    :param update: Telegram update object.
    :param context: CallbackContext object.
    :return: Next conversation state.
    """
    query = update.callback_query
    query.answer()
    if query.data == 'isbn':
        query.edit_message_text(text="Please send me the image of the book's ISBN.")
        return RECEIVE_ISBN_IMAGE
    elif query.data == 'keyword':
        query.edit_message_text(text="Please enter the book title, author, or keyword.")
        return RECEIVE_KEYWORD
    else:
        query.edit_message_text(text="Invalid selection. Please choose again.")
        return SEARCH_METHOD

def receive_isbn_image(update: Update, context: CallbackContext) -> int:
    """
    Receive and process the ISBN image sent by the user.
    :param update: Telegram update object.
    :param context: CallbackContext object.
    :return: Conversation state.
    """
    photo_file = update.message.photo[-1].get_file()
    photo_path = "isbn_image.jpg"
    photo_file.download(photo_path)

    isbn = extract_isbn_from_image(photo_path)
    if isbn:
        update.message.reply_text(f"Extracted ISBN: {isbn}. Searching for the book...")
        book_link = search_amazon(isbn)
        if book_link:
            book_info = fetch_book_info_amazon(book_link)
            if book_info:
                book_info_str = format_book_info(book_info)
                update.message.reply_text(book_info_str)
                save_to_google_sheet(books_dict)
                update.message.reply_text("Data has been successfully saved to the Google Sheet.")
            else:
                update.message.reply_text("Failed to fetch book information.")
        else:
            update.message.reply_text("Failed to find book link.")
    else:
        update.message.reply_text("Failed to extract ISBN from the image.")

    return ConversationHandler.END

def receive_keyword(update: Update, context: CallbackContext) -> int:
    """
    Receive and process the keyword sent by the user.
    :param update: Telegram update object.
    :param context: CallbackContext object.
    :return: Conversation state.
    """
    keyword = update.message.text.strip()
    update.message.reply_text(f"Searching for the book with keyword: {keyword}")
    book_link = search_amazon(keyword)
    if book_link:
        book_info = fetch_book_info_amazon(book_link)
        if book_info:
            book_info_str = format_book_info(book_info)
            update.message.reply_text(book_info_str)
            save_to_google_sheet(books_dict)
            update.message.reply_text("Data has been successfully saved to the Google Sheet.")
        else:
            update.message.reply_text("Failed to fetch book information.")
    else:
        update.message.reply_text("Failed to find book link.")

    return ConversationHandler.END

def format_book_info(book_info):
    """
    Format book information for display.
    :param book_info: Dictionary of book information.
    :return: Formatted string of book information.
    """
    return (
        f"Title: {book_info['Title']}\n"
        f"Author: {book_info['Author']}\n"
        f"Publisher: {book_info['Publisher']}\n"
        f"Publish Year: {book_info['Publish Year']}\n"
        f"Language: {book_info['Language']}\n"
        f"Pages: {book_info['Pages']}\n"
        f"Dimensions: {book_info['Dimensions']}\n"
        f"Best Sellers Rank: {book_info['Best Sellers Rank']}\n"
        f"Customer Reviews: {book_info['Customer Reviews']}"
    )

def cancel(update: Update, context: CallbackContext) -> int:
    """
    Cancel the current operation.
    :param update: Telegram update object.
    :param context: CallbackContext object.
    :return: Conversation state.
    """
    update.message.reply_text('Operation cancelled.')
    return ConversationHandler.END

def main():

    updater = Updater("7215489781:AAFhxC7lBxYydUMa8kXJbOKOFe929z2-eWE", use_context=True)

    dispatcher = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            SEARCH_METHOD: [CallbackQueryHandler(choose_search_method)],
            RECEIVE_ISBN_IMAGE: [MessageHandler(Filters.photo, receive_isbn_image)],
            RECEIVE_KEYWORD: [MessageHandler(Filters.text & ~Filters.command, receive_keyword)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dispatcher.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()

