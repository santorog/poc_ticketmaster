import os
import json
import logging

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "culturai.log")


class PrettyJsonFormatter(logging.Formatter):
    """Formatter that pretty-prints dicts/lists found in log messages."""

    def format(self, record):
        # Format any 'json_data' extra as indented JSON
        if hasattr(record, "json_data"):
            try:
                pretty = json.dumps(record.json_data, indent=2, ensure_ascii=False, default=str)
                record.msg = f"{record.msg}\n{pretty}"
            except (TypeError, ValueError):
                pass
        return super().format(record)


def setup_logging(console_level=logging.WARNING):
    """Configure logging: detailed file + quiet console."""
    os.makedirs(LOG_DIR, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Remove existing handlers (avoid duplicates on re-init)
    root.handlers.clear()

    # File handler — DEBUG level, detailed
    file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_formatter = PrettyJsonFormatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)
    root.addHandler(file_handler)

    # Console handler — WARNING+ only (keeps CLI clean)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    root.addHandler(console_handler)

    # Quiet noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

    logging.getLogger("culturai").info("=== Nouvelle session CulturAI ===")
