import uuid
from io import BytesIO
from urllib.parse import urlparse
from minio import Minio
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from app.auth.deps import get_current_user
from app.config import get_settings
from app.models.user import User

router = APIRouter(prefix='/media', tags=['uploads'])
settings = get_settings()


def _minio_endpoint_and_tls() -> tuple[str, bool]:
    endpoint = settings.s3_endpoint.strip()
    if '://' not in endpoint:
        return endpoint, False
    parsed = urlparse(endpoint)
    host = parsed.netloc or parsed.path
    return host, parsed.scheme.lower() == 'https'


def _client() -> Minio:
    endpoint, secure = _minio_endpoint_and_tls()
    return Minio(
        endpoint,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        region=settings.s3_region,
        secure=secure,
    )


def _upload_image(file: UploadFile, user: User) -> dict[str, str]:
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail='Only image files are accepted')

    client = _client()
    if not client.bucket_exists(settings.s3_bucket):
        client.make_bucket(settings.s3_bucket)

    ext = (file.filename or 'upload').split('.')[-1]
    key = f'{user.id}/{uuid.uuid4()}.{ext}'
    data = file.file.read()
    client.put_object(
        settings.s3_bucket,
        key,
        data=BytesIO(data),
        length=len(data),
        content_type=file.content_type,
    )
    return {'media_url': f"{settings.s3_public_base.rstrip('/')}/{key}"}


@router.post('/upload')
def upload_image(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    return _upload_image(file, user)


@router.post('/image', include_in_schema=False)
def upload_image_legacy(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    return _upload_image(file, user)
