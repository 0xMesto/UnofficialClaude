import logging
import re
import time
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UnofficialClaudeAPI:
    def __init__(self, browser_ws_endpoint):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.base_url = "https://claude.ai"
        self.chat_code = None
        self.browser_ws_endpoint = browser_ws_endpoint
        self.timeout = 120000  # 120 seconds timeout
        self.response_timeout = 10  # 10 seconds timeout for Claude's response
        self.last_message_count = 0
        self.message_count = 0
        self.pause_duration = 5.5 * 60 * 60  # 5 hours and 30 minutes in seconds
        logger.info("UnofficialClaudeAPI instance created")

    def __enter__(self):
        logger.debug("Entering context manager")
        self.playwright = sync_playwright().start()
        logger.debug("Playwright started")
        
        try:
            # Connect to the existing browser instance
            self.browser = self.playwright.chromium.connect_over_cdp(self.browser_ws_endpoint)
            logger.debug("Connected to existing browser")
            
            # Use the default context and create a new page
            self.context = self.browser.contexts[0]
            self.page = self.context.new_page()
            logger.debug("New page created in existing context")

            # Navigate to Claude AI
            self.page.goto(self.base_url, timeout=self.timeout)
            logger.debug(f"Navigated to {self.base_url}")
            
            # Wait for the page to be fully loaded
            self.wait_for_page_load()
            
            logger.debug("Successfully connected to browser")
        except Exception as e:
            logger.error(f"Failed to connect to browser: {e}", exc_info=True)
            raise

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.debug("Exiting context manager")
        self.close()

    def wait_for_page_load(self):
        logger.debug("Waiting for page to load")
        try:
            self.page.wait_for_load_state("networkidle", timeout=self.timeout)
            self.page.wait_for_load_state("domcontentloaded", timeout=self.timeout)
            self.page.wait_for_load_state("load", timeout=self.timeout)
            time.sleep(5)  # Additional 5-second delay
            logger.debug("Page fully loaded")
        except PlaywrightTimeoutError:
            logger.warning("Timeout while waiting for page to load. Proceeding anyway.")

    def reload_page(self):
        logger.info("Reloading the page")
        try:
            self.page.reload(timeout=self.timeout)
            self.wait_for_page_load()
            logger.info("Page reloaded successfully")
        except Exception as e:
            logger.error(f"Failed to reload the page: {e}", exc_info=True)
            raise

    def start_conversation(self):
        logger.info("Starting conversation")
        try:
            self.page.goto(f"{self.base_url}/new", timeout=self.timeout)
            logger.debug(f"Navigated to {self.base_url}/new")
            
            self.wait_for_page_load()
            
            # Wait for the input field to appear
            input_selector = "div[contenteditable='true']"
            self.page.wait_for_selector(input_selector, state="visible", timeout=self.timeout)
            logger.debug("Input field is visible")
            
            self.last_message_count = 0
            self.message_count = 0
            logger.info("Successfully started conversation")
        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout error while starting conversation: {e}", exc_info=True)
            self.reload_page()
            raise
        except Exception as e:
            logger.error(f"An error occurred while starting conversation: {e}", exc_info=True)
            self.reload_page()
            raise

    def send_message(self, message):
        logger.info(f"Sending message: {message}")
        try:
            if self.message_count >= 30:
                logger.info(f"Reached 30 messages. Pausing for {self.pause_duration / 3600} hours.")
                time.sleep(self.pause_duration)
                self.message_count = 0
                self.reload_page()

            self.wait_for_page_load()
            
            input_selector = "div[contenteditable='true']"
            input_element = self.page.query_selector(input_selector)
            
            if input_element:
                # Simulate human typing
                for char in message:
                    input_element.type(char, delay=random.uniform(50, 200))
                    time.sleep(random.uniform(0.05, 0.2))
                
                logger.debug("Filled input with message")
            else:
                logger.error("Input element not found")
                self.reload_page()
                raise Exception("Input element not found")
            
            # Wait for send button to appear
            send_button_selector = "button[aria-label='Send Message']"
            self.page.wait_for_selector(send_button_selector, state="visible", timeout=self.timeout)
            logger.debug("Send button is visible")

            # Get the current message count
            current_message_count = len(self.page.query_selector_all("div.group"))

            # Click the send button
            self.page.click(send_button_selector)
            logger.debug("Clicked send button")
            
            # Wait for a new message to appear
            start_time = time.time()
            while time.time() - start_time < self.response_timeout:
                new_message_count = len(self.page.query_selector_all("div.group"))
                if new_message_count > current_message_count:
                    logger.debug("New message appeared")
                    break
                time.sleep(1)
            else:
                logger.warning("Timeout waiting for new message")
            
            # Wait for Claude's response
            response_selector = "div.font-claude-message >> nth=-1"
            self.page.wait_for_selector(response_selector, state="attached", timeout=self.timeout)
            logger.debug("Waited for response selector")
            
            # Wait for the response to finish loading (when the typing animation stops)
            start_time = time.time()
            last_response = ""
            while time.time() - start_time < self.response_timeout:
                if not self.page.query_selector('.animate-pulse'):
                    response_element = self.page.query_selector(response_selector)
                    if response_element:
                        current_response = response_element.inner_html()
                        if current_response == last_response:
                            logger.debug("Response finished loading")
                            break
                        last_response = current_response
                time.sleep(1)
            else:
                logger.warning("Timeout waiting for response to finish loading")

            # Extract the final response text
            response_element = self.page.query_selector(response_selector)
            if response_element:
                response_html = response_element.inner_html()
                response_text = self.html_to_text(response_html)
                logger.info(f"Received response: {response_text[:500]}...")  # Log first 500 chars
                self.last_message_count = len(self.page.query_selector_all("div.group"))
                self.message_count += 1
                return response_text
            else:
                logger.warning("No response element found")
                return None
        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout error while sending message or waiting for response: {e}", exc_info=True)
            self.reload_page()
            raise
        except Exception as e:
            logger.error(f"An error occurred while sending message: {e}", exc_info=True)
            self.reload_page()
            raise

    def get_conversation_history(self):
        logger.info("Getting conversation history")
        try:
            self.wait_for_page_load()
            
            self.page.evaluate("window.scrollTo(0, 0)")
            logger.debug("Scrolled to top of page")
            self.page.wait_for_load_state("networkidle", timeout=self.timeout)
            logger.debug("Waited for network idle after scrolling")

            conversation_html = self.page.inner_html("div.flex-1.flex.flex-col.gap-3")
            logger.debug(f"Conversation HTML: {conversation_html[:500]}...")  # Log first 500 chars of HTML
            conversation_soup = BeautifulSoup(conversation_html, 'html.parser')
            
            messages = conversation_soup.find_all("div", class_="group")
            history = []
            for msg in messages:
                user_message = msg.find("div", class_="font-user-message")
                claude_message = msg.find("div", class_="font-claude-message")
                
                if user_message:
                    content = self.html_to_text(str(user_message))
                    history.append({"sender": "User", "content": content})
                    logger.debug(f"Added user message to history: {content[:100]}...")
                elif claude_message:
                    content = self.html_to_text(str(claude_message))
                    history.append({"sender": "Claude", "content": content})
                    logger.debug(f"Added Claude message to history: {content[:100]}...")
                else:
                    logger.warning("Unrecognized message structure")

            logger.info(f"Retrieved {len(history)} messages from history")
            return history
        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout error while fetching conversation history: {e}", exc_info=True)
            self.reload_page()
            raise
        except Exception as e:
            logger.error(f"An error occurred while getting conversation history: {e}", exc_info=True)
            self.reload_page()
            raise

    def upload_file(self, file_path):
        logger.info(f"Uploading file: {file_path}")
        try:
            self.wait_for_page_load()
            
            file_input_selector = "input[type='file']"
            self.page.wait_for_selector(file_input_selector, state="attached", timeout=self.timeout)
            
            file_input = self.page.query_selector(file_input_selector)
            if file_input:
                file_input.set_input_files(file_path)
                logger.debug("Set file input")
                self.page.wait_for_load_state("networkidle", timeout=self.timeout)
                logger.debug("Waited for network idle after file upload")
                logger.info(f"File uploaded successfully: {file_path}")
            else:
                logger.error("File upload input not found")
                self.reload_page()
                raise Exception("File upload input not found")
        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout error while uploading file: {e}", exc_info=True)
            self.reload_page()
            raise
        except Exception as e:
            logger.error(f"An error occurred while uploading file: {e}", exc_info=True)
            self.reload_page()
            raise

    def set_model(self, model_name):
        logger.info(f"Setting model to: {model_name}")
        try:
            self.wait_for_page_load()
            
            model_selector = "button[data-testid='model-selector-dropdown']"
            self.page.click(model_selector)
            logger.debug("Clicked model selector dropdown")

            model_option = f"button:has-text('{model_name}')"
            self.page.click(model_option)
            logger.debug(f"Selected model: {model_name}")

            self.page.wait_for_load_state("networkidle", timeout=self.timeout)
            logger.debug("Waited for network idle after model selection")
            logger.info(f"Model set to: {model_name}")
        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout error while setting model: {e}", exc_info=True)
            self.reload_page()
            raise
        except Exception as e:
            logger.error(f"An error occurred while setting model: {e}", exc_info=True)
            self.reload_page()
            raise

    def wait_for_network_idle(self, timeout=60000):
        try:
            self.page.wait_for_load_state("networkidle", timeout=timeout)
            logger.debug("Network is idle")
        except PlaywrightTimeoutError:
            logger.warning("Timeout waiting for network idle")

    @staticmethod
    def html_to_text(html):
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(separator='\n', strip=True)
        return text

    def close(self):
        logger.info("Closing UnofficialClaudeAPI instance")
        try:
            if self.page:
                self.page.close()
                logger.debug("Page closed")
            # We don't close the browser or context as they were pre-existing
            if self.playwright:
                self.playwright.stop()
                logger.debug("Playwright stopped")
        except Exception as e:
            logger.error(f"An error occurred while closing: {e}", exc_info=True)
        finally:
            logger.info("UnofficialClaudeAPI instance closed")