"""
Utils — shared string operations, similarity, and validation helpers.

Low-level building blocks reused by text_matcher, text_parser,
text_dummy, and text_anonymizer.

Quick start::

    from shadetriptxt.utils import levenshtein_score, is_valid_iban

    score = levenshtein_score("hello", "helo")
    print(is_valid_iban("ES9121000418450200051332"))
"""

from ._locale import BaseLocaleProfile

from .string_ops import (
    flat_vowels,
    normalize_spaces,
    erase_allspaces,
    normalize_symbols,
    erase_specialchar,
    fix_spanish,
    string_filter,
    string_aZ,
    string_aZ09,
    reorder_comma_fullname,
    split_all,
    get_in_text_by_pattern,
    normalize_phone,
)

from .string_similarity import (
    levenshtein_score,
    jaro_winkler_score,
    jaccard_similarity,
    sorensen_dice_coefficient,
    ratcliff_obershelp_score,
    lcs_score,
    mra_similarity,
    soundex,
    metaphone,
    double_metaphone,
    are_words_equivalent,
    calculate_similarity,
    string_distance_hamming,
)

from .string_validation import (
    luhn_checksum,
    is_valid_luhn,
    ean13_check_digit,
    is_valid_iban,
    is_valid_isbn,
    is_valid_credit_card,
    is_valid_vat,
    is_valid_ean,
    is_valid_swift_bic,
    data_type_inference,
    is_valid_phone_format,
    email_domain_type,
    has_mixed_case_anomaly,
    contains_repeated_words,
    detect_mixed_scripts,
    homoglyph_risk_score,
)
