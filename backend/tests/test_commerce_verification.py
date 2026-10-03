import io
import socket

import httpx
from PIL import Image

from app.commerce.guardrails import LinkStatus
from app.commerce.verification import verify_technical_evidence


def public_resolver(host, port):
    return [(socket.AF_INET,socket.SOCK_STREAM,6,'',( '93.184.216.34',443))]


def png_bytes():
    output=io.BytesIO()
    Image.new('RGB',(300,300),'orange').save(output,format='PNG')
    return output.getvalue()


def record():
    return {'product_id':'1:2','affiliate_url':'https://shope.ee/go',
            'image_url':'https://down-br.img.susercontent.com/file/real'}


def test_technical_verification_proves_destination_and_raster_but_not_tracking():
    image=png_bytes()
    def handler(request):
        if request.url.host == 'shope.ee':
            return httpx.Response(302,headers={'location':'https://shopee.com.br/product/1/2'})
        if request.url.host == 'shopee.com.br':
            return httpx.Response(200)
        return httpx.Response(200,content=image,headers={'content-type':'image/png'})
    with httpx.Client(transport=httpx.MockTransport(handler),follow_redirects=False) as client:
        result=verify_technical_evidence(record(),client=client,resolver=public_resolver,now=1800000000)
    assert result.status == LinkStatus.REVIEW_REQUIRED
    assert result.destination_product_id == '1:2'
    assert result.destination_matches is True and result.image_valid is True
    assert result.stock_valid is False and result.tracking_verified is False
    assert result.reason == 'tracking_and_stock_unconfirmed'
    assert result.evidence_ref.startswith('cp-tech-v1:')


def test_technical_verification_rejects_mismatch_private_redirect_and_fake_image():
    cases=(
        lambda request:httpx.Response(302,headers={'location':'https://shopee.com.br/product/9/9'}),
        lambda request:httpx.Response(302,headers={'location':'https://127.0.0.1/product/1/2'}),
        lambda request:httpx.Response(200,content=b'not-an-image',headers={'content-type':'image/png'}),
    )
    for index,handler in enumerate(cases):
        def routed(request):
            if index == 2 and request.url.host == 'shope.ee':
                return httpx.Response(302,headers={'location':'https://shopee.com.br/product/1/2'})
            if index == 2 and request.url.host == 'shopee.com.br':
                return httpx.Response(200)
            return handler(request)
        with httpx.Client(transport=httpx.MockTransport(routed),follow_redirects=False) as client:
            result=verify_technical_evidence(record(),client=client,resolver=public_resolver,now=1800000000)
        assert result.status != LinkStatus.VALID
        assert result.tracking_verified is False and result.image_valid is False
