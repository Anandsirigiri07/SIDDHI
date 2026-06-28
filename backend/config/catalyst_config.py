# backend/config/catalyst_config.py
import os

USE_CATALYST = os.getenv("USE_CATALYST", "false").lower() == "true"
USE_SMARTBROWZ = os.getenv("USE_SMARTBROWZ", "false").lower() == "true"
USE_STRATUS = os.getenv("USE_STRATUS", "false").lower() == "true"
USE_LOCAL_FALLBACK = os.getenv("USE_LOCAL_FALLBACK", "true").lower() == "true"

# Catalyst Project Environment Keys
CATALYST_PROJECT_ID = os.getenv("CATALYST_PROJECT_ID", "")
CATALYST_PROJECT_NAME = os.getenv("CATALYST_PROJECT_NAME", "")
CATALYST_ENVIRONMENT = os.getenv("CATALYST_ENVIRONMENT", "Development")
