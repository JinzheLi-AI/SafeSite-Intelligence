import base64
from io import BytesIO
from pathlib import Path
import pytest
from PIL import Image
from app.ai.images import prepare_image,image_data_url
from app.ai.errors import AIProviderError
from app.core.config import settings
from test_real_provider import provider,observation,analyze


@pytest.fixture(scope='module')
def oversized_jpeg():
    with Image.new('RGB',(6000,4500),'#557788') as image:
        output=BytesIO();image.save(output,format='JPEG',quality=90)
    return output.getvalue()


def dimensions(data):
    with Image.open(BytesIO(data)) as image:
        image.load();return image.size


def test_oversized_jpeg_resizes_and_preserves_aspect(oversized_jpeg):
    processed,mime=prepare_image(oversized_jpeg)
    assert mime=='image/jpeg' and dimensions(processed)==(2400,1800)
    assert 2400/1800==6000/4500
    assert dimensions(oversized_jpeg)==(6000,4500)


@pytest.mark.parametrize('format',['JPEG','PNG','WEBP'])
def test_normal_image_bytes_unchanged(format):
    output=BytesIO();Image.new('RGB',(120,80),'blue').save(output,format=format)
    raw=output.getvalue();processed,_=prepare_image(raw)
    assert processed==raw and dimensions(processed)==(120,80)


def test_original_preserved_and_processed_bytes_reach_provider(tmp_path,monkeypatch,oversized_jpeg):
    monkeypatch.setattr(settings,'upload_dir',tmp_path)
    original=tmp_path/'large.jpg';original.write_bytes(oversized_jpeg)
    instance=provider(observation([]))
    answer=analyze(instance,'/uploads/large.jpg')
    content=instance._injected_client.responses.parse.call_args.kwargs['input'][1]['content'][1]
    actual=base64.b64decode(content['image_url'].split(',',1)[1])
    assert actual==prepare_image(oversized_jpeg)[0]
    assert dimensions(actual)==(2400,1800) and answer.hazards==[]
    assert original.read_bytes()==oversized_jpeg
    assert list(tmp_path.iterdir())==[original]


def test_exif_rotation_applied_before_resize(oversized_jpeg):
    with Image.open(BytesIO(oversized_jpeg)) as im:
        exif=im.getexif();exif[274]=6
        source=BytesIO();im.save(source,format='JPEG',exif=exif)
    processed,_=prepare_image(source.getvalue())
    with Image.open(BytesIO(processed)) as im:
        assert im.size==(1800,2400) and im.getexif().get(274,1)==1


def test_normal_exif_rotation_is_not_ignored():
    output=BytesIO();im=Image.new('RGB',(120,80),'green');exif=im.getexif();exif[274]=6
    im.save(output,format='JPEG',exif=exif)
    assert dimensions(prepare_image(output.getvalue())[0])==(80,120)


@pytest.mark.parametrize('raw',[b'not an image',b'<svg xmlns="http://www.w3.org/2000/svg"/>'])
def test_invalid_bytes_rejected(raw):
    with pytest.raises(AIProviderError,match='safely decoded'):prepare_image(raw)


def test_truncated_jpeg_rejected(oversized_jpeg):
    with pytest.raises(AIProviderError):prepare_image(oversized_jpeg[:-100])


def test_decompression_bomb_guard_remains(monkeypatch,oversized_jpeg):
    monkeypatch.setattr(Image,'MAX_IMAGE_PIXELS',20_000_000)
    with pytest.raises(AIProviderError):prepare_image(oversized_jpeg)


def test_byte_limit_remains(monkeypatch,oversized_jpeg):
    monkeypatch.setattr(settings,'max_upload_bytes',100)
    with pytest.raises(AIProviderError) as exc:prepare_image(oversized_jpeg)
    assert exc.value.code=='image_too_large'


def test_oversized_upload_is_sanitized(client,oversized_jpeg):
    response=client.post('/api/v1/uploads',files={'file':('large.jpg',oversized_jpeg,'image/jpeg')})
    assert response.status_code==201
    stored=settings.upload_dir/Path(response.json()['image_path']).name
    assert dimensions(stored.read_bytes())==(2400,1800)
    assert len(stored.read_bytes())==response.json()['size_bytes']
    with Image.open(stored) as im:assert not im.getexif()
