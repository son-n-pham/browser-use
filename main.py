import os
import asyncio
import certifi
from browser_use import Agent, BrowserConfig, Browser
from pydantic import SecretStr
from langchain_google_genai import ChatGoogleGenerativeAI

# Get the API key from the environment
api_key = os.environ.get('GEMINI_API_KEY')

# Set SSL certificate path for requests
os.environ['SSL_CERT_FILE'] = certifi.where()
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()

# Disable telemetry to avoid SSL certificate verification errors
os.environ['BROWSER_USE_TELEMETRY'] = 'false'

# Basic configuration
config = BrowserConfig(
    headless=False,
    disable_security=False,  # Changed to False for better security
    chrome_instance_path='C:\\Program Files\\Google\\Chrome Dev\\Application\\chrome.exe',
    extra_chromium_args=['--ignore-certificate-errors']
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

# Create agent with the model
agent = Agent(
    task="Compare the price of gpt-4o and DeepSeek-V3",
    llm=llm,
    use_vision=True,
    browser=browser
)


async def main():
    try:
        await agent.run()
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        input('Press Enter to close the browser...')
        await browser.close()

if __name__ == '__main__':
    asyncio.run(main())
