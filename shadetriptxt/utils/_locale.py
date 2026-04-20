"""Base locale profile shared across all ShadeTripTxt modules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BaseLocaleProfile:
    """Common locale fields shared by all module-specific profiles.

    Every module (text_dummy, text_parser, text_anonymizer) defines its own
    locale profile that inherits from this base, adding domain-specific
    fields.  The three shared fields enable cross-module type checks::

        from shadetriptxt.utils._locale import BaseLocaleProfile

        isinstance(profile, BaseLocaleProfile)  # True for any module profile

    Attributes:
        code: IETF locale tag, e.g. `"es_ES"`, `"en_US"`.
        country: Human-readable country name.
        language: Human-readable language name (or ISO 639-1 code).
    """

    code: str
    country: str
    language: str
