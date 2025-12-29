"""Configuration package for post-processing features."""

# Post-processing feature flags
ENABLE_LEXICON_REPLACEMENT = True  # Enable lexicon-based term corrections
ENABLE_TEXT_CLEANUP = True          # Enable text cleanup and normalization
ENABLE_NUMERAL_HANDLING = True      # Enable Persian/English numeral conversion
ENABLE_GPT_CLEANUP = True           # Enable GPT-4o-mini post-processing cleanup

# Fuzzy matching configuration
ENABLE_FUZZY_MATCHING = True        # Enable fuzzy matching for lexicon corrections
FUZZY_MATCH_THRESHOLD = 85          # Minimum similarity score (0-100) for fuzzy matches
