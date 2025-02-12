from urllib.parse import urlparse
from pathlib import Path
import json
import asyncio
import certifi
import os
from browser_use import Agent, Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig, BrowserContext
from pydantic import SecretStr
from langchain_google_genai import ChatGoogleGenerativeAI

# Define cookies directory and file structure
COOKIES_DIR = Path("saved_cookies")
COOKIES_DIR.mkdir(exist_ok=True)

# Get the API key from the environment
api_key = os.environ.get('GEMINI_API_KEY')

# Set SSL certificate path for requests
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# Disable telemetry to avoid SSL certificate verification errors
os.environ['BROWSER_USE_TELEMETRY'] = 'false'
# NOTE: Disabling telemetry might not fully prevent SSL errors.
# Consider configuring your system to trust the necessary certificates for eu.i.posthog.com,
# or (less securely) disabling SSL verification for the telemetry service.

# Initialize the model
llm = ChatGoogleGenerativeAI(
    model='gemini-2.0-flash-exp', api_key=SecretStr(api_key)
)


class CookieManager:
    def __init__(self):
        self.cookies_dir = COOKIES_DIR

    def get_cookie_file(self, url):
        """Get cookie file path for a specific domain"""
        domain = urlparse(url).netloc
        return self.cookies_dir / f"{domain}_cookies.json"

    def save_cookies(self, url, cookies):
        """Save cookies for a specific domain"""
        cookie_file = self.get_cookie_file(url)
        with open(cookie_file, 'w') as f:
            json.dump(cookies, f)

    def load_cookies(self, url):
        """Load cookies for a specific domain"""
        cookie_file = self.get_cookie_file(url)
        if cookie_file.exists():
            with open(cookie_file, 'r') as f:
                return json.load(f)
        return None


# Initialize cookie manager
cookie_manager = CookieManager()

# Basic configuration
config = BrowserConfig(
    headless=False,
    disable_security=False,
    chrome_instance_path='C:\\Program Files\\Google\\Chrome Dev\\Application\\chrome.exe',
    extra_chromium_args=['--ignore-certificate-errors']
)

# Create browser instance first
browser = Browser(config=config)


async def create_context_for_url(url):
    """Create browser context with appropriate cookies for URL"""
    cookie_file = cookie_manager.get_cookie_file(url)
    # Create basic context first
    context = await browser.new_context()
    # Tag the context with the URL so we can find it later
    context.url = url

    # Load cookies if they exist
    if Path(cookie_file).exists():
        cookies = cookie_manager.load_cookies(url)
        if cookies:
            await context.add_cookies(cookies)

    return context


async def check_authentication(agent, url):
    """Check if we have valid cookies for the specific URL"""
    try:
        cookies = cookie_manager.load_cookies(url)
        if not cookies:
            return False

        # Try to access authenticated content
        result = await agent.run(f"Check if we're logged in to {url}")
        return True
    except Exception:
        return False


async def handle_authentication(agent, url):
    """Handle authentication for specific URL"""
    try:
        print(f"Authentication required for {url}. Please log in manually...")
        agent.pause()
        input("Press Enter after you've completed the login...")

        # Retrieve the context associated with the URL.
        # We attached the URL to the context in create_context_for_url.
        context = next(
            (c for c in agent.browser._contexts if getattr(c, 'url', None) == url), None)
        if not context:
            print(f"Could not find context for URL: {url}")
            return False

        cookies = await context.cookies()
        cookie_manager.save_cookies(url, cookies)

        agent.resume()
        return True
    except Exception as e:
        print(f"Authentication error: {e}")
        return False


async def main():
    # Example URL to work with
    target_url = "https://google.com"  # Replace with your target URL

    try:
        # Create context for specific URL and tag it with the URL
        await create_context_for_url(target_url)

        # Initialize agent with the browser instance
        agent = Agent(
            task=f"Navigate to {target_url} and search for Baker Hughes stock",
            llm=llm,
            use_vision=True,
            browser=browser  # Only pass the browser instance
        )

        # Check authentication
        if not await check_authentication(agent, target_url):
            auth_success = await handle_authentication(agent, target_url)
            if not auth_success:
                print("Could not authenticate. Exiting...")
                return

        # Proceed with main task
        print("Executing main task...")
        await agent.run()

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        input('Press Enter to close the browser...')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
