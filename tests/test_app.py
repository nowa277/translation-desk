from quick_translate.app import TranslationController


def test_controller_increments_revision_and_rejects_stale_results():
    controller = TranslationController(translate_func=lambda text, source, target: f"{text}:{target}")
    first = controller.request("one", "auto", ("en",))
    second = controller.request("two", "auto", ("en",))
    assert second > first
    controller.receive_result(first, "en", "old")
    assert controller.result_for("en") == ""
    controller.receive_result(second, "en", "new")
    assert controller.result_for("en") == "new"


def test_controller_keeps_success_when_one_target_fails():
    controller = TranslationController()
    revision = controller.begin_request("hello", "auto", ("en", "ja"))
    controller.receive_result(revision, "en", "Hello")
    controller.receive_error(revision, "ja", "Translation unavailable")
    assert controller.result_for("en") == "Hello"
    assert controller.result_for("ja") == ""
    assert controller.can_paste("en") is True
    assert controller.can_paste("ja") is False
