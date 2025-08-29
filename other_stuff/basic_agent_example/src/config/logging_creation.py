from loguru import logger
from datetime import datetime

def init_logging():
    """Simple logging setup - one file, fresh start each run"""
    log_file_path = "/Users/natelevinson/Desktop/practice/basic_agent_example/logs/run.log"
    
    # Remove default handler and add file handler with mode="w" for fresh start
    logger.remove()
    
    # Add file handler with immediate flushing
    def write_and_flush(message):
        """Custom sink that writes and immediately flushes"""
        with open(log_file_path, 'a') as f:
            f.write(message)
            f.flush()  # Force immediate write to disk
    
    # Clear the file first
    open(log_file_path, 'w').close()
    
    # Add handler with custom sink
    logger.add(write_and_flush,
               format="{time:HH:mm:ss.SSS} | {level:<8} | {message}\n",
               level="DEBUG")

def log_startup():
    """Log session start"""
    logger.info("=" * 80)
    logger.info(f"Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)