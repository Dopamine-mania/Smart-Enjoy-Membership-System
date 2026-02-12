"""Data masking utilities for sensitive information."""
from typing import Optional


def mask_email(email: Optional[str]) -> Optional[str]:
    """
    Mask email address.

    Example: "abc@example.com" -> "abc***@example.com"

    Args:
        email: Email address to mask

    Returns:
        Masked email or None if email is None
    """
    if not email:
        return None

    parts = email.split("@")
    if len(parts) != 2:
        return email

    local, domain = parts
    if len(local) <= 3:
        masked_local = local + "***"
    else:
        masked_local = local[:3] + "***"

    return f"{masked_local}@{domain}"


def mask_phone(phone: Optional[str]) -> Optional[str]:
    """
    Mask phone number, showing only first 3 and last 4 digits.

    Example: "13812345678" -> "138****5678"

    Args:
        phone: Phone number to mask

    Returns:
        Masked phone or None if phone is None
    """
    if not phone:
        return None

    if len(phone) < 7:
        return "***"

    return phone[:3] + "****" + phone[-4:]
