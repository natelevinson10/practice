from loguru import logger

def init_logging():
    log_file_path = "/Users/natelevinson/Desktop/practice/logs/workflow_react.log"
    logger.add(log_file_path, rotation="1 day", 
  retention="7 days", level="DEBUG", mode="w")

def log_startup():
    logger.info("=" * 80)
    logger.info(f"⏰ Start time: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)