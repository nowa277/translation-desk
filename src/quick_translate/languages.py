from dataclasses import dataclass


@dataclass(frozen=True)
class LanguageOption:
    code: str
    label: str
    shortcut: str


SOURCE_LANGUAGES = (
    LanguageOption("auto", "Auto detect", ""),
    LanguageOption("zh", "Chinese", ""),
    LanguageOption("en", "English", ""),
)

TARGET_LANGUAGES = (
    LanguageOption("en", "English", "Ctrl 1"),
    LanguageOption("ja", "Japanese", "Ctrl 2"),
    LanguageOption("ko", "Korean", "Ctrl 3"),
    LanguageOption("de", "German", ""),
    LanguageOption("fr", "French", ""),
    LanguageOption("es", "Spanish", ""),
    LanguageOption("zh", "Chinese", ""),
)

TARGET_BY_CODE = {option.code: option for option in TARGET_LANGUAGES}
SOURCE_BY_CODE = {option.code: option for option in SOURCE_LANGUAGES}


class TargetSelection:
    def __init__(self, enabled=("en", "ja", "ko")):
        self._enabled = []
        for code in enabled:
            self._validate(code)
            if code not in self._enabled:
                self._enabled.append(code)
        if not self._enabled:
            raise ValueError("at least one target language must remain enabled")

    def _validate(self, code):
        if code not in TARGET_BY_CODE:
            raise ValueError(f"unknown target language: {code}")

    def toggle(self, code):
        self._validate(code)
        if code in self._enabled:
            if len(self._enabled) == 1:
                return
            self._enabled.remove(code)
        else:
            self._enabled.append(code)
            self._enabled.sort(key=lambda item: list(TARGET_BY_CODE).index(item))

    def is_enabled(self, code):
        self._validate(code)
        return code in self._enabled

    def ordered(self):
        return tuple(self._enabled)
