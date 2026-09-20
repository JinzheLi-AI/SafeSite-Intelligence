from uuid import uuid4
from fastapi import APIRouter, UploadFile, HTTPException
from app.ai.images import prepare_image
from app.ai.errors import AIProviderError
from app.core.config import settings

router = APIRouter(prefix='/uploads', tags=['Evidence'])


@router.post('', status_code=201)
async def upload_image(file: UploadFile):
    data = await file.read(settings.max_upload_bytes + 1)
    await file.close()
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(413, f'Image must be {settings.max_upload_bytes / (1024 * 1024):g} MB or smaller.')
    try:
        # Shared validation/preprocessing; uploads still strip metadata by re-encoding.
        processed, _ = prepare_image(data, sanitize=True)
    except AIProviderError as exc:
        raise HTTPException(413 if exc.code == 'image_too_large' else 415, exc.message) from None
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f'{uuid4().hex}.jpg'
    (settings.upload_dir / filename).write_bytes(processed)
    return {'image_path': f'/uploads/{filename}', 'size_bytes': len(processed)}
