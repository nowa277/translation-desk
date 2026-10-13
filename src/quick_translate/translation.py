from concurrent.futures import ThreadPoolExecutor
import re

import requests

from .languages import SOURCE_BY_CODE, TARGET_BY_CODE

MAX_QUERY_BYTES = 1500


class TranslationError(RuntimeError):
    pass


def _parse_gtx(payload):
    if not isinstance(payload, list) or not payload or not isinstance(payload[0], list):
        return ""
    segments = payload[0]
    if not segments or any(not isinstance(s, list) or not s or not isinstance(s[0], str) for s in segments):
        return ""
    return "".join(segment[0] for segment in segments)


def _parse_mymemory(payload):
    if not isinstance(payload, dict) or payload.get("responseStatus") != 200 or payload.get("quotaFinished"):
        return ""
    data = payload.get("responseData")
    text = data.get("translatedText") if isinstance(data, dict) else None
    return text if isinstance(text, str) else ""


def _chunks(text, limit):
    remaining = text
    while remaining:
        if len(remaining.encode("utf-8")) <= limit:
            yield remaining
            break
        prefix = remaining.encode("utf-8")[:limit].decode("utf-8", errors="ignore")
        breaks = list(re.finditer(r"[。！？.!?]\s*|\s+", prefix))
        end = breaks[-1].end() if breaks and breaks[-1].end() > len(prefix) // 2 else len(prefix)
        yield remaining[:end]
        remaining = remaining[end:]


def _translate_chunk(text, source, target, session):
    try:
        response = session.get(
            "https://translate.googleapis.com/translate_a/single",
            params={"client": "gtx", "sl": source, "tl": target, "dt": "t", "q": text},
            timeout=(4, 8),
        )
        if response.status_code == 200:
            result = _parse_gtx(response.json())
            if result.strip():
                return result
    except (requests.RequestException, ValueError):
        pass

    fallback_source = source
    if source == "auto":
        fallback_source = "zh" if re.search(r"[㐀-鿿]", text) else "en"
    fallback_source = "zh-CN" if fallback_source == "zh" else fallback_source
    translated = []
    for chunk in _chunks(text, 480):
        try:
            response = session.get(
                "https://api.mymemory.translated.net/get",
                params={"q": chunk, "langpair": f"{fallback_source}|{target}"},
                timeout=(4, 8),
            )
            result = _parse_mymemory(response.json()) if response.status_code == 200 else ""
        except (requests.RequestException, ValueError):
            result = ""
        if not result.strip():
            raise TranslationError("Translation unavailable. Check your connection or try again later.")
        translated.append(result)
    return "".join(translated)


def translate_text(text, source="auto", target="en", session=None):
    if source not in SOURCE_BY_CODE or target not in TARGET_BY_CODE:
        raise ValueError("Unsupported source or target language")
    if not text.strip():
        return ""
    if source == target:
        return text
    own_session = session is None
    session = requests.Session() if own_session else session
    try:
        output = []
        for paragraph in re.split(r"(\r?\n)", text):
            if not paragraph.strip():
                output.append(paragraph)
            else:
                output.extend(_translate_chunk(chunk, source, target, session) for chunk in _chunks(paragraph, MAX_QUERY_BYTES))
        return "".join(output)
    finally:
        if own_session:
            session.close()


def translate_many(text, source, targets, session=None):
    with ThreadPoolExecutor(max_workers=max(1, min(4, len(targets)))) as pool:
        futures = {target: pool.submit(translate_text, text, source, target, session) for target in targets}
        return {target: future.result() for target, future in futures.items()}
