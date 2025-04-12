import logging
import sys
from typing import Optional

def setup_logging(
    level: int = logging.INFO,
    format: str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream: Optional[logging.StreamHandler] = None
) -> None:
    """
    Set up basic logging configuration.
    
    Args:
        level: The logging level to use (default: INFO)
        format: The log message format (default: includes timestamp, name, level, and message)
        stream: Optional stream handler to use (default: sys.stderr)
    """
    if stream is None:
        stream = logging.StreamHandler(sys.stderr)
    
    stream.setFormatter(logging.Formatter(format))
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.addHandler(stream)
    
    # Set up specific loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("mcp").setLevel(logging.INFO) 