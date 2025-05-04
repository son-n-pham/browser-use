import os
import asyncio
import certifi
import json
import signal
import sys
import platform
from dotenv import load_dotenv
from browser_use import Agent, BrowserConfig, Browser
from browser_use.browser.context import BrowserContextConfig
from pydantic import SecretStr
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment
api_key = os.environ.get("GEMINI_API_KEY")
# DO NOT print the API key - security risk removed.

# Set SSL certificate path for requests
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

# Disable telemetry to avoid SSL certificate verification errors
os.environ["BROWSER_USE_TELEMETRY"] = "false"

# --- Configuration from Environment Variables ---
COOKIES_DIR = "saved_cookies"
DEFAULT_COOKIES_FILENAME = "default_cookies.json"
DEFAULT_URL = "https://example.com"
DEFAULT_TASK = "Describe the main content of this page."

# Ensure cookies directory exists
cookies_dir_path = os.path.join(os.path.dirname(__file__), COOKIES_DIR)
os.makedirs(cookies_dir_path, exist_ok=True)

# Path to cookies file from environment or default
cookies_filename = os.environ.get("COOKIES_FILENAME", DEFAULT_COOKIES_FILENAME)
cookies_file = os.path.join(cookies_dir_path, cookies_filename)

# Context configuration with cookies file path
context_config = BrowserContextConfig(
    cookies_file=cookies_file,  # Set cookies file path here
    disable_security=False,
)

# Basic configuration
config = BrowserConfig(
    headless=False,
    disable_security=False,
    chrome_instance_path=os.environ.get(
        "CHROME_PATH"
    ),  # Get Chrome path from env, None lets Playwright find it
    extra_chromium_args=[],  # Start with empty args
    new_context_config=context_config,  # Pass the context config with cookies file
)

# Conditionally add --ignore-certificate-errors based on environment variable
# WARNING: Ignoring certificate errors can be a security risk. Only enable if absolutely necessary.
if os.environ.get("IGNORE_CERT_ERRORS", "false").lower() == "true":
    config.extra_chromium_args.append("--ignore-certificate-errors")

# Configure the browser to connect to your Chrome instance
browser = Browser(config=config)

if api_key is None:
    raise ValueError("API key for GEMINI_API_KEY environment variable is not set.")

# Initialize the model
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", api_key=SecretStr(api_key))


# Get URL and Task from environment variables or use defaults
url = os.environ.get("TARGET_URL", DEFAULT_URL)
task = os.environ.get("AGENT_TASK", DEFAULT_TASK).replace(
    "{url}", url
)  # Allow {url} placeholder in task

# Create agent with the model
agent = Agent(task=task, llm=llm, use_vision=True, browser=browser)


async def close_browser():
    """Handle browser closing gracefully"""
    try:
        await browser.close()
        print("Browser closed successfully")
    except Exception as e:
        print(f"Error while closing browser: {e}")
    finally:
        # Force exit using os._exit(0) to potentially avoid gRPC cleanup issues observed with Playwright/Asyncio.
        # Standard exit (sys.exit or natural loop end) might be preferable if underlying issues are resolved.
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
    if platform.system() != "Windows":
        # Unix-like systems can use asyncio signal handlers
        for sig in [signal.SIGINT, signal.SIGTERM]:
            loop = asyncio.get_running_loop()
            try:
                loop.add_signal_handler(
                    sig, lambda: asyncio.create_task(close_browser())
                )
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
            print(f"Attempting to load cookies from: {cookies_file}")
        else:
            print(f"Cookies file not found, will create if needed: {cookies_file}")
        await agent.run()
    except Exception as e:
        # Consider adding more specific exception handling for browser/agent errors if needed
        print(f"An error occurred during agent execution: {e}")
    finally:
        print("Press Enter to close the browser...")
        # Use a separate task to monitor for Enter key
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, input)
        await close_browser()


if __name__ == "__main__":
    asyncio.run(main())
