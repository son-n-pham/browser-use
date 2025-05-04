# browser-use

## Current Implementation

The current implementation consists of a single `refactor/main.py` file that handles:

- Browser configuration and initialization
- Cookie management
- Signal handling
- LLM integration (using Gemini via ChatGoogleGenerativeAI)
- Task execution

```python
# Overview of main.py:
# - Loads environment variables (API keys, paths, etc.)
# - Configures the SSL certificate paths
# - Initializes browser settings including headless mode, security options, and extra Chromium arguments
# - Loads saved cookies for authentication from a specified JSON file
# - Initializes an LLM agent to execute a browser-based task
# - Implements graceful shutdown using signal handling (SIGINT, SIGTERM)
```

### Current Limitations

1. All functionality is packed into a single file, making maintenance and future extensions difficult.
2. Cookie management is basic and limited to a specific domain.
3. Browser and authentication logic are not modularized.
4. Error handling and recovery strategies are minimal.
5. Configuration is scattered throughout the code rather than centralized.

## Refactoring Plan

### Phase 1: Enhanced Project Structure Setup

- **Goal:** Modularize the project with interfaces for component isolation.
- **New Directory Structure:**
  ```
  project/
  ├── main.py
  ├── config/
  │   ├── __init__.py
  │   ├── interfaces.py          # NEW: Configuration protocols
  │   ├── browser_config.py      # Browser and context configurations
  │   ├── settings.py            # API keys, paths, environment variables
  │   └── env_loader.py          # NEW: Environment variable loading
  ├── auth/
  │   ├── __init__.py
  │   ├── interfaces.py          # NEW: Authentication protocols
  │   ├── cookie_manager.py      # Cookie handling
  │   └── auth_handler.py        # Authentication logic
  ├── browser/
  │   ├── __init__.py
  │   ├── interfaces.py          # NEW: Browser operation protocols
  │   ├── browser_controller.py  # Browser operations and control
  │   └── commands.py            # NEW: Command pattern implementations
  ├── llm/                       # NEW: LLM integration module
  │   ├── __init__.py
  │   ├── interfaces.py          # NEW: LLM client protocols
  │   ├── model_client.py        # Client for LLM API calls
  │   └── task_executor.py       # LLM task execution logic
  └── utils/
      ├── __init__.py
      ├── dependency.py          # NEW: Dependency injection system
      ├── signal_handlers.py     # Signal handling utilities
      ├── logging.py            # NEW: Centralized logging
      └── errors.py             # NEW: Error management
  ```

### Phase 2: Core Infrastructure (High Priority)

- **Objective:** Establish foundational services for dependency management, logging, and error handling.
- **Tasks:**

  1. **Dependency Injection System (`utils/dependency.py`):**

     ```python
     class DependencyContainer:
         _instance = None

         @classmethod
         def get_instance(cls):
             if cls._instance is None:
                 cls._instance = cls()
             return cls._instance

         def __init__(self):
             self._services = {}

         def register(self, interface, implementation):
             self._services[interface] = implementation

         def resolve(self, interface):
             if interface not in self._services:
                 raise KeyError(f"No implementation registered for {interface}")
             return self._services[interface]
     ```

  2. **Error Management (`utils/errors.py`):**

     ```python
     class BrowserUseError(Exception):
         """Base exception for all application errors"""
         pass

     class ConfigurationError(BrowserUseError):
         """Raised when configuration is invalid or missing"""
         pass

     class AuthenticationError(BrowserUseError):
         """Raised when authentication fails"""
         pass

     class BrowserOperationError(BrowserUseError):
         """Raised when browser operations fail"""
         pass
     ```

  3. **Logging System (`utils/logging.py`):**

     ```python
     import logging
     import os
     from pathlib import Path

     def configure_logging(log_level=None, log_file=None):
         """Configure application-wide logging"""
         if log_level is None:
             log_level = os.environ.get("LOG_LEVEL", "INFO")

         if log_file is None:
             logs_dir = Path("./logs")
             logs_dir.mkdir(exist_ok=True)
             log_file = logs_dir / "browser_use.log"

         logging.basicConfig(
             level=getattr(logging, log_level),
             format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
             handlers=[
                 logging.FileHandler(log_file),
                 logging.StreamHandler()
             ]
         )

         return logging.getLogger("browser-use")
     ```

### Phase 3: Configuration Management (High Priority)

- **Objective:** Centralize configurations to facilitate easy changes and support multiple environments.
- **Tasks:**

  1. **Browser Configuration (`config/browser_config.py`):**

     ```python
     from pydantic import BaseModel

     class BrowserSettings(BaseModel):
         headless: bool
         disable_security: bool
         chrome_path: str
         extra_args: list[str]
     ```

  2. **Environment Settings (`config/settings.py`):**

     ```python
     from pathlib import Path

     class Settings:
         GEMINI_API_KEY: str
         COOKIES_DIR: Path
         SSL_CERT_PATH: str
     ```

### Phase 4: Building the Authentication System (High Priority)

- **Objective:** Decouple cookie management and authentication from browser control.
- **Tasks:**

  1. **Cookie Manager (`auth/cookie_manager.py`):**

     ```python
     class CookieManager:
         async def load_cookies(self, domain: str):
             # Load and validate cookies for the domain
             pass

         async def save_cookies(self, domain: str, cookies: dict):
             # Securely save cookies for future use
             pass

         async def has_valid_cookies(self, domain: str) -> bool:
             # Check cookie validity
             pass
     ```

  2. **Authentication Handler (`auth/auth_handler.py`):**

     ```python
     class AuthenticationHandler:
         async def ensure_authenticated(self, url: str):
             # Check if cookies exist and are valid:
             #  - Load cookies using CookieManager
             #  - If valid, set cookies in the browser session
             # Otherwise, trigger a login flow and save new cookies
             pass

         async def handle_login(self, url: str):
             # Perform login steps for the given URL
             pass
     ```

### Phase 5: Modularizing Browser Control (Medium Priority)

- **Objective:** Simplify browser operations and encapsulate navigation, interactions, and state management.
- **Tasks:**

  1. **Browser Controller (`browser/browser_controller.py`):**

     ```python
     class BrowserController:
         async def navigate(self, url: str):
             # Navigate to the specified URL
             pass

         async def wait_for_login(self):
             # Wait and detect if login is needed
             pass

         async def capture_state(self):
             # Capture and log the current state or content of the page
             pass
     ```

### Phase 6: Utility Functions and Helpers (Low Priority)

- **Objective:** Enhance the maintainability by centralizing utilities.
- **Tasks:**

  1. **Signal Handling (`utils/signal_handlers.py`):**

     ```python
     class SignalHandler:
         def setup_handlers():
             # Setup signal handlers for SIGINT, SIGTERM, etc.
             pass

         async def handle_shutdown():
             # Gracefully shutdown the browser and cleanup resources
             pass
     ```

### Phase 7: Main Application Flow (Medium Priority)

- **Objective:** Integrate all components into a cohesive executable.
- **Tasks:** Refactor `main.py` to:
  - Initialize configuration using the new modules.
  - Set up the Browser Controller and Authentication Handler.
  - Listen for user commands and handle tasks.
  - Implement proper error handling and logging.
  - Use utility functions (e.g., signal handling for graceful shutdown).

### Phase 8: Testing and Documentation (Low Priority)

- **Objective:** Ensure reliability and ease future development.
- **Tasks:**
  1. Write unit tests for each module.
  2. Develop integration tests for the overall workflow.
  3. Update documentation with usage examples and module specifics.
  4. Ensure code follows PEP 8 and includes adequate error handling.

## Implementation Order

1. **Project Structure Setup (Phase 1)**
   - Create the directory structure.
   - Move and split the existing code into initial modules.
2. **Core Infrastructure (Phase 2)**
   - Implement dependency management, logging, and error handling.
3. **Configuration Management (Phase 3)**
   - Implement browser and environment settings.
4. **Authentication System (Phase 4)**
   - Develop cookie management and authentication handlers.
5. **Browser Control (Phase 5)**
   - Refactor browser operations into a dedicated controller.
6. **Main Application Flow (Phase 7)**
   - Integrate all components and manage the application lifecycle.
7. **Utilities and Helpers (Phase 6)**
   - Centralize signal handling and logging.
8. **Testing and Documentation (Phase 8)**
   - Develop tests and refine documentation.

## Next Steps

- Start by setting up the new directory structure and moving the current code into the respective modules.
- Begin with configuration management to centralize settings.
- Implement the cookie management system and authentication handler.
- Gradually refactor browser controls.
- Continuously test and document each phase.

## Development Guidelines

1. Follow the PEP 8 style guide.
2. Utilize type hints and docstrings to ensure code clarity.
3. Include robust error handling and logging in every module.
4. Write comprehensive tests to validate functionality.
5. Update documentation with every change.
6. Ensure modular design to allow isolated testing and future extensions.
