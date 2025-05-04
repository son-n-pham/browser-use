import os
import asyncio
import certifi
import json
import signal
import sys
import platform
import logging
import warnings

# --- Early Configuration ---
# Disable telemetry BEFORE importing browser_use to prevent initial connection attempts
os.environ["BROWSER_USE_TELEMETRY"] = "false"

# Configure logging to reduce verbosity
logging.getLogger("browser_use").setLevel(logging.WARNING)
logging.getLogger("agent").setLevel(
    logging.WARNING
)  # Specifically target agent logs if needed
logging.getLogger("backoff").setLevel(
    logging.ERROR
)  # Only show errors for backoff attempts
# Optionally set root logger level if other libraries are too noisy
# logging.basicConfig(level=logging.WARNING)

# Filter specific warnings

# --- Third-Party Imports ---
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

# --- Configuration from Environment Variables ---
COOKIES_DIR = "saved_cookies"
DEFAULT_COOKIES_FILENAME = "default_cookies.json"
DEFAULT_URL = "https://example.com"
DEFAULT_TASK_PREFIX = (
    "Navigate to the URL provided and then describe the main content of the page. URL: "
)

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


# Get URL from environment variables or use default
url = os.environ.get("TARGET_URL", DEFAULT_URL)
DEFAULT_TASK = DEFAULT_TASK_PREFIX + url

# Ask user for task preference
print(f"\nThe default task is: '{DEFAULT_TASK}'")  # Updated print statement
use_default = input("Run default task? (Y/n): ").lower().strip()

if use_default == "" or use_default == "y":
    task_input = DEFAULT_TASK
    print("Using default task.")
else:
    # Guide user for custom tasks involving navigation
    task_input = input(
        f"Enter the custom task (e.g., 'Navigate to {url} and then summarize'): "
    )
    print(f"Using custom task: '{task_input}'")


# Create agent with the model
agent = Agent(task=task_input, llm=llm, use_vision=True, browser=browser)


async def close_browser(browser_instance):
    """Handle browser closing gracefully"""
    if browser_instance:
        try:
            print("Attempting to close browser...")
            await browser_instance.close()
            print("Browser closed successfully.")
        except Exception as e:
            print(f"Error while closing browser: {e}")
    else:
        print("Browser instance not available to close.")
    # Let asyncio handle the exit more gracefully, remove os._exit
    # Consider loop.stop() or sys.exit() if needed after main finishes


# Define a Windows-compatible signal handler
# Define a signal handler
def handle_exit_signal(sig, frame):
    print(f"\nReceived signal {sig}. Closing browser...")
    # Schedule the close_browser coroutine to run
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # Pass the global browser instance to the handler
        asyncio.create_task(close_browser(browser))
        # Optionally, tell the loop to stop after the task is done
        # loop.call_soon_threadsafe(loop.stop) # Use if needed
    else:
        print("Event loop not running. Exiting.")
        sys.exit(0)  # Use sys.exit instead of os._exit


async def main():
    # Setup signal handlers for graceful shutdown in a platform-compatible way
    if platform.system() != "Windows":
        # Unix-like systems can use asyncio signal handlers
        for sig in [signal.SIGINT, signal.SIGTERM]:
            loop = asyncio.get_running_loop()
            try:
                loop.add_signal_handler(
                    # Pass the global browser instance to the handler
                    sig,
                    lambda: asyncio.create_task(close_browser(browser)),
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
        print("Agent run finished or encountered an error.")
        # --- Browser Closing Logic ---
        # Option 1: Close immediately without waiting for Enter
        # await close_browser(browser)

        # Option 2: Wait for Enter, then close (as originally intended)
        print("Press Enter to close the browser...")
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, input)  # Wait for Enter
        await close_browser(browser)  # Close after Enter

        # --- Agent Cleanup (Removed) ---
        # No agent.close() method exists based on the error message.
        # Browser closing should handle resource cleanup.

        print("Script finished.")
        # Program exits naturally after main() finishes unless sys.exit was called by signal handler


if __name__ == "__main__":
    asyncio.run(main())
