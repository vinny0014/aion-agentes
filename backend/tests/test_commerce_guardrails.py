from app.commerce.guardrails import (
    LinkStatus,
    assess_offer_for_publication,
    validate_shopee_url_structure,
)


def test_rejects_non_shopee_destination():
    result = validate_shopee_url_structure("https://example.com/produto")
    assert result.status == LinkStatus.INVALID
    assert result.technically_valid is False


def test_shopee_url_requires_attribution_confirmation():
    result = validate_shopee_url_structure("https://shopee.com.br/produto-exemplo-i.1.2")
    assert result.status == LinkStatus.REVIEW_REQUIRED
    assert result.technically_valid is True


def test_offer_is_fail_closed_until_affiliate_link_is_valid():
    state = assess_offer_for_publication(
        product_active=True,
        offer_active=True,
        image_valid=True,
        affiliate_status=LinkStatus.REVIEW_REQUIRED,
        destination_matches_product=True,
        price_valid=True,
        price_fresh=True,
    )
    assert state.publishable is False
    assert state.reason == "affiliate_link_not_valid"


def test_offer_can_publish_only_when_all_signals_pass():
    state = assess_offer_for_publication(
        product_active=True,
        offer_active=True,
        image_valid=True,
        affiliate_status=LinkStatus.VALID,
        destination_matches_product=True,
        price_valid=True,
        price_fresh=True,
    )
    assert state.publishable is True
    assert state.reason == "ok"
