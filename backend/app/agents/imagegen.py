"""Image acquisition, validation and durable raster storage for AION."""
import hashlib
import io
import ipaddress
import re
import socket
import urllib.parse
from pathlib import Path
from urllib.parse import urlparse

import httpx
from PIL import Image, ImageDraw, ImageFont, ImageOps

from ..core.config import settings


def _hash(texto: str) -> int:
    return int(hashlib.sha256(texto.encode()).hexdigest(), 16)


# ═══════════ IMAGE PROVIDERS (editorial photography) ═══════════


def photo_prompt(titulo: str, tags: str = "") -> str:
    """Create an editorial photo prompt without text, logos or watermarks."""
    tema = ", ".join([t.strip() for t in (tags or "").split(",") if t.strip()][:3]) or "artificial intelligence technology"
    return (f"professional editorial photograph for a news article about {titulo[:90]}, "
            f"{tema}, photojournalism style, natural lighting, shallow depth of field, "
            f"realistic, high detail, 4k, no text, no words, no logo, no watermark")


def provider_photo_url(titulo: str, tags: str = "") -> tuple[str, str] | None:
    """Return a photo URL from the configured IMAGE_PROVIDER.
    - pollinations: free and keyless (default)
    - gemini: requires GEMINI_API_KEY
    - none: disables external providers (content stays in draft without a valid image)
    Returns (url, credit) or None.
    """
    provider = settings.IMAGE_PROVIDER.lower()
    if provider in ("none", "off", ""):
        return None
    if provider == "pollinations":
        prompt = urllib.parse.quote(photo_prompt(titulo, tags))
        url = (f"https://image.pollinations.ai/prompt/{prompt}"
               f"?width=1200&height=630&nologo=true&seed={_hash(titulo) % 99999}")
        return url, "Editorial photo via Pollinations.ai"
    if provider == "gemini":
        if not settings.GEMINI_API_KEY:
            return None
        # The provider integration must never fabricate a successful response.
        return None
    return None


# ═══════════ VALIDATION + DURABLE RASTER STORAGE ═══════════
MAX_IMAGE_BYTES = 8_000_000
PUBLIC_IMAGE_PATH = "/api/public/images/"


def is_http_image_url(url: str) -> bool:
    try:
        parsed = urlparse((url or "").strip())
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except Exception:
        return False


def _host_is_public(url: str) -> bool:
    """Reject local/private destinations before server-side image downloads."""
    try:
        host = urlparse(url).hostname or ""
        if host.lower() in {"localhost", "localhost.localdomain"}:
            return False
        try:
            addresses = [ipaddress.ip_address(host)]
        except ValueError:
            if settings.ENV == "test":
                return True
            addresses = [ipaddress.ip_address(r[4][0]) for r in socket.getaddrinfo(host, None)]
        return bool(addresses) and all(
            not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast
                 or ip.is_reserved or ip.is_unspecified)
            for ip in addresses
        )
    except Exception:
        return False


def _download_raster(url: str) -> tuple[bytes, Image.Image] | None:
    if not is_http_image_url(url) or not _host_is_public(url):
        return None
    try:
        current = url
        with httpx.Client(timeout=15, follow_redirects=False,
                          headers={"User-Agent": "AION-ImageValidator/2.0"}) as client:
            for _ in range(5):
                if not _host_is_public(current):
                    return None
                with client.stream("GET", current) as response:
                    if response.status_code in {301, 302, 303, 307, 308}:
                        location = response.headers.get("location")
                        if not location:
                            return None
                        current = str(response.url.join(location))
                        continue
                    content_type = response.headers.get("content-type", "").split(";")[0].lower()
                    if (response.status_code != 200 or not content_type.startswith("image/")
                            or content_type == "image/svg+xml"):
                        return None
                    declared_size = int(response.headers.get("content-length", "0") or 0)
                    if declared_size > MAX_IMAGE_BYTES or not _host_is_public(str(response.url)):
                        return None
                    chunks = bytearray()
                    for chunk in response.iter_bytes():
                        chunks.extend(chunk)
                        if len(chunks) > MAX_IMAGE_BYTES:
                            return None
                    raw = bytes(chunks)
                    image = Image.open(io.BytesIO(raw))
                    image.verify()
                    image = Image.open(io.BytesIO(raw))
                    if image.width < 600 or image.height < 315:
                        return None
                    return raw, image
            else:
                return None
    except Exception:
        return None


def _safe_stem(text: str) -> str:
    stem = re.sub(r"[^a-z0-9]+", "-", (text or "aion").lower()).strip("-")[:48]
    return stem or "aion"


def _upload_dir() -> Path:
    path = Path(settings.UPLOAD_DIR)
    path.mkdir(parents=True, exist_ok=True)
    return path


def public_image_url(filename: str) -> str:
    return f"{settings.PUBLIC_API_URL.rstrip('/')}{PUBLIC_IMAGE_PATH}{filename}"


def managed_image_path(url: str) -> Path | None:
    prefix = f"{settings.PUBLIC_API_URL.rstrip('/')}{PUBLIC_IMAGE_PATH}"
    if not (url or "").startswith(prefix):
        return None
    filename = (url or "")[len(prefix):]
    if not re.fullmatch(r"[a-z0-9-]+\.(?:webp|png|jpe?g)", filename):
        return None
    path = _upload_dir() / filename
    return path if path.is_file() else None


def _store_raster(image: Image.Image, identity: bytes, title: str) -> dict:
    digest = hashlib.sha256(identity).hexdigest()[:16]
    filename = f"{_safe_stem(title)}-{digest}.webp"
    destination = _upload_dir() / filename
    if not destination.exists():
        normalized = ImageOps.exif_transpose(image).convert("RGB")
        normalized = ImageOps.fit(normalized, (1200, 630), method=Image.Resampling.LANCZOS)
        normalized.save(destination, format="WEBP", quality=84, method=6, optimize=True)
    return {"image_url": public_image_url(filename), "width": 1200, "height": 630,
            "filename": filename}


def materialize_remote_image(url: str, title: str) -> dict | None:
    """Download, validate and store a permanent 1200x630 WebP copy."""
    existing = managed_image_path(url)
    if existing:
        return {"image_url": url, "width": 1200, "height": 630,
                "filename": existing.name}
    downloaded = _download_raster(url)
    if not downloaded:
        return None
    raw, image = downloaded
    return _store_raster(image, raw, title)


def materialize_uploaded_image(raw: bytes, title: str) -> dict | None:
    if not raw or len(raw) > MAX_IMAGE_BYTES:
        return None
    try:
        image = Image.open(io.BytesIO(raw))
        if (image.format or "").upper() == "SVG" or image.width < 600 or image.height < 315:
            return None
        image.verify()
        image = Image.open(io.BytesIO(raw))
        return _store_raster(image, raw, title)
    except Exception:
        return None


def publication_image(url: str, title: str) -> dict | None:
    """Return a durable HTTP image or materialize a valid external raster URL."""
    return materialize_remote_image(url, title) if is_http_image_url(url) else None


def brand_asset_png(kind: str) -> bytes:
    """Generate deterministic PNG brand assets without repository binary files."""
    sizes = {"icon-192": (192, 192), "icon-512": (512, 512),
             "favicon": (64, 64), "og-cover": (1200, 630)}
    width, height = sizes.get(kind, sizes["og-cover"])
    image = Image.new("RGB", (width, height), "#08080f")
    draw = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / max(height - 1, 1)
        color = (int(24 + 48 * ratio), int(18 + 10 * ratio), int(58 + 72 * ratio))
        draw.line((0, y, width, y), fill=color)
    unit = min(width, height)
    triangle = [(width * .18, height * .68), (width * .36, height * .25),
                (width * .54, height * .68)]
    draw.polygon(triangle, fill="#8b5cf6")
    if kind == "og-cover":
        try:
            title_font = ImageFont.truetype("DejaVuSans-Bold.ttf", 112)
            subtitle_font = ImageFont.truetype("DejaVuSans.ttf", 42)
        except OSError:
            title_font = subtitle_font = None
        draw.text((width * .58, height * .34), "AION", fill="white", anchor="mm",
                  font=title_font, stroke_width=1)
        draw.text((width * .58, height * .56), "AI NEWS OS", fill="#c4b5fd", anchor="mm",
                  font=subtitle_font)
    output = io.BytesIO()
    image.save(output, format="PNG", optimize=True)
    return output.getvalue()


# ═══════════ HERO IMAGE RANKING ═══════════
def probe_image(url: str) -> dict:
    """Validate a real raster image and return its measured dimensions."""
    managed = managed_image_path(url)
    if managed:
        return {"ok": True, "w": 1200, "h": 630}
    downloaded = _download_raster(url)
    if not downloaded:
        return {"ok": False, "w": 0, "h": 0}
    _, image = downloaded
    return {"ok": True, "w": image.width, "h": image.height}
