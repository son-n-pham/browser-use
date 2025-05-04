# Phase 3: Configuration Management

## Objective

Centralize configurations to facilitate easy changes and support multiple environments.

## High Priority Tasks

### 1. Browser Configuration (`config/browser_config.py`)

```python
from pydantic import BaseModel

class BrowserSettings(BaseModel):
    headless: bool
    disable_security: bool
    chrome_path: str
    extra_args: list[str]
```

### 2. Environment Settings (`config/settings.py`)

```python
from pathlib import Path

class Settings:
    GEMINI_API_KEY: str
    COOKIES_DIR: Path
    SSL_CERT_PATH: str
```

## Implementation Steps

1. Install pydantic if not already present
2. Create the configuration classes
3. Add validation and type checking
4. Implement environment variable loading
5. Add configuration file support
