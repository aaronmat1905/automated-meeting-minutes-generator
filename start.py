"""
Simple launcher script - Run this from anywhere!
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Change to project root directory
os.chdir(project_root)

# Now import and run the app
from src.app_simple import app, logger, config

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))

    logger.info("=" * 60)
    logger.info("Meeting Minutes Generator - Simplified Version")
    logger.info("=" * 60)
    logger.info(f"Starting on http://localhost:{port}")
    logger.info(f"Gemini Configured: {config.GEMINI_API_KEY is not None}")
    logger.info(f"AssemblyAI Configured: {config.ASSEMBLYAI_API_KEY is not None}")
    logger.info("=" * 60)

    app.run(
        host='0.0.0.0',
        port=port,
        debug=config.DEBUG
    )
