import base64
import warnings
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageOps, UnidentifiedImageError
from app.ai.errors import AIProviderError
from app.core.config import settings


def resolve_upload(path: str, root: Path | None = None) -> Path:
    root = (root or settings.upload_dir).resolve()
    name = path.removeprefix('/uploads/')
    if not path.startswith('/uploads/') or not name or any(c in name for c in ('/', '\\', ':', '..', '\x00')):
        raise AIProviderError('invalid_image_path', 'Evidence must refer to an image returned by the upload API.', 422)
    resolved = (root / name).resolve()
    if resolved.parent != root or not resolved.is_file():
        raise AIProviderError('missing_image', 'The uploaded image is unavailable. Please upload it again.', 422)
    return resolved


def image_data_url(path: str | None) -> str:
    if not path:
        raise AIProviderError('image_required', 'Real AI analysis requires an uploaded image. No demo fallback was used.', 422)
    image_path = resolve_upload(path)
    with image_path.open('rb') as image_file:
        content = image_file.read(settings.max_upload_bytes + 1)
    content, media_type = prepare_image(content)
    return 'data:' + media_type + ';base64,' + base64.b64encode(content).decode('ascii')


def prepare_image(content: bytes, *, sanitize: bool = False) -> tuple[bytes, str]:
    """Validate fully; resize >25 MP in memory. Never write to the source file.

    Ordinary correctly oriented provider inputs retain their exact bytes. Uploads
    request sanitization to preserve the existing metadata-stripping re-encode.
    Pillow's decompression-bomb ceiling remains an independent hard safety limit.
    """
    if len(content) > settings.max_upload_bytes:
        raise AIProviderError('image_too_large', 'Image exceeds the configured upload size limit.', 413)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(content)) as image:
                media_type = {'JPEG': 'image/jpeg', 'PNG': 'image/png', 'WEBP': 'image/webp'}.get(image.format)
                if media_type is None:
                    raise AIProviderError('invalid_image', 'Use a valid JPEG, PNG or WebP image.', 422)
                image.verify()
            with Image.open(BytesIO(content)) as image:
                # verify() alone does not detect every truncated JPEG; force full decoding.
                image.load()
                oversized = image.width * image.height > 25_000_000
                orientation = image.getexif().get(274, 1)
                if not sanitize and not oversized and orientation == 1:
                    return content, media_type
                oriented = ImageOps.exif_transpose(image)
                if oversized:
                    oriented.thumbnail((2400, 2400), Image.Resampling.LANCZOS)
                # Fresh RGB canvas strips metadata, including the already applied EXIF.
                clean = Image.new('RGB', oriented.size, 'white')
                if 'A' in oriented.getbands() or 'transparency' in oriented.info:
                    rgba = oriented.convert('RGBA')
                    clean.paste(rgba, mask=rgba.getchannel('A'))
                else:
                    clean.paste(oriented.convert('RGB'))
                output = BytesIO()
                clean.save(output, format='JPEG', quality=95, subsampling=0)
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError,
            Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise AIProviderError('invalid_image', 'The image could not be safely decoded. Upload a valid JPEG, PNG or WebP image.', 422) from None
    processed = output.getvalue()
    if len(processed) > settings.max_upload_bytes:
        raise AIProviderError('image_too_large', 'The decoded image exceeds the storage size limit. Upload a smaller image.', 413)
    return processed, 'image/jpeg'
