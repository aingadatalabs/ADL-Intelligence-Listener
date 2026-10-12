import re
from urllib.parse import urlsplit


def validate_subreddit_url(target: str) -> str:
    """
    Production-hardened validator for Reddit subreddit URLs.
    Prevents SSRF, open redirects, query pollution, and case-mismatch bypasses.
    """
    if not isinstance(target, str) or not target.strip():
        raise ValueError("Target must be a non-empty string URL.")

    try:
        parsed = urlsplit(target)
        port = parsed.port
    except ValueError as exc:
        raise ValueError("Target must be a valid HTTPS Reddit subreddit URL.") from exc

    # Normalize hostname to lowercase to prevent case-mismatch bypasses (e.g., WWW.REDDIT.COM)
    hostname = parsed.hostname.lower() if parsed.hostname else ""

    if (
        parsed.scheme != "https"
        or hostname not in {"reddit.com", "www.reddit.com", "old.reddit.com"}
        or port not in {None, 443}
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or re.fullmatch(r"/r/[A-Za-z0-9_]{1,21}/?", parsed.path) is None
    ):
        raise ValueError("Target must be an HTTPS Reddit subreddit URL.")
        
    return target