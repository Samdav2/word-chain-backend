"""
The "Breakthrough" Game Engine - NetworkX Word Graph

This module builds an in-memory graph where every word is a node and
connections (edges) represent 1-letter differences. It enables instant
path validation and BFS-powered hint generation.

Enhanced with category support for educational word filtering.
"""

import networkx as nx
from typing import List, Optional, Set, Tuple, Dict
from pathlib import Path
import random
import os


class WordCategory:
    """Word category constants."""
    GENERAL = "general"
    SCIENCE = "science"
    BIOLOGY = "biology"
    PHYSICS = "physics"
    EDUCATION = "education"
    MIXED = "mixed"

    ALL_CATEGORIES = [GENERAL, SCIENCE, BIOLOGY, PHYSICS, EDUCATION]


class WordGraph:
    """
    A graph-based word chain validator using NetworkX.

    The graph is built once on application startup by comparing all words
    in the dictionary. Words that differ by exactly one letter are connected
    with edges, enabling constant-time validation and BFS pathfinding.

    Now supports word categories for educational filtering.
    """

    def __init__(self, dictionary_path: Optional[str] = None):
        """Initialize the word graph."""
        self.graph = nx.Graph()
        self.words: Set[str] = set()
        self.edtech_words: Set[str] = set()
        self._is_loaded = False

        # Category-specific word sets
        self.words_by_category: Dict[str, Set[str]] = {
            WordCategory.GENERAL: set(),
            WordCategory.SCIENCE: set(),
            WordCategory.BIOLOGY: set(),
            WordCategory.PHYSICS: set(),
            WordCategory.EDUCATION: set(),
        }

        # Word definitions (educational context) - stores rich definition data
        self.word_definitions: Dict[str, Dict] = {}

        # Word difficulty ratings (1-5)
        self.word_difficulty: Dict[str, int] = {}

        if dictionary_path:
            self.load_dictionary(dictionary_path)

    def load_dictionary(self, path: str) -> int:
        """
        Load dictionary and build the word graph.
        Returns the number of words loaded.
        """
        words = []

        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip().upper()
                    if word and not word.startswith('#') and 3 <= len(word) <= 6:
                        words.append(word)
        except FileNotFoundError:
            # Use default built-in dictionary
            words = self._get_default_words()

        self._build_graph(words)
        self._is_loaded = True
        return len(self.words)

    def load_category_dictionaries(self, base_path: str) -> Dict[str, int]:
        """
        Load all category dictionary files from a directory.

        Expected files:
        - general_words.txt
        - science_words.txt
        - biology_words.txt
        - physics_words.txt
        - education_words.txt

        Returns dict of category -> word count.
        """
        category_files = {
            WordCategory.GENERAL: "general_words.txt",
            WordCategory.SCIENCE: "science_words.txt",
            WordCategory.BIOLOGY: "biology_words.txt",
            WordCategory.PHYSICS: "physics_words.txt",
            WordCategory.EDUCATION: "education_words.txt",
        }

        all_words = []
        counts = {}

        for category, filename in category_files.items():
            filepath = os.path.join(base_path, filename)
            category_words = self._load_word_file(filepath)
            self.words_by_category[category] = set(category_words)
            counts[category] = len(category_words)
            all_words.extend(category_words)

            # Assign difficulty based on category
            for word in category_words:
                if category == WordCategory.GENERAL:
                    self.word_difficulty[word] = self._calculate_word_difficulty(word, 2)
                elif category == WordCategory.EDUCATION:
                    self.word_difficulty[word] = self._calculate_word_difficulty(word, 3)
                else:  # Science, Biology, Physics
                    self.word_difficulty[word] = self._calculate_word_difficulty(word, 4)

        # Build combined graph from all words
        self._build_graph(all_words)
        self._is_loaded = True

        return counts

    def load_definitions_json(self, filepath: str) -> None:
        """Load rich word definitions from a JSON file."""
        import json
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                definitions = json.load(f)
                # Normalize keys to uppercase
                self.word_definitions = {k.upper(): v for k, v in definitions.items()}
                print(f"📖 Loaded {len(self.word_definitions)} word definitions")
        except FileNotFoundError:
            print(f"⚠️ Word definitions file not found: {filepath}")
        except json.JSONDecodeError as e:
            print(f"⚠️ Error parsing definitions JSON: {e}")

    def _load_word_file(self, filepath: str) -> List[str]:
        """Load words from a single file."""
        words = []
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip().upper()
                    # Skip comments and empty lines
                    if word and not word.startswith('#') and 3 <= len(word) <= 6:
                        words.append(word)
        except FileNotFoundError:
            print(f"⚠️ Word file not found: {filepath}")
        return words

    def _calculate_word_difficulty(self, word: str, base_difficulty: int) -> int:
        """
        Calculate word difficulty (1-5) based on length and base category difficulty.
        """
        length_modifier = 0
        if len(word) >= 5:
            length_modifier = 1
        elif len(word) <= 3:
            length_modifier = -1

        difficulty = base_difficulty + length_modifier
        return max(1, min(5, difficulty))  # Clamp between 1-5

    def load_from_list(self, words: List[str]) -> int:
        """Load words from a list (useful for testing)."""
        cleaned = [w.strip().upper() for w in words if 3 <= len(w.strip()) <= 6]
        self._build_graph(cleaned)
        self._is_loaded = True
        return len(self.words)

    def _build_graph(self, words: List[str]) -> None:
        """Build the graph by connecting words that differ by 1 letter."""
        self.words = set(words)
        self.graph.clear()

        # Add all words as nodes
        self.graph.add_nodes_from(self.words)

        # Group words by length for efficient comparison
        by_length: dict[int, List[str]] = {}
        for word in self.words:
            length = len(word)
            if length not in by_length:
                by_length[length] = []
            by_length[length].append(word)

        # Connect words that differ by exactly 1 letter
        for length, word_list in by_length.items():
            n = len(word_list)
            for i in range(n):
                for j in range(i + 1, n):
                    if self._differs_by_one(word_list[i], word_list[j]):
                        self.graph.add_edge(word_list[i], word_list[j])

    def _differs_by_one(self, word1: str, word2: str) -> bool:
        """Check if two words differ by exactly one letter."""
        if len(word1) != len(word2):
            return False

        differences = sum(c1 != c2 for c1, c2 in zip(word1, word2))
        return differences == 1

    def is_valid_word(self, word: str) -> bool:
        """Check if a word exists in the dictionary."""
        return word.upper() in self.words

    def is_valid_word_in_category(self, word: str, category: str) -> bool:
        """Check if a word exists in a specific category."""
        word = word.upper()
        if category == WordCategory.MIXED:
            return word in self.words
        return word in self.words_by_category.get(category, set())

    def get_words_in_category(self, category: str) -> Set[str]:
        """Get all words in a specific category."""
        if category == WordCategory.MIXED:
            return self.words
        return self.words_by_category.get(category, set())

    def is_valid_move(self, current: str, next_word: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a move from current word to next word.

        Returns:
            Tuple of (is_valid, error_reason)
        """
        current = current.upper()
        next_word = next_word.upper()

        # Same word check
        if current == next_word:
            return False, "same_word"

        # Length check
        if len(current) != len(next_word):
            return False, "wrong_length"

        # Dictionary check
        if next_word not in self.words:
            return False, "not_in_dictionary"

        # One letter difference check
        if not self._differs_by_one(current, next_word):
            return False, "not_one_letter"

        # Check if edge exists in graph (should always be true at this point)
        if not self.graph.has_edge(current, next_word):
            return False, "not_one_letter"

        return True, None

    def get_neighbors(self, word: str) -> List[str]:
        """Get all valid next words from the current word."""
        word = word.upper()
        if word not in self.graph:
            return []
        return list(self.graph.neighbors(word))

    def get_neighbors_in_category(self, word: str, category: str) -> List[str]:
        """Get valid next words from current word, filtered by category."""
        neighbors = self.get_neighbors(word)
        if category == WordCategory.MIXED:
            return neighbors
        category_words = self.words_by_category.get(category, set())
        return [n for n in neighbors if n in category_words]

    def get_shortest_path(self, start: str, target: str) -> Optional[List[str]]:
        """
        Find the shortest path between two words using BFS.

        Returns:
            List of words in the path, or None if no path exists.
        """
        start = start.upper()
        target = target.upper()

        if start not in self.graph or target not in self.graph:
            return None

        try:
            path = nx.shortest_path(self.graph, start, target)
            return path
        except nx.NetworkXNoPath:
            return None

    def get_distance(self, start: str, target: str) -> int:
        """Get the minimum number of moves to reach target from start."""
        path = self.get_shortest_path(start, target)
        if path is None:
            return -1  # No path exists
        return len(path) - 1  # -1 because path includes start word

    def get_hint(self, current: str, target: str) -> Optional[str]:
        """
        Get the next word in the optimal path to target.

        This is the AI-powered hint using BFS.
        """
        path = self.get_shortest_path(current, target)
        if path and len(path) > 1:
            return path[1]  # Return the next word after current
        return None

    def get_word_definition(self, word: str) -> Optional[Dict]:
        """Get the rich educational definition for a word."""
        return self.word_definitions.get(word.upper())

    def get_word_difficulty_level(self, word: str) -> int:
        """Get the difficulty level (1-5) for a word."""
        return self.word_difficulty.get(word.upper(), 3)

    def get_random_word_pair(
        self,
        min_distance: int = 3,
        max_distance: int = 6
    ) -> Optional[Tuple[str, str]]:
        """
        Get a random start/target word pair with the specified path distance.

        Returns:
            Tuple of (start_word, target_word) or None if no suitable pair found.
        """
        return self._find_word_pair(self.words, min_distance, max_distance)

    def get_random_word_pair_by_category(
        self,
        category: str,
        min_distance: int = 3,
        max_distance: int = 6,
        difficulty: Optional[int] = None
    ) -> Optional[Tuple[str, str]]:
        """
        Get a random word pair from a specific category.

        Args:
            category: Word category (general, science, biology, physics, education, mixed)
            min_distance: Minimum path distance
            max_distance: Maximum path distance
            difficulty: Optional difficulty filter (1-5)

        Returns:
            Tuple of (start_word, target_word) or None if no suitable pair found.
        """
        if category == WordCategory.MIXED:
            word_pool = self.words
        else:
            word_pool = self.words_by_category.get(category, set())

        if not word_pool:
            # Fallback to all words
            word_pool = self.words

        # Filter by difficulty if specified
        if difficulty:
            word_pool = {w for w in word_pool
                        if abs(self.word_difficulty.get(w, 3) - difficulty) <= 1}

        return self._find_word_pair(word_pool, min_distance, max_distance)

    def _find_word_pair(
        self,
        word_pool: Set[str],
        min_distance: int,
        max_distance: int
    ) -> Optional[Tuple[str, str]]:
        """Find a random word pair from a pool with distance constraints."""
        if not self._is_loaded or not word_pool:
            return None

        words_list = list(word_pool)
        random.shuffle(words_list)

        attempts = 0
        max_attempts = 200

        while attempts < max_attempts:
            start = random.choice(words_list)
            target = random.choice(words_list)

            if start == target:
                attempts += 1
                continue

            # Ensure both words are in the graph
            if start not in self.graph or target not in self.graph:
                attempts += 1
                continue

            distance = self.get_distance(start, target)

            if min_distance <= distance <= max_distance:
                return (start, target)

            attempts += 1

        return None

    def get_stats(self) -> dict:
        """Get graph statistics."""
        category_counts = {
            cat: len(words) for cat, words in self.words_by_category.items()
        }

        return {
            "total_words": len(self.words),
            "total_edges": self.graph.number_of_edges(),
            "is_connected": nx.is_connected(self.graph) if len(self.words) > 0 else False,
            "average_degree": sum(dict(self.graph.degree()).values()) / len(self.words) if len(self.words) > 0 else 0,
            "words_by_category": category_counts
        }

    def get_category_stats(self, category: str) -> dict:
        """Get statistics for a specific category."""
        if category == WordCategory.MIXED:
            words = self.words
        else:
            words = self.words_by_category.get(category, set())

        # Count words in graph for this category
        in_graph = sum(1 for w in words if w in self.graph)

        return {
            "category": category,
            "word_count": len(words),
            "words_in_graph": in_graph,
            "sample_words": list(words)[:20]
        }

    def get_learning_tip(self, word: str) -> Optional[str]:
        """
        Get a learning tip for a word.
        Returns educational context about the word.
        """
        word = word.upper()

        # Check which categories the word belongs to
        categories = []
        for cat, words in self.words_by_category.items():
            if word in words:
                categories.append(cat)

        if not categories:
            return None

        # Generate educational context based on category
        tips = {
            WordCategory.SCIENCE: f"'{word}' is a science term. Think about how it relates to scientific concepts!",
            WordCategory.BIOLOGY: f"'{word}' is used in biology. Consider its connection to living organisms!",
            WordCategory.PHYSICS: f"'{word}' is a physics term. How does it relate to forces, energy, or motion?",
            WordCategory.EDUCATION: f"'{word}' is an educational term. It's commonly used in learning contexts!",
            WordCategory.GENERAL: f"'{word}' is a common word. Great for building vocabulary chains!",
        }

        return tips.get(categories[0])

    def _get_default_words(self) -> List[str]:
        """Get a default word list for the game."""
        # Common 3-4 letter words that form good chains
        return [
            # 3-letter words
            "CAT", "BAT", "HAT", "RAT", "SAT", "MAT", "PAT", "FAT", "VAT",
            "COT", "COW", "HOW", "NOW", "BOW", "ROW", "SOW", "TOW", "LOW", "MOW",
            "DOG", "LOG", "FOG", "HOG", "JOG", "BOG", "COG",
            "BIG", "DIG", "FIG", "GIG", "JIG", "PIG", "RIG", "WIG",
            "BIT", "FIT", "HIT", "KIT", "LIT", "PIT", "SIT", "WIT",
            "CUT", "GUT", "HUT", "JUT", "NUT", "PUT", "RUT", "TUT",
            "BED", "FED", "LED", "RED", "WED",
            "BET", "GET", "JET", "LET", "MET", "NET", "PET", "SET", "VET", "WET", "YET",
            "DEN", "HEN", "MEN", "PEN", "TEN", "ZEN",
            "CAN", "BAN", "FAN", "MAN", "PAN", "RAN", "TAN", "VAN",
            "TOP", "COP", "HOP", "MOP", "POP", "SOP",
            "TON", "CON", "SON", "WON",
            "TOE", "FOE", "HOE", "JOE", "ROE", "WOE",
            "TIP", "DIP", "HIP", "LIP", "NIP", "RIP", "SIP", "ZIP",
            "TAP", "CAP", "GAP", "LAP", "MAP", "NAP", "RAP", "SAP", "ZAP",
            "TIN", "BIN", "DIN", "FIN", "GIN", "KIN", "PIN", "SIN", "WIN",
            "AIR", "FAIR", "HAIR", "PAIR",
            "AGE", "CAGE", "PAGE", "RAGE", "SAGE", "WAGE",
            "ACE", "FACE", "LACE", "PACE", "RACE",
            "ADE", "FADE", "JADE", "MADE", "WADE",
            # 4-letter words
            "CAKE", "BAKE", "FAKE", "LAKE", "MAKE", "RAKE", "SAKE", "TAKE", "WAKE",
            "CAME", "DAME", "FAME", "GAME", "LAME", "NAME", "SAME", "TAME",
            "CARE", "BARE", "DARE", "FARE", "HARE", "MARE", "PARE", "RARE", "WARE",
            "CASE", "BASE", "VASE",
            "CAST", "FAST", "LAST", "MAST", "PAST", "VAST",
            "COLD", "BOLD", "FOLD", "GOLD", "HOLD", "MOLD", "SOLD", "TOLD",
            "COOL", "FOOL", "POOL", "TOOL", "WOOL",
            "COPE", "DOPE", "HOPE", "MOPE", "POPE", "ROPE",
            "CORE", "BORE", "FORE", "MORE", "PORE", "SORE", "TORE", "WORE",
            "COST", "HOST", "LOST", "MOST", "POST",
            "DATE", "FATE", "GATE", "HATE", "LATE", "MATE", "RATE",
            "DAZE", "FAZE", "GAZE", "HAZE", "MAZE", "RAZE",
            "DEAL", "HEAL", "MEAL", "PEAL", "REAL", "SEAL", "TEAL", "ZEAL",
            "DEAR", "BEAR", "FEAR", "GEAR", "HEAR", "NEAR", "PEAR", "REAR", "SEAR", "TEAR", "WEAR", "YEAR",
            "FAIL", "BAIL", "HAIL", "JAIL", "MAIL", "NAIL", "PAIL", "RAIL", "SAIL", "TAIL", "WAIL",
            "FALL", "BALL", "CALL", "HALL", "MALL", "TALL", "WALL",
            "FEEL", "HEEL", "KEEL", "PEEL", "REEL",
            "FILE", "BILE", "MILE", "PILE", "RILE", "TILE", "VILE", "WILE",
            "FILL", "BILL", "DILL", "GILL", "HILL", "KILL", "MILL", "PILL", "WILL",
            "FIND", "BIND", "HIND", "KIND", "MIND", "RIND", "WIND",
            "FIRE", "HIRE", "MIRE", "TIRE", "WIRE",
            "FISH", "DISH", "WISH",
            "HEAD", "BEAD", "DEAD", "LEAD", "MEAD", "READ",
            "HEAT", "BEAT", "FEAT", "MEAT", "NEAT", "PEAT", "SEAT",
            "LAND", "BAND", "HAND", "SAND",
            "LEAD", "BEAD", "DEAD", "HEAD", "MEAD", "READ",
            "LEND", "BEND", "FEND", "MEND", "REND", "SEND", "TEND", "VEND", "WEND",
            "LINE", "BINE", "DINE", "FINE", "MINE", "NINE", "PINE", "VINE", "WINE",
            "LINK", "BINK", "KINK", "MINK", "PINK", "RINK", "SINK", "WINK",
            "LOAD", "GOAD", "ROAD", "TOAD",
            "LOCK", "DOCK", "HOCK", "MOCK", "ROCK", "SOCK",
            "LOOK", "BOOK", "COOK", "HOOK", "NOOK", "ROOK", "TOOK",
            "PASS", "BASS", "LASS", "MASS",
            "PATH", "BATH", "MATH",
            "PLAN", "BLAN", "CLAN", "FLAN", "SCAN",
            "PLAY", "CLAY", "FLAY", "SLAY", "STAY",
            "TEST", "BEST", "FEST", "JEST", "NEST", "PEST", "REST", "VEST", "WEST", "ZEST",
            "WORD", "CORD", "FORD", "LORD",
            "WORK", "CORK", "FORK", "PORK", "YORK",
            # Educational/SAM words
            "GOAL", "COAL", "FOAL",
            "TASK", "BASK", "CASK", "MASK",
            "STEP", "PREP",
            "FORM", "DORM", "NORM", "WORM",
            "RULE", "MULE",
            "NOTE", "DOTE", "MOTE", "ROTE", "TOTE", "VOTE",
            "MODE", "BODE", "CODE", "NODE", "RODE",
        ]


# Global word graph instance (loaded once on startup)
word_graph = WordGraph()


def get_word_graph() -> WordGraph:
    """Get the global word graph instance."""
    return word_graph


def initialize_word_graph(dictionary_path: Optional[str] = None) -> int:
    """
    Initialize the word graph with dictionary files.

    If dictionary_path points to a directory, loads category files.
    If it's a file, loads that file.
    If None, uses default words.
    """
    global word_graph

    # Try to load category files from data/words directory
    words_dir = Path(__file__).parent.parent.parent / "data" / "words"

    if words_dir.exists() and words_dir.is_dir():
        counts = word_graph.load_category_dictionaries(str(words_dir))
        total = sum(counts.values())
        print(f"📚 Loaded words by category: {counts}")

        # Also load rich word definitions
        definitions_file = words_dir / "word_definitions.json"
        if definitions_file.exists():
            word_graph.load_definitions_json(str(definitions_file))

        return total
    elif dictionary_path:
        return word_graph.load_dictionary(dictionary_path)
    else:
        return word_graph.load_from_list(word_graph._get_default_words())
