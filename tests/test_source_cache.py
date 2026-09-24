from urllib.error import HTTPError

from nightcity import services


def test_conditional_get_reuses_validated_body(tmp_path, monkeypatch):
    requests = []

    class Response:
        headers = {"ETag": '"v1"', "Last-Modified": "Wed, 23 Sep 2026 10:00:00 GMT"}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, limit):
            return b'{"items":[1]}'

    def open_url(request, **kwargs):
        requests.append(request)
        if len(requests) == 2:
            raise HTTPError(request.full_url, 304, "Not Modified", {}, None)
        return Response()

    monkeypatch.setattr(services, "urlopen", open_url)
    url = "https://example.org/catalog.json"
    first = services.SourceCache(tmp_path)
    assert first.get(url) == ({"items": [1]}, True)
    first.commit()
    second = services.SourceCache(tmp_path)
    assert second.get(url) == ({"items": [1]}, False)
    assert requests[1].get_header("If-none-match") == '"v1"'
    assert len(list((tmp_path / "source-cache").glob("*.json"))) == 1


def test_unvalidated_source_is_not_cached(tmp_path, monkeypatch):
    url = "https://example.org/catalog.json"
    monkeypatch.setattr(services, "fetch_conditional_json", lambda *args: ({"items": []}, "etag", ""))
    cache = services.SourceCache(tmp_path)
    assert cache.get(url)[1]
    assert not (tmp_path / "source-cache").exists()


def test_same_content_without_server_validators_is_unchanged(tmp_path, monkeypatch):
    url = "https://example.org/catalog.json"
    payload = {"items": [1]}
    monkeypatch.setattr(services, "fetch_conditional_json", lambda *args: (payload, "", ""))
    cache = services.SourceCache(tmp_path)
    assert cache.get(url)[1]
    cache.commit()
    assert services.SourceCache(tmp_path).get(url) == (payload, False)
