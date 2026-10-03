"""Bounded technical checks for one authorized Shopee draft.

These checks prove only that the affiliate URL currently resolves to the exact
product and that the official image URL returns a decodable raster. They never
claim stock or affiliate attribution; both remain false until Shopee evidence is
available from an authorized report.
"""
from __future__ import annotations

import hashlib
import io
import ipaddress
import socket
import time
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urljoin, urlsplit

import httpx
from PIL import Image

from .guardrails import LinkStatus

MAX_IMAGE_BYTES = 8_000_000
REDIRECT_CODES = frozenset((301, 302, 303, 307, 308))


@dataclass(frozen=True)
class TechnicalVerification:
    status: LinkStatus
    destination_product_id: str | None
    destination_matches: bool
    image_valid: bool
    stock_valid: bool
    tracking_verified: bool
    reason: str
    evidence_ref: str
    checked_at: int


def _merchant_host(host: str) -> bool:
    return host == "shope.ee" or host == "shopee.com.br" or host.endswith(".shopee.com.br")


def _image_host(host: str) -> bool:
    return host == "susercontent.com" or host.endswith(".susercontent.com")


def _safe_target(url: str, *, image: bool, resolver: Callable) -> bool:
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower().rstrip(".")
        if (
            parsed.scheme != "https"
            or not host
            or parsed.username
            or parsed.password
            or parsed.port not in (None, 443)
            or not (_image_host(host) if image else _merchant_host(host))
        ):
            return False
        addresses = [ipaddress.ip_address(row[4][0]) for row in resolver(host, None)]
        return bool(addresses) and all(
            not (
                address.is_private
                or address.is_loopback
                or address.is_link_local
                or address.is_multicast
                or address.is_reserved
                or address.is_unspecified
            )
            for address in addresses
        )
    except (OSError, TypeError, ValueError):
        return False


def _product_id(url: str) -> str | None:
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower().rstrip(".")
        parts = [part for part in parsed.path.split("/") if part]
        if (
            parsed.scheme != "https"
            or not (host == "shopee.com.br" or host.endswith(".shopee.com.br"))
            or parsed.username
            or parsed.password
            or len(parts) != 3
            or parts[0] != "product"
            or not parts[1].isdigit()
            or not parts[2].isdigit()
        ):
            return None
        return f"{parts[1]}:{parts[2]}"
    except ValueError:
        return None


def _get_final(client: httpx.Client, url: str, *, image: bool, resolver: Callable):
    current = url
    visited = set()
    for _ in range(5):
        if current in visited or not _safe_target(current, image=image, resolver=resolver):
            raise ValueError("unsafe_or_looping_redirect")
        visited.add(current)
        with client.stream("GET", current) as response:
            if response.status_code in REDIRECT_CODES:
                location = response.headers.get("location")
                if not location:
                    raise ValueError("redirect_without_location")
                current = urljoin(str(response.url), location)
                continue
            if response.status_code != 200 or not _safe_target(
                str(response.url), image=image, resolver=resolver
            ):
                raise ValueError("unexpected_response")
            if not image:
                return str(response.url), None
            content_type = response.headers.get("content-type", "").split(";", 1)[0].lower()
            if content_type not in {"image/jpeg", "image/png", "image/webp", "image/avif"}:
                raise ValueError("unexpected_image_type")
            declared = int(response.headers.get("content-length", "0") or 0)
            if declared > MAX_IMAGE_BYTES:
                raise ValueError("image_too_large")
            raw = bytearray()
            for chunk in response.iter_bytes():
                raw.extend(chunk)
                if len(raw) > MAX_IMAGE_BYTES:
                    raise ValueError("image_too_large")
            raster = Image.open(io.BytesIO(raw))
            raster.verify()
            raster = Image.open(io.BytesIO(raw))
            if raster.width < 200 or raster.height < 200:
                raise ValueError("image_too_small")
            return str(response.url), bytes(raw)
    raise ValueError("too_many_redirects")


def verify_technical_evidence(
    record: dict,
    *,
    client: httpx.Client | None = None,
    resolver: Callable = socket.getaddrinfo,
    now: int | None = None,
) -> TechnicalVerification:
    """Check destination and raster bytes while keeping attribution fail-closed."""
    checked_at = int(time.time()) if now is None else now
    expected = record.get("product_id") if isinstance(record, dict) else None
    owned_client = client is None
    client = client or httpx.Client(
        timeout=httpx.Timeout(15, connect=5),
        follow_redirects=False,
        headers={"User-Agent": "CompraPulse-TechnicalVerifier/1.0"},
    )
    destination_id = None
    destination_matches = False
    image_valid = False
    reason = "technical_check_failed"
    image_digest = "missing"
    try:
        final_url, _ = _get_final(
            client, record["affiliate_url"], image=False, resolver=resolver
        )
        destination_id = _product_id(final_url)
        destination_matches = destination_id == expected
        if not destination_matches:
            reason = "destination_product_mismatch"
        else:
            _, image_bytes = _get_final(
                client, record["image_url"], image=True, resolver=resolver
            )
            image_digest = hashlib.sha256(image_bytes).hexdigest()
            image_valid = True
            reason = "tracking_and_stock_unconfirmed"
    except (httpx.HTTPError, KeyError, OSError, TypeError, ValueError):
        pass
    finally:
        if owned_client:
            client.close()
    identity = f"{expected}|{destination_id}|{image_digest}|{checked_at}".encode()
    evidence_ref = "cp-tech-v1:" + hashlib.sha256(identity).hexdigest()
    if not destination_matches:
        status = LinkStatus.MISMATCH if destination_id else LinkStatus.INVALID
    elif not image_valid:
        status = LinkStatus.INVALID
    else:
        status = LinkStatus.REVIEW_REQUIRED
    return TechnicalVerification(
        status=status,
        destination_product_id=destination_id,
        destination_matches=destination_matches,
        image_valid=image_valid,
        stock_valid=False,
        tracking_verified=False,
        reason=reason,
        evidence_ref=evidence_ref,
        checked_at=checked_at,
    )
