import json
import os
import uuid
from curl_cffi import requests
import requests as req
import re
import time
import logging
import random
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Client:

    def __init__(self, cookie, model="claude-3-5-sonnet-20240620"):
        self.cookie = cookie
        self.organization_id = os.getenv('ORGANIZATION_ID') 
        self.model = model
        logger.debug(f"Initialized Client with organization_id: {self.organization_id} and model: {self.model}")

    def get_organization_id(self):
        url = "https://claude.ai/api/organizations"
        
        headers = {
            'User-Agent': self.get_random_user_agent(),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Referer': 'https://claude.ai/chats',
            'Content-Type': 'application/json',
            'Origin': 'https://claude.ai',
            'Connection': 'keep-alive',
            'Cookie': f'{self.cookie}'
        }

        try:
            logger.info("Human-like behavior: Fetching organization ID")
            time.sleep(random.uniform(0.5, 1.5))  # Simulate human delay
            response = requests.get(url, headers=headers, impersonate="chrome110")
            res = json.loads(response.text)
            logger.debug(f"API response for organizations: {res}")
            uuid = self.organization_id  # Using the hardcoded value
            logger.debug(f"Returning organization UUID: {uuid}")
            logger.info("Human-like behavior: Retrieved organization ID")
            return uuid
        except Exception as e:
            logger.error(f"Error in get_organization_id: {str(e)}")
            return None

    def get_content_type(self, file_path):
        extension = os.path.splitext(file_path)[-1].lower()
        if extension == '.pdf':
            return 'application/pdf'
        elif extension == '.txt':
            return 'text/plain'
        elif extension == '.csv':
            return 'text/csv'
        else:
            return 'application/octet-stream'

    def list_all_conversations(self):
        url = f"https://claude.ai/api/organizations/{self.organization_id}/chat_conversations"

        headers = {
            'User-Agent': self.get_random_user_agent(),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Referer': 'https://claude.ai/chats',
            'Content-Type': 'application/json',
            'Origin': 'https://claude.ai',
            'Connection': 'keep-alive',
            'Cookie': f'{self.cookie}'
        }

        logger.info("Human-like behavior: Listing conversations")
        time.sleep(random.uniform(1, 2))  # Simulate human delay
        response = requests.get(url, headers=headers, impersonate="chrome110")
        conversations = response.json()

        if response.status_code == 200:
            logger.info(f"Human-like behavior: Retrieved {len(conversations)} conversations")
            return conversations
        else:
            logger.error(f"Error: {response.status_code} - {response.text}")
            return None

    def send_message(self, prompt, conversation_id, attachment=None, timeout=500, max_retries=3):
        logger.info(f"Human-like behavior: Composing message for conversation {conversation_id}")
        url = f"https://api.claude.ai/api/organizations/{self.organization_id}/chat_conversations/{conversation_id}/completion"

        # Simulate human typing speed
        typing_delay = len(prompt) * 0.00005  # 50ms per character
        logger.info(f"Human-like behavior: Typing message (simulated delay: {typing_delay:.2f} seconds)")
        time.sleep(typing_delay)

        payload = json.dumps({
            "prompt": prompt,
            "timezone": "Atlantic/Canary",
            "model": self.model,
            "attachments": [],
            "files": [],
            "rendering_mode": "raw"
        })
        logger.debug(f"Request payload: {payload}")

        headers = {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/event-stream, text/event-stream',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Referer': 'https://claude.ai/',
            'Content-Type': 'application/json',
            'Origin': 'https://claude.ai',
            'Cookie': f'{self.cookie}'
        }
        logger.debug(f"Request headers: {headers}")

        for attempt in range(max_retries):
            try:
                logger.info(f"Human-like behavior: Sending message (Attempt {attempt + 1}/{max_retries})")
                response = requests.post(url, headers=headers, data=payload, impersonate="chrome110", timeout=timeout)
                logger.info(f"Received response with status code: {response.status_code}")
                logger.debug(f"Response headers: {response.headers}")
                logger.debug(f"Raw response content: {response.content}")

                if response.status_code != 200:
                    logger.error(f"Received non-200 status code: {response.status_code}")
                    if attempt < max_retries - 1:
                        retry_delay = random.uniform(1, 3)
                        logger.warning(f"Human-like behavior: Retrying in {retry_delay:.2f} seconds...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        return f"Error: Received status code {response.status_code} after {max_retries} attempts"

                decoded_data = response.content.decode("utf-8")
                logger.debug(f"Decoded response data: {decoded_data}")

                completions = []
                for line in decoded_data.split('\n'):
                    if line.startswith('data: '):
                        try:
                            data = json.loads(line[6:])
                            if data['type'] == 'completion' and 'completion' in data:
                                completions.append(data['completion'])
                                logger.debug(f"Added completion: {data['completion']}")
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse JSON: {line[6:]}")

                answer = ''.join(completions)
                logger.info(f"Human-like behavior: Received answer (length: {len(answer)})")
                
                # Simulate human reading time
                reading_time = len(answer) * 0.005  # 10ms per character
                logger.info(f"Human-like behavior: Reading response (simulated delay: {reading_time:.2f} seconds)")
                time.sleep(reading_time)
                
                logger.debug(f"Final answer: {answer}")
                return answer

            except requests.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                if attempt < max_retries - 1:
                    retry_delay = random.uniform(1, 3)
                    logger.warning(f"Human-like behavior: Retrying in {retry_delay:.2f} seconds...")
                    time.sleep(retry_delay)
                else:
                    return f"Error: Request failed after {max_retries} attempts - {str(e)}"

        logger.error("Failed to get a valid response after all retries")
        return "Error: Failed to get a valid response from the API"

    def delete_conversation(self, conversation_id):
        url = f"https://claude.ai/api/organizations/{self.organization_id}/chat_conversations/{conversation_id}"

        payload = json.dumps(f"{conversation_id}")
        headers = {
            'User-Agent': self.get_random_user_agent(),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Content-Type': 'application/json',
            'Referer': 'https://claude.ai/chats',
            'Origin': 'https://claude.ai',
            'Connection': 'keep-alive',
            'Cookie': f'{self.cookie}'
        }

        logger.info(f"Human-like behavior: Deleting conversation {conversation_id}")
        time.sleep(random.uniform(0.5, 1.5))  # Simulate human delay
        response = requests.delete(url, headers=headers, data=payload, impersonate="chrome110")

        if response.status_code == 204:
            logger.info(f"Human-like behavior: Successfully deleted conversation {conversation_id}")
        else:
            logger.error(f"Failed to delete conversation {conversation_id}")

        return response.status_code == 204

    def chat_conversation_history(self, conversation_id):
        url = f"https://claude.ai/api/organizations/{self.organization_id}/chat_conversations/{conversation_id}"

        headers = {
            'User-Agent': self.get_random_user_agent(),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Referer': 'https://claude.ai/chats',
            'Content-Type': 'application/json',
            'Origin': 'https://claude.ai',
            'Connection': 'keep-alive',
            'Cookie': f'{self.cookie}'
        }

        logger.info(f"Human-like behavior: Fetching conversation history for {conversation_id}")
        time.sleep(random.uniform(0.8, 1.8))  # Simulate human delay
        response = requests.get(url, headers=headers, impersonate="chrome110")
        logger.info(f"Human-like behavior: Retrieved conversation history")
        return response.json()

    def generate_uuid(self):
        random_uuid = uuid.uuid4()
        random_uuid_str = str(random_uuid)
        formatted_uuid = f"{random_uuid_str[0:8]}-{random_uuid_str[9:13]}-{random_uuid_str[14:18]}-{random_uuid_str[19:23]}-{random_uuid_str[24:]}"
        return formatted_uuid

    def create_new_chat(self):
        url = f"https://api.claude.ai/api/organizations/{self.organization_id}/chat_conversations"
        uuid = self.generate_uuid()
        
        payload = json.dumps({
            "uuid": uuid,
            "name": "",
            "model": self.model
        })
        headers = {
            'User-Agent': self.get_random_user_agent(),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Content-Type': 'application/json',
            'Origin': 'https://claude.ai',
            'Referer': 'https://claude.ai/',
            'Connection': 'keep-alive',
            'Cookie': self.cookie
        }

        try:
            logger.info("Human-like behavior: Creating new chat")
            time.sleep(random.uniform(0.5, 1.5))  # Simulate human delay
            response = requests.post(url, headers=headers, data=payload, impersonate="chrome110")
            logger.debug(f"Create new chat response status: {response.status_code}")
            logger.debug(f"Create new chat response content: {response.text}")
            logger.info("Human-like behavior: New chat created successfully")
            return response.json()
        except Exception as e:
            logger.error(f"Error in create_new_chat: {str(e)}")
            return None

    def reset_all(self):
        conversations = self.list_all_conversations()
        if conversations:
            logger.info(f"Human-like behavior: Resetting all conversations")
            for conversation in conversations:
                conversation_id = conversation['uuid']
                self.delete_conversation(conversation_id)
                time.sleep(random.uniform(0.3, 0.7))  # Simulate human delay between deletions
            logger.info("Human-like behavior: All conversations reset")
            return True
        logger.info("Human-like behavior: No conversations to reset")
        return False

    def upload_attachment(self, file_path):
        logger.info(f"Human-like behavior: Preparing to upload attachment {file_path}")
        if file_path.endswith('.txt'):
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            file_type = "text/plain"
            with open(file_path, 'r', encoding='utf-8') as file:
                file_content = file.read()

            logger.info(f"Human-like behavior: Uploaded text file {file_name}")
            return {
                "file_name": file_name,
                "file_type": file_type,
                "file_size": file_size,
                "extracted_content": file_content
            }
        url = 'https://claude.ai/api/convert_document'
        headers = {
            'User-Agent': self.get_random_user_agent(),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Referer': 'https://claude.ai/chats',
            'Origin': 'https://claude.ai',
            'Connection': 'keep-alive',
            'Cookie': f'{self.cookie}'
        }

        file_name = os.path.basename(file_path)
        content_type = self.get_content_type(file_path)

        files = {
            'file': (file_name, open(file_path, 'rb'), content_type),
            'orgUuid': (None, self.organization_id)
        }

        logger.info(f"Human-like behavior: Uploading file {file_name}")
        time.sleep(random.uniform(1, 3))  # Simulate human delay for file upload
        response = req.post(url, headers=headers, files=files)
        if response.status_code == 200:
            logger.info(f"Human-like behavior: Successfully uploaded file {file_name}")
            return response.json()
        else:
            logger.error(f"Failed to upload file {file_name}")
            return False

    def rename_chat(self, title, conversation_id):
        url = "https://claude.ai/api/rename_chat"

        payload = json.dumps({
            "organization_uuid": f"{self.organization_id}",
            "conversation_uuid": f"{conversation_id}",
            "title": f"{title}"
        })
        headers = {
            'User-Agent': self.get_random_user_agent(),
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
            'Content-Type': 'application/json',
            'Referer': 'https://claude.ai/chats',
            'Origin': 'https://claude.ai',
            'Connection': 'keep-alive',
            'Cookie': f'{self.cookie}'
        }

        logger.info(f"Human-like behavior: Renaming conversation {conversation_id} to '{title}'")
        time.sleep(random.uniform(0.5, 1.5))  # Simulate human delay
        response = requests.post(url, headers=headers, data=payload, impersonate="chrome110")

        if response.status_code == 200:
            logger.info(f"Human-like behavior: Successfully renamed conversation to '{title}'")
        else:
            logger.error(f"Failed to rename conversation {conversation_id}")

        return response.status_code == 200

    def get_random_user_agent(self):
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Mobile/15E148 Safari/604.1'
        ]
        return random.choice(user_agents)

    def get_available_models(self):
        # This is a placeholder method. In a real implementation, you would fetch this from the API.
        # For now, we'll return a list of known Claude models.
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3-5-sonnet-20240620",
            "claude-2.1",
            "claude-2.0"
        ]

    def set_model(self, model):
        available_models = self.get_available_models()
        if model in available_models:
            self.model = model
            logger.info(f"Model set to: {self.model}")
        else:
            logger.error(f"Invalid model: {model}. Available models are: {', '.join(available_models)}")
            raise ValueError(f"Invalid model: {model}")

    def get_current_model(self):
        return self.model

# End of Client class

# You might want to add some utility functions or additional classes here if needed
