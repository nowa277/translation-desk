from quick_translate.theme import GLASS_CLARITY, build_stylesheet


def test_glass_clarity_is_25_percent():
    assert GLASS_CLARITY == 0.25


def test_stylesheet_contains_translucent_glass_and_no_branding():
    stylesheet = build_stylesheet()
    assert "rgba(205, 230, 237, 0.25)" in stylesheet
    assert "Claude" not in stylesheet
    assert "Anthropic" not in stylesheet
