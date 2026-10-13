import pytest

from quick_translate.translation import TranslationError, _parse_gtx, translate_text


class Response:
    def __init__(self, payload, status=200):
        self.status_code = status
        self.payload = payload

    def json(self):
        return self.payload


class Session:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append((url, params))
        return next(self.responses)


def test_malformed_gtx_segments_are_not_partial_translations():
    assert _parse_gtx([["Hello", "world", None]]) == ""


def test_provider_quota_error_is_not_translation():
    session = Session([
        Response({}, 503),
        Response({'responseStatus': 429, 'quotaFinished': True,
                  'responseData': {'translatedText': 'QUERY LIMIT EXCEEDED'}}),
    ])
    with pytest.raises(TranslationError):
        translate_text('Hello there', 'en', 'ja', session)


def test_auto_english_fallback_does_not_claim_chinese():
    session = Session([
        Response({}, 503),
        Response({'responseStatus': 200, 'responseData': {'translatedText': 'こんにちは'}}),
    ])
    assert translate_text('Hello there', 'auto', 'ja', session) == 'こんにちは'
    assert session.calls[1][1]['langpair'] == 'en|ja'


def test_long_paragraphs_are_chunked_and_newlines_preserved():
    class EchoSession:
        def __init__(self):
            self.queries = []

        def get(self, url, params, timeout):
            self.queries.append(params['q'])
            return Response([[[params['q'], None, None]]])

    text = '测试' * 3000 + '\n\n' + '尾段'
    session = EchoSession()
    assert translate_text(text, 'zh', 'en', session) == text
    assert max(len(q.encode('utf-8')) for q in session.queries) <= 1500


def test_same_explicit_source_target_avoids_network():
    session = Session([])
    assert translate_text('Hello there', 'en', 'en', session) == 'Hello there'
    assert session.calls == []


def test_unsupported_language_rejected_before_request():
    session = Session([])
    with pytest.raises(ValueError):
        translate_text('Hello', 'en', 'xx', session)
    assert not session.calls
