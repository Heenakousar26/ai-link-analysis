import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeURLError(ValueError):
    """Raised when a URL is malformed or resolves to a private/internal network (SSRF protection)."""


def validate_public_url(raw_url: str) -> str:
    """
    Validates that a URL uses http/https, has a valid public hostname,
    and does not resolve to a loopback, private, link-local, or reserved IP address.
    """
    cleaned = raw_url.strip()
    if not cleaned:
        raise UnsafeURLError("URL cannot be empty.")

    # Auto-prepend https:// if user omitted scheme, then parse
    if not cleaned.startswith(("http://", "https://")):
        cleaned = f"https://{cleaned}"

    parsed = urlparse(cleaned)

    if parsed.scheme not in ("http", "https"):
        raise UnsafeURLError("Only HTTP and HTTPS schemes are allowed.")

    hostname = parsed.hostname
    if not hostname:
        raise UnsafeURLError("URL must contain a valid hostname.")

    lower_host = hostname.lower()
    if lower_host in ("localhost", "127.0.0.1", "::1", "0.0.0.0") or lower_host.endswith(".local"):
        raise UnsafeURLError("Access to localhost or internal domains is blocked (SSRF protection).")

    # Resolve DNS to verify none of the target IPs are private/internal
    try:
        addr_info = socket.getaddrinfo(hostname, parsed.port or (443 if parsed.scheme == "https" else 80))
    except socket.gaierror as exc:
        raise UnsafeURLError(f"Unable to resolve domain '{hostname}': {exc}")

    for _, _, _, _, sockaddr in addr_info:
        ip_str = sockaddr[0]
        try:
            ip_obj = ipaddress.ip_address(ip_str)
            if (
                ip_obj.is_private
                or ip_obj.is_loopback
                or ip_obj.is_link_local
                or ip_obj.is_multicast
                or ip_obj.is_reserved
                or ip_obj.is_unspecified
            ):
                raise UnsafeURLError(
                    f"Access to private/internal IP address ({ip_str}) is forbidden (SSRF protection)."
                )
        except ValueError:
            raise UnsafeURLError(f"Invalid resolved IP address: {ip_str}")

    return cleaned