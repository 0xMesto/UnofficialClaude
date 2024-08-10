import logging
import re
import asyncio
import json
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UnofficialClaudeAPI:
    def __init__(self, browser_ws_endpoint, organization_id):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.data_page = None
        self.base_url = "https://claude.ai"
        self.api_base_url = "https://api.claude.ai"
        self.chat_code = None
        self.browser_ws_endpoint = browser_ws_endpoint
        self.organization_id = organization_id
        self.timeout = 120000
        self.message_count = 0
        self.pause_duration = 5.5 * 60 * 60
        self.last_message_index = -1
        self.current_model = "Claude 3.5 Sonnet"
        logger.info("UnofficialClaudeAPI instance created")
    
    async def get_current_model(self):
        return self.current_model

    async def __aenter__(self):
        logger.debug("Entering context manager")
        self.playwright = await async_playwright().start()
        logger.debug("Playwright started")
        
        try:
            self.browser = await self.playwright.chromium.connect_over_cdp(self.browser_ws_endpoint)
            logger.debug("Connected to existing browser")
            
            self.context = self.browser.contexts[0]
            self.data_page = await self.context.new_page()
            self.page = await self.context.new_page()
            
            logger.debug("Created chat page and data fetching page")

            await self.page.goto(self.base_url, timeout=self.timeout)
            logger.debug(f"Navigated to {self.base_url} on chat page")
            
            await self.wait_for_page_load()
            
            logger.debug("Successfully connected to browser")
        except Exception as e:
            logger.error(f"Failed to connect to browser: {e}", exc_info=True)
            raise

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        logger.debug("Exiting context manager")
        await self.close()

    async def wait_for_page_load(self):
        logger.debug("Waiting for page to load")
        try:
            await self.page.wait_for_load_state("networkidle", timeout=self.timeout)
            await self.page.wait_for_load_state("domcontentloaded", timeout=self.timeout)
            await self.page.wait_for_load_state("load", timeout=self.timeout)
            await asyncio.sleep(5)
            logger.debug("Page fully loaded")
        except PlaywrightTimeoutError:
            logger.warning("Timeout while waiting for page to load. Proceeding anyway.")

    async def reload_page(self):
        logger.info("Reloading the page")
        try:
            await self.page.reload(timeout=self.timeout)
            await self.wait_for_page_load()
            logger.info("Page reloaded successfully")
        except Exception as e:
            logger.error(f"Failed to reload the page: {e}", exc_info=True)
            raise

    async def start_conversation(self):
        logger.info("Starting new conversation")
        try:
            await self.page.goto(f"{self.base_url}/new", timeout=self.timeout)
            logger.debug(f"Navigated to {self.base_url}/new")
            
            await self.wait_for_page_load()
            
            input_selector = "div[contenteditable='true']"
            await self.page.wait_for_selector(input_selector, state="visible", timeout=self.timeout)
            logger.debug("Input field is visible")
            
            self.message_count = 0
            self.last_message_index = -1
            self.chat_code = None
            
            logger.info("New conversation started successfully")
        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout error while starting conversation: {e}", exc_info=True)
            await self.reload_page()
            raise
        except Exception as e:
            logger.error(f"An error occurred while starting conversation: {e}", exc_info=True)
            await self.reload_page()
            raise

    async def upload_file(self, file_path):
        logger.info(f"Uploading file: {file_path}")
        try:
            await self.wait_for_page_load()
            
            file_input_selector = "input[type='file']"
            await self.page.wait_for_selector(file_input_selector, state="attached", timeout=self.timeout)
            
            file_input = await self.page.query_selector(file_input_selector)
            if file_input:
                await file_input.set_input_files(file_path)
                logger.debug("Set file input")
                await self.page.wait_for_load_state("networkidle", timeout=self.timeout)
                logger.debug("Waited for network idle after file upload")
                logger.info(f"File uploaded successfully: {file_path}")
            else:
                logger.error("File upload input not found")
                await self.reload_page()
                raise Exception("File upload input not found")
        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout error while uploading file: {e}", exc_info=True)
            await self.reload_page()
            raise
        except Exception as e:
            logger.error(f"An error occurred while uploading file: {e}", exc_info=True)
            await self.reload_page()
            raise        

    async def fetch_conversation_code(self):
        logger.info("Fetching conversation code")
        max_retries = 5
        for attempt in range(max_retries):
            try:
                current_url = self.page.url
                match = re.search(r'/chat/([a-f0-9-]+)', current_url)
                if match:
                    new_chat_code = match.group(1)
                    if new_chat_code != self.chat_code:
                        self.chat_code = new_chat_code
                        logger.info(f"New conversation code fetched: {self.chat_code}")
                    else:
                        logger.debug(f"Conversation code unchanged: {self.chat_code}")
                    return
                else:
                    logger.warning(f"Could not extract conversation code from URL: {current_url}")
                    await asyncio.sleep(1)  # Wait a bit before retrying
            except Exception as e:
                logger.error(f"An error occurred while fetching conversation code: {e}", exc_info=True)
            
        logger.error("Failed to fetch conversation code after multiple attempts")
        self.chat_code = None

    async def send_message(self, message, temperature=1.0, max_tokens=None):
        logger.info(f"Sending message: {message}")
        max_retries = 5
        for attempt in range(max_retries):
            try:
                await self.wait_for_page_load()
            
                input_selector = "div[contenteditable='true']"
                await self.page.wait_for_selector(input_selector, state="visible", timeout=30000)
            
                input_element = await self.page.query_selector(input_selector)
                if input_element:
                    await input_element.evaluate('(element) => element.innerHTML = ""')
                    await self.page.fill(input_selector, message)
                    logger.debug("Filled input with message")
                else:
                    logger.error("Input element not found")
                    raise Exception("Input element not found")
            
                send_button_selector = "button[aria-label='Send Message']"
                await self.page.wait_for_selector(send_button_selector, state="visible", timeout=30000)
                logger.debug("Send button is visible")

                if self.message_count == 0 or not self.chat_code:
                    await self.page.click(send_button_selector)
                    logger.debug("Clicked send button")
                    await self.page.wait_for_load_state("networkidle", timeout=30000)
                    await self.fetch_conversation_code()
                else:
                    await self.page.click(send_button_selector)
                    logger.debug("Clicked send button")
            
                self.message_count += 1
                logger.info("Message sent successfully")
                
                logger.debug("Waiting for 6 seconds before checking for response")
                await asyncio.sleep(6)
                
                # Check for capacity constraint error message
                error_message_selector = "p:text-is('Due to unexpected capacity constraints, Claude is unable to respond to your message. Please try again soon.')"
                try:
                    error_message = await self.page.wait_for_selector(error_message_selector, timeout=5000)
                    if error_message:
                        logger.warning("Capacity constraint error detected. Closing error message and retrying.")
                        close_button_selector = "button[data-radix-toast-announce-exclude]"
                        close_button = await self.page.query_selector(close_button_selector)
                        if close_button:
                            await close_button.click()
                            logger.debug("Closed error message")
                        await asyncio.sleep(5)  # Wait a bit before retrying
                        continue  # Retry sending the message
                except PlaywrightTimeoutError:
                    logger.debug("No capacity constraint error detected. Proceeding to fetch response.")
                
                response = await self.wait_for_response()
                
                # Apply max_tokens if specified
                if max_tokens and isinstance(max_tokens, int):
                    words = response.split()
                    truncated_response = ' '.join(words[:max_tokens])
                    if len(words) > max_tokens:
                        truncated_response += "... [truncated]"
                    return truncated_response
                
                return response

            except PlaywrightError as e:
                logger.error(f"Playwright error in send_message: {str(e)}", exc_info=True)
                if attempt < max_retries - 1:
                    await asyncio.sleep(5)
                else:
                    raise
            except Exception as e:
                logger.error(f"An error occurred while sending message: {e}", exc_info=True)
                await self.reload_page()
                if attempt < max_retries - 1:
                    await asyncio.sleep(5)
                else:
                    raise

        logger.error("All attempts to send message failed")
        return None

    async def wait_for_response(self):
        logger.info("Waiting for Claude's response")
        max_retries = 60
        retry_interval = 2

        for attempt in range(max_retries):
            logger.debug(f"Attempt {attempt + 1} of {max_retries} to fetch response")
            conversation_data = await self.fetch_conversation_data()
            if conversation_data:
                chat_messages = conversation_data.get('chat_messages', [])
                logger.debug(f"Retrieved {len(chat_messages)} chat messages")
                new_messages = [msg for msg in chat_messages if msg['index'] > self.last_message_index]
                logger.debug(f"Found {len(new_messages)} new messages")
                
                if new_messages:
                    latest_message = new_messages[-1]
                    
                    logger.debug(f"Latest message index: {latest_message['index']}")
                    
                    if latest_message['sender'] == 'assistant':
                        self.last_message_index = latest_message['index']
                        logger.info("Response received")
                        logger.debug(f"Response content: {latest_message['text'][:100]}...")  # Log first 100 chars
                        return latest_message['text']
                
            logger.debug(f"No response yet, waiting for {retry_interval} seconds")
            await asyncio.sleep(retry_interval)

        logger.warning("Timeout waiting for Claude's response")
        return None

    async def fetch_conversation_data(self):
        logger.debug("Fetching conversation data")
        if not self.chat_code:
            logger.warning("No chat code available. Fetching conversation code first.")
            await self.fetch_conversation_code()
            if not self.chat_code:
                logger.error("Failed to fetch conversation code.")
                return None

        target_url = f"{self.api_base_url}/api/organizations/{self.organization_id}/chat_conversations/{self.chat_code}?tree=True&rendering_mode=raw"
        logger.debug(f"Target URL: {target_url}")
        
        try:
            logger.debug("Switching to data fetching page")
            await self.data_page.bring_to_front()
            
            logger.debug("Navigating to conversation data URL")
            response = await self.data_page.goto(target_url, wait_until="networkidle", timeout=30000)
            logger.debug(f"Response status: {response.status}")
            content = await response.text()
            logger.debug(f"Response content length: {len(content)} characters")
            data = json.loads(content)
            logger.debug(f"Parsed JSON data with {len(data.get('chat_messages', []))} messages")
            
            logger.debug("Switching back to chat page")
            await self.page.bring_to_front()
            
            return data
        except Exception as e:
            logger.error(f"An error occurred while fetching conversation data: {e}", exc_info=True)
            return None

    async def get_all_conversations(self):
        logger.info("Fetching all conversations")
        target_url = f"{self.api_base_url}/api/organizations/{self.organization_id}/chat_conversations"
        logger.debug(f"Target URL for all conversations: {target_url}")
        
        try:
            logger.debug("Switching to data fetching page")
            await self.data_page.bring_to_front()
            
            logger.debug("Navigating to all conversations URL")
            response = await self.data_page.goto(target_url, wait_until="networkidle", timeout=30000)
            logger.debug(f"Response status: {response.status}")
            content = await response.text()
            logger.debug(f"Response content length: {len(content)} characters")
            data = json.loads(content)
            logger.debug(f"Parsed JSON data with {len(data)} conversations")
            
            logger.debug("Switching back to chat page")
            await self.page.bring_to_front()
            
            return data
        except Exception as e:
            logger.error(f"An error occurred while fetching all conversations: {e}", exc_info=True)
            return None

    async def set_model(self, model_name):
        logger.info(f"Setting model to: {model_name}")
        try:
            await self.wait_for_page_load()
            
            model_selector = "button[data-testid='model-selector-dropdown']"
            await self.page.click(model_selector)
            logger.debug("Clicked model selector dropdown")

            dropdown_selector = "div[role='menu']"
            await self.page.wait_for_selector(dropdown_selector, state="visible", timeout=self.timeout)
            logger.debug("Model dropdown is visible")

            model_option = f"div[role='menuitem'] div.flex-1:text-is('{model_name}')"
            await self.page.click(model_option)
            logger.debug(f"Selected model: {model_name}")

            await self.page.wait_for_selector(dropdown_selector, state="hidden", timeout=self.timeout)
            logger.debug("Model dropdown has closed")

            await self.page.wait_for_load_state("networkidle", timeout=self.timeout)
            logger.debug("Waited for network idle after model selection")
            self.current_model = model_name
            logger.info(f"Model set to: {model_name}")
            
            # Reset conversation-related variables
            self.message_count = 0
            self.last_message_index = -1
            self.chat_code = None

            logger.info(f"Model set to: {model_name} and new conversation started")
        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout error while setting model: {e}", exc_info=True)
            await self.reload_page()
            raise
        except Exception as e:
            logger.error(f"An error occurred while setting model: {e}", exc_info=True)
            await self.reload_page()
            raise

    async def close(self):
        logger.info("Closing UnofficialClaudeAPI instance")
        try:
            if self.page:
                await self.page.close()
                logger.debug("Chat page closed")
            if self.data_page:
                await self.data_page.close()
                logger.debug("Data fetching page closed")
            if self.playwright:
                await self.playwright.stop()
                logger.debug("Playwright stopped")
        except Exception as e:
            logger.error(f"An error occurred while closing: {e}", exc_info=True)
        finally:
            logger.info("UnofficialClaudeAPI instance closed")

    async def health_check(self):
        logger.info("Performing health check")
        try:
            await self.page.goto(self.base_url, timeout=self.timeout)
            await self.wait_for_page_load()
        
            selectors = [
                "div[contenteditable='true']",
                "button[data-testid='model-selector-dropdown']"
            ]
        
            for selector in selectors:
                if not await self.page.query_selector(selector):
                    logger.error(f"Health check failed: {selector} not found")
                    return False
        
            input_selector = "div[contenteditable='true']"
            await self.page.fill(input_selector, "Test message")
        
            send_button_selector = "button[aria-label='Send Message']"
            try:
                await self.page.wait_for_selector(send_button_selector, state="visible", timeout=5000)
            except PlaywrightTimeoutError:
                logger.error(f"Health check failed: {send_button_selector} not found after typing")
                return False
        
            await self.page.evaluate("document.querySelector('div[contenteditable=\"true\"]').innerHTML = ''")
        
            logger.info("Health check passed")
            return True
        except Exception as e:
            logger.error(f"Health check failed: {e}", exc_info=True)
            return False