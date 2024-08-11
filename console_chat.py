import os
import logging
from claude_api import Client

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_cookie():
    cookie = "__stripe_mid=e9153cd4-5011-4cbd-af18-87e7e863b0620764fe; _gcl_au=1.1.1106054366.1718907813; _fbp=fb.1.1718907813879.324036528159443754; __ssid=1392ae80aa353d71067177c732b7aaa; intercom-device-id-lupk8zyo=9ed36bd1-07cd-4a87-a93f-e15210017630; lastActiveOrg=05719259-a917-4a27-a78e-56ec78cc9b93; _rdt_uuid=1711054816455.57490846-04aa-4c80-9cd7-3abed8a61969; sessionKey=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; CH-prefers-color-scheme=dark; activitySessionId=fefa5509-e15e-4c96-917c-edebfb093525; intercom-session-lupk8zyo=YitKaEpvQ2tYVzZaUmc1TkdreUdlb3dJOGhhK0d4TElnTzEzWFlCZk1qQkhOVzMwcDFFdVhSZ2xBV0tITjluYy0tclpYMXhCd0wzZUxMMmZXTmgxenBoUT09--f8dd73e738a923e55418ee466eb8db2e65e2ae2f; cf_clearance=v4yfJ.FbyyL9DbyHCUp.PWRdYVXT_TCDN4c_qfg3DeQ-1723289344-1.0.1.1-GcWjL1jPhzewemoA00ImP1B4jpwQmqZ.AQYTOXqntWRMOb.ZZbr3nvd_vlhZmREHpiBSTx3Etlxi.4txZS0TiQ; __cf_bm=9tAgxyONmRAiB5Lxy0lgQD5w8fianrV1AKB.twiEbao-1723290534-1.0.1.1-CVFQrHVwgbcNrMjVSedVemjvrsfZZt4OU3GcA2O1CjijWZO4E18ft4UT1vDMUb8po6J.ABjCreMedv56ZS5.QQ"
    if not cookie:
        raise ValueError("Please set the 'cookie' variable.")
    logger.debug(f"Cookie retrieved: {cookie[:20]}...") # Log first 20 chars of cookie
    return cookie

def main():
    try:
        cookie = get_cookie()
        logger.info("Initializing Claude client")
        claude = Client(cookie)
        logger.debug(f"Claude client initialized with organization ID: {claude.organization_id}")
        conversation_id = None

        print("Welcome to Claude AI Chat!")

        while True:
            user_input = input("You: ")

            if user_input.lower() == 'exit':
                print("Thank you!")
                break

            if not conversation_id:
                logger.info("Creating new chat conversation")
                conversation = claude.create_new_chat()
                logger.debug(f"Create new chat response: {conversation}")
                conversation_id = conversation.get('uuid') if conversation else None
                if not conversation_id:
                    logger.error(f"Failed to get conversation UUID. Full response: {conversation}")
                    raise ValueError("Unable to create new conversation")

            logger.info(f"Sending message to conversation {conversation_id}")
            response = claude.send_message(user_input, conversation_id)
            logger.debug(f"Received response: {response[:100]}...") # Log first 100 chars of response
            print("Chatbot:", response)

    except Exception as e:
        logger.exception(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    main()