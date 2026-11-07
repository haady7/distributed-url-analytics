from app.services.url_service import encode_base62


def test_base62_encoding():
    assert encode_base62(0) == "0"
    assert encode_base62(61) == "Z"
    assert encode_base62(62) == "10"
    assert encode_base62(3844) == "100"
