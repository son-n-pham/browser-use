import os
import asyncio
import certifi
import json
import signal
import sys
import platform
from browser_use import Agent, BrowserConfig, Browser
from browser_use.browser.context import BrowserContextConfig
from pydantic import SecretStr
from langchain_google_genai import ChatGoogleGenerativeAI

# Get the API key from the environment
api_key = os.environ.get('GEMINI_API_KEY')

# Set SSL certificate path for requests
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# Disable telemetry to avoid SSL certificate verification errors
os.environ['BROWSER_USE_TELEMETRY'] = 'false'

# Path to cookies file
cookies_file = os.path.join(os.path.dirname(
    __file__), 'saved_cookies', 'bakerhughes.kahunaonline.com_cookies.json')

# Context configuration with cookies file path
context_config = BrowserContextConfig(
    cookies_file=cookies_file,  # Set cookies file path here
    disable_security=False,
)

# Basic configuration
config = BrowserConfig(
    headless=False,
    disable_security=False,  # Changed to False for better security
    chrome_instance_path='C:\\Program Files\\Google\\Chrome Dev\\Application\\chrome.exe',
    extra_chromium_args=['--ignore-certificate-errors'],
    new_context_config=context_config  # Pass the context config with cookies file
)

# Configure the browser to connect to your Chrome instance
browser = Browser(
    config=config
)

if api_key is None:
    raise ValueError(
        "API key for GEMINI_API_KEY environment variable is not set.")

# Initialize the model
llm = ChatGoogleGenerativeAI(
    model='gemini-2.0-flash-exp', api_key=SecretStr(api_key)
)


url = "https://bakerhughes.kahunaonline.com/"
# Create agent with the model
agent = Agent(
    task=f"Go to {url}, wait for login if it is, then list what you see in this current page.",
    llm=llm,
    use_vision=True,
    browser=browser
)


async def close_browser():
    """Handle browser closing gracefully"""
    try:
        await browser.close()
        print("Browser closed successfully")
    except Exception as e:
        print(f"Error while closing browser: {e}")
    finally:
        # Force exit to avoid gRPC cleanup issues
        os._exit(0)


# Define a Windows-compatible signal handler
def handle_exit_signal(sig, frame):
    print("\nReceived exit signal. Closing browser...")
    # Schedule the close_browser coroutine to run
    if asyncio.get_event_loop().is_running():
        asyncio.create_task(close_browser())
    else:
        # Force exit if no event loop is running
        os._exit(0)


async def main():
    # Setup signal handlers for graceful shutdown in a platform-compatible way
    if platform.system() != 'Windows':
        # Unix-like systems can use asyncio signal handlers
        for sig in [signal.SIGINT, signal.SIGTERM]:
            loop = asyncio.get_running_loop()
            try:
                loop.add_signal_handler(
                    sig, lambda: asyncio.create_task(close_browser()))
            except NotImplementedError:
                # Fallback to signal.signal if add_signal_handler is not available
                signal.signal(sig, handle_exit_signal)
    else:
        # Windows - use regular signal handlers
        for sig in [signal.SIGINT, signal.SIGTERM]:
            signal.signal(sig, handle_exit_signal)

    try:
        # Log that we're loading cookies
        if os.path.exists(cookies_file):
            print(f"Loading saved cookies for https://bakerhughes.kahunaonline.com/")
        await agent.run()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print('Press Enter to close the browser...')
        # Use a separate task to monitor for Enter key
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, input)
        await close_browser()

if __name__ == '__main__':
    asyncio.run(main())
