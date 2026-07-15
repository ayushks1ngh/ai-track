import logging
import os


def setup_logging(verbose: bool = False) -> None:
    """Configure logging. Always logs to file; only streams to stderr when verbose."""
    log_dir = os.path.expanduser("~/.local/share/aitrack/log")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "aitrack.log")

    handlers: list[logging.Handler] = [logging.FileHandler(log_path)]
    if verbose:
        handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )
