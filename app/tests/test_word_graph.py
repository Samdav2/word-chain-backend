"""
Unit tests for the Word Graph engine.

Tests the core game mechanics:
- Graph building
- Move validation
- BFS pathfinding
- Hint generation
"""

import pytest
from app.service.word_graph import WordGraph


@pytest.fixture
def word_graph():
    """Create a word graph with test words."""
    graph = WordGraph()
    test_words = [
        "CAT", "BAT", "HAT", "RAT", "SAT", "MAT",
        "COT", "COW", "HOW", "NOW", "BOW", "ROW",
        "DOG", "LOG", "FOG", "HOG", "JOG", "BOG", "COG",
        "BIG", "DIG", "FIG", "GIG", "PIG", "RIG", "WIG",
        "BIT", "FIT", "HIT", "KIT", "LIT", "PIT", "SIT", "WIT",
        "CAKE", "BAKE", "FAKE", "LAKE", "MAKE", "RAKE",
        "FAIL", "BAIL", "HAIL", "JAIL", "MAIL", "NAIL", "PAIL", "RAIL", "SAIL", "TAIL",
        "FALL", "BALL", "CALL", "HALL", "MALL", "TALL", "WALL",
        "PASS", "BASS", "LASS", "MASS",
    ]
    graph.load_from_list(test_words)
    return graph


class TestWordGraphBuilding:
    """Tests for graph construction."""

    def test_load_words(self, word_graph):
        """Test that words are loaded correctly."""
        assert word_graph.is_valid_word("CAT")
        assert word_graph.is_valid_word("DOG")
        assert word_graph.is_valid_word("CAKE")

    def test_case_insensitive(self, word_graph):
        """Test that word lookup is case insensitive."""
        assert word_graph.is_valid_word("cat")
        assert word_graph.is_valid_word("Cat")
        assert word_graph.is_valid_word("CAT")

    def test_invalid_word(self, word_graph):
        """Test that invalid words are rejected."""
        assert not word_graph.is_valid_word("XYZ")
        assert not word_graph.is_valid_word("ZEBRA")
        assert not word_graph.is_valid_word("")

    def test_graph_stats(self, word_graph):
        """Test graph statistics."""
        stats = word_graph.get_stats()
        assert stats["total_words"] > 0
        assert stats["total_edges"] > 0


class TestMoveValidation:
    """Tests for move validation logic."""

    def test_valid_move_one_letter(self, word_graph):
        """Test valid move with one letter change."""
        is_valid, reason = word_graph.is_valid_move("CAT", "BAT")
        assert is_valid is True
        assert reason is None

    def test_valid_move_case_insensitive(self, word_graph):
        """Test that validation is case insensitive."""
        is_valid, reason = word_graph.is_valid_move("cat", "bat")
        assert is_valid is True

    def test_invalid_same_word(self, word_graph):
        """Test that same word is rejected."""
        is_valid, reason = word_graph.is_valid_move("CAT", "CAT")
        assert is_valid is False
        assert reason == "same_word"

    def test_invalid_not_in_dictionary(self, word_graph):
        """Test that non-dictionary words are rejected."""
        is_valid, reason = word_graph.is_valid_move("CAT", "ZAT")
        assert is_valid is False
        assert reason == "not_in_dictionary"

    def test_invalid_more_than_one_letter(self, word_graph):
        """Test that multiple letter changes are rejected."""
        is_valid, reason = word_graph.is_valid_move("CAT", "DOG")
        assert is_valid is False
        assert reason == "not_one_letter"

    def test_invalid_different_length(self, word_graph):
        """Test that different length words are rejected."""
        is_valid, reason = word_graph.is_valid_move("CAT", "CAKE")
        assert is_valid is False
        assert reason == "wrong_length"


class TestPathfinding:
    """Tests for BFS pathfinding and hints."""

    def test_get_neighbors(self, word_graph):
        """Test getting neighboring words."""
        neighbors = word_graph.get_neighbors("CAT")
        assert "BAT" in neighbors
        assert "HAT" in neighbors
        assert "DOG" not in neighbors  # Not a neighbor

    def test_shortest_path_exists(self, word_graph):
        """Test finding shortest path between connected words."""
        path = word_graph.get_shortest_path("CAT", "BAT")
        assert path is not None
        assert path == ["CAT", "BAT"]

    def test_shortest_path_multiple_steps(self, word_graph):
        """Test multi-step path."""
        # CAT -> COT -> COW
        path = word_graph.get_shortest_path("CAT", "COW")
        assert path is not None
        assert len(path) == 3
        assert path[0] == "CAT"
        assert path[-1] == "COW"

    def test_shortest_path_no_connection(self, word_graph):
        """Test path between unconnected words."""
        # 3-letter words can't connect to 4-letter words
        path = word_graph.get_shortest_path("CAT", "CAKE")
        assert path is None

    def test_get_distance(self, word_graph):
        """Test distance calculation."""
        assert word_graph.get_distance("CAT", "BAT") == 1
        assert word_graph.get_distance("CAT", "CAT") == 0

    def test_get_hint(self, word_graph):
        """Test hint generation."""
        hint = word_graph.get_hint("CAT", "BAT")
        assert hint == "BAT"  # Direct path

    def test_get_hint_multi_step(self, word_graph):
        """Test hint for multi-step path."""
        hint = word_graph.get_hint("CAT", "COW")
        # Hint should be the next step, not the final destination
        assert hint in word_graph.get_neighbors("CAT")


class TestRandomWordPair:
    """Tests for random word pair generation."""

    def test_get_random_pair(self, word_graph):
        """Test getting a random word pair."""
        pair = word_graph.get_random_word_pair(min_distance=1, max_distance=5)
        if pair:  # May return None if no suitable pair found
            start, target = pair
            assert word_graph.is_valid_word(start)
            assert word_graph.is_valid_word(target)
            assert start != target

    def test_random_pair_respects_distance(self, word_graph):
        """Test that random pairs respect distance constraints."""
        # Try multiple times since it's random
        for _ in range(10):
            pair = word_graph.get_random_word_pair(min_distance=1, max_distance=2)
            if pair:
                start, target = pair
                distance = word_graph.get_distance(start, target)
                assert 1 <= distance <= 2


class TestDiffersbyOne:
    """Tests for the one-letter difference check."""

    def test_differs_by_one_true(self, word_graph):
        """Test words that differ by one letter."""
        assert word_graph._differs_by_one("CAT", "BAT") is True
        assert word_graph._differs_by_one("CAT", "COT") is True
        assert word_graph._differs_by_one("CAT", "CUT") is True

    def test_differs_by_one_false_multiple(self, word_graph):
        """Test words that differ by multiple letters."""
        assert word_graph._differs_by_one("CAT", "DOG") is False
        assert word_graph._differs_by_one("CAT", "RAG") is False

    def test_differs_by_one_false_same(self, word_graph):
        """Test identical words."""
        assert word_graph._differs_by_one("CAT", "CAT") is False

    def test_differs_by_one_false_length(self, word_graph):
        """Test words of different lengths."""
        assert word_graph._differs_by_one("CAT", "CATS") is False
        assert word_graph._differs_by_one("CAT", "CA") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
