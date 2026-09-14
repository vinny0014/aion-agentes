from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from urllib.parse import urlparse


class LinkStatus(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    EXPIRED = "EXPIRED"
    MISMATCH = "MISMATCH"
    UNKNOWN = "UNKNOWN"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"


@dataclass(frozen=True)
class AffiliateLinkCheck:
    status: LinkStatus
    technically_valid: bool
    reason: str


@dataclass(frozen=True)
class OfferPublicationState:
    publishable: bool
    reason: str


def validate_shopee_url_structure(url: str) -> AffiliateLinkCheck:
    """Validate only the technical URL structure.

    This deliberately does not claim affiliate attribution. Attribution can only
    be confirmed by an authorized Shopee source/report. The exact URL should be
    persisted separately and never rewritten by this function.
    """
    if not url or not isinstance(url, str):
        return AffiliateLinkCheck(LinkStatus.INVALID, False, "empty_url")

    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return AffiliateLinkCheck(LinkStatus.INVALID, False, "malformed_url")

    if parsed.scheme != "https":
        return AffiliateLinkCheck(LinkStatus.INVALID, False, "https_required")

    host = (parsed.hostname or "").lower().rstrip(".")
    if not host:
        return AffiliateLinkCheck(LinkStatus.INVALID, False, "missing_host")

    allowed = host == "shopee.com.br" or host.endswith(".shopee.com.br") or host == "shope.ee"
    if not allowed:
        return AffiliateLinkCheck(LinkStatus.INVALID, False, "unexpected_destination")

    # Short/redirect URLs and full product URLs can both be legitimate. A valid
    # host is therefore necessary but not sufficient for affiliate attribution.
    return AffiliateLinkCheck(LinkStatus.REVIEW_REQUIRED, True, "structure_ok_requires_authorized_attribution_check")


def assess_offer_for_publication(
    *,
    product_active: bool,
    offer_active: bool,
    image_valid: bool,
    affiliate_status: LinkStatus,
    destination_matches_product: bool,
    price_valid: bool,
    price_fresh: bool,
) -> OfferPublicationState:
    """Fail closed: every required signal must pass before traffic is allowed."""
    checks = (
        (product_active, "product_inactive"),
        (offer_active, "offer_inactive"),
        (image_valid, "image_invalid"),
        (affiliate_status == LinkStatus.VALID, "affiliate_link_not_valid"),
        (destination_matches_product, "destination_product_mismatch"),
        (price_valid, "price_invalid"),
        (price_fresh, "price_stale"),
    )
    for passed, reason in checks:
        if not passed:
            return OfferPublicationState(False, reason)
    return OfferPublicationState(True, "ok")
