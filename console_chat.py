import os
import logging
from claude_api import Client

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_cookie():
    cookie = "__stripe_mid=e9153cd4-5011-4cbd-af18-87e7e863b0620764fe; _gcl_au=1.1.1106054366.1718907813; _fbp=fb.1.1718907813879.324036528159443754; __ssid=1392ae80aa353d71067177c732b7aaa; intercom-device-id-lupk8zyo=9ed36bd1-07cd-4a87-a93f-e15210017630; lastActiveOrg=05719259-a917-4a27-a78e-56ec78cc9b93; _rdt_uuid=1711054816455.57490846-04aa-4c80-9cd7-3abed8a61969; activitySessionId=b246c6e6-01f5-45c7-a29e-30d163c6f41f; sessionKey=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; cf_clearance=3qzsAaPRt9240e6QaOEJSRjRz_WzoBD3LDt6RMXYDtY-1723390181-1.0.1.1-vV6jrejGnvKqgjyEw4CRzkL9pJP0L0GSbz_4ZnkaJ25b7jvqgHZYf8_LsGglZPPLvitkfcPWowdggNp5KuSTrQ; CH-prefers-color-scheme=light; intercom-session-lupk8zyo=YlVuc0R0RGx1SFE2a05aeGZ0My9Lclk2Z05UcjhGSUZsWnk0WnZsVWxxdUVvd3JUNHFKdlI2c0NmS1pJbEJ5Ky0tWVRKdlF2cTd4WEE4Ym1oMWdrREkrdz09--23b3446be06fe3b578cc20e077b0620c51af0baa; __cf_bm=76M5FTh3sf5uPGSm0ur.AcXf7D838q7gmcqa4vY2.ao-1723391981-1.0.1.1-S2Wo_fRN0PnNS_5LqVUUgvSaCjmATg7hecgCmKiLjmlYmU53_zDH3stCOGeEjh7MhXlsoyLOR7dDyLJUBv3pgg"
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