from hcra.manager import HCRAManager


def test_add_and_get_context():
    manager = HCRAManager()
    manager.add_context("intro", "Hello world", {"source": "unit"})
    entry = manager.get_context("intro")
    assert entry is not None
    assert entry.context_id == "intro"
    assert entry.metadata["source"] == "unit"


def test_search_returns_best_match():
    manager = HCRAManager()
    manager.add_context("greeting", "Hello world and hello sky")
    manager.add_context("farewell", "Goodbye moon")

    results = manager.search("hello")
    assert results
    assert results[0]["context_id"] == "greeting"


def test_remove_context():
    manager = HCRAManager()
    manager.add_context("temp", "Temporary entry")
    manager.remove_context("temp")
    assert manager.get_context("temp") is None
