import pytest

from quick_translate.translation import TranslationError, translate_many, translate_text


class FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self.payload = payload

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append(type("Call", (), {"url": url, "params": params, "timeout": timeout}))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_gtx_response_is_joined_and_source_is_forwarded():
    session = FakeSession([FakeResponse(200, [[["你好", "Hello", None], ["世界", "world", None]]])])
    assert translate_text("Hello world", "en", "zh", session=session) == "你好世界"
    assert session.calls[0].params["sl"] == "en"
    assert session.calls[0].params["tl"] == "zh"


def test_mymemory_is_used_when_gtx_fails():
    session = FakeSession([
        FakeResponse(503, {}),
        FakeResponse(200, {"responseStatus": 200, "responseData": {"translatedText": "Hello"}}),
    ])
    assert translate_text("你好", "auto", "en", session=session) == "Hello"
    assert session.calls[1].params["langpair"] == "zh-CN|en"


def test_both_provider_failures_raise_translation_error():
    session = FakeSession([FakeResponse(503, {}), FakeResponse(503, {})])
    with pytest.raises(TranslationError):
        translate_text("你好", "auto", "en", session=session)


def test_translate_many_requests_only_enabled_targets():
    class TargetSession:
        def __init__(self):
            self.calls = []

        def get(self, url, params, timeout):
            self.calls.append(params)
            payload = {
                "en": [["Hello", "Hello", None]],
                "ja": [["こんにちは", "こんにちは", None]],
            }[params["tl"]]
            return FakeResponse(200, [payload])

    session = TargetSession()
    result = translate_many("你好", "auto", ("en", "ja"), session=session)
    assert result == {"en": "Hello", "ja": "こんにちは"}
    assert {call["tl"] for call in session.calls} == {"en", "ja"}
