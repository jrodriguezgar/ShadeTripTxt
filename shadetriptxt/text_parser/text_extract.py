"""
Module for extracting various content from text strings.

This module provides a TextExtractor class to extract phone numbers, postal codes, emails, URLs, and other content from input strings.
The class allows configuration of separators for flexible extraction.
"""

import re
from ..utils import string_ops


def _import_string_operations():
    """Lazy loader for string_operations."""
    return string_ops.get_in_text_by_pattern, string_ops.split_all


class TextExtractor:
    """
    A class for extracting various types of content from text strings.

    Allows configuration of separators to customize extraction behavior.
    """

    # Compile regex patterns once for efficiency, as they are static.
    # \b ensures a "word boundary", so it matches whole numbers.
    _POSTAL_CODE_5_DIGIT_PATTERN = re.compile(r"\b\d{5}\b")
    _POSTAL_CODE_4_DIGIT_PATTERN = re.compile(r"\b\d{4}\b")

    def __init__(self, separators=None):
        """
        Initializes the TextExtractor with configurable separators.

        Args:
            separators (str, list, or 'all', optional): The separators to use.
                - If str: use that string as separators.
                - If list: join the list into a string.
                - If 'all': use a comprehensive set of separators.
                - If None: use default separators.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor(separators=[' ', '-', '(', ')'])
            # or TextExtractor(separators=' -()')
            # or TextExtractor(separators='all')
        """
        if separators == "all":
            self.separators = " \t\n\r\f\v-()./,;:!?@#$%^&*+="  # comprehensive separators
        elif isinstance(separators, list):
            self.separators = "".join(separators)
        elif isinstance(separators, str):
            self.separators = separators
        else:
            self.separators = " \t\n\r\f\v-()."  # default

        # Lazy load string utility functions
        get_in_text_by_pattern, split_all = _import_string_operations()
        self._get_in_text_by_pattern = get_in_text_by_pattern
        self._split_all = split_all

    # ==================== Generic Purpose ====================
    def extract_from_parentheses(self, text: str) -> list[str] | None:
        """
        Extracts substrings enclosed in parentheses from the input text.

        Identifies text enclosed within parentheses, including the parentheses themselves.

        Args:
            text (str): The input text to search for substrings in parentheses.

        Returns:
            list[str] or None: A list of found substrings enclosed in parentheses if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            parentheses = extractor.extract_from_parentheses("This is (an example) and (another one)")
            # Returns: ['(an example)', '(another one)']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        # Use internal utility to get the content inside parentheses
        contents = self._get_in_text_by_pattern(text, "text_in_parentheses")
        # Reconstruct the full strings with parentheses
        full_matches = [f"({content})" for content in contents]
        return full_matches if full_matches else None

    def tokenize(self, text: str) -> list[str] | None:
        """
        Tokenizes the input text into a list of words or tokens.

        Uses the split_all function from internal utilities to split the text based on comprehensive delimiters,
        including punctuation, symbols, and whitespace.

        Args:
            text (str): The input text to tokenize.

        Returns:
            list[str] or None: A list of tokens if any are found, otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            tokens = extractor.tokenize("Hello, world! This is a test.")
            # Returns: ['Hello', 'world', 'This', 'is', 'a', 'test']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        tokens = self._split_all(text)
        return tokens if tokens else None

    def extract_phones(self, text: str, pattern: str | None = None) -> list[str] | None:
        r"""
        Extracts potential phone numbers from a string.

        A phone number is identified as a sequence of digits that:
        1. Is at least 5 digits long after removing common phone number delimiters
           (spaces, hyphens, parentheses, dots) and configured separators.
        2. May optionally start with a '+' sign.
        3. May contain common phone number delimiters internally.

        If a custom `pattern` is provided, it is used as the regex instead of the
        default phone detection logic, allowing extraction of phone numbers that
        match a specific format.

        Args:
            text (str): The input string to parse for phone numbers.
            pattern (str, optional): A custom regex pattern to use instead of
                the default phone extraction logic. When provided, all matches
                of this pattern are returned directly without digit-length
                filtering. Defaults to None (use default behavior).

        Returns:
            list[str] or None: A list of cleaned phone numbers (digits only) if found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            phones = extractor.extract_phones("Call me at +1-234-567-8901 or 123 456 7890")
            # Returns: ['12345678901', '1234567890']

            # With custom pattern (only Spanish mobile numbers starting with 6):
            phones = extractor.extract_phones("Llama al 612345678 o al 912345678", pattern=r'\b6\d{8}\b')
            # Returns: ['612345678']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return text

        # If a custom pattern is provided, use it directly
        if pattern is not None:
            custom_re = re.compile(pattern)
            matches = custom_re.findall(text)
            return matches if matches else None

        # Define characters that are allowed within a phone number string but should be stripped
        # for the final digit-only output. This includes common phone number separators
        # and the configured separators.
        allowed_internal_chars = re.escape(" \t\n\r\f\v-()." + self.separators)

        # Regex pattern to find potential phone number candidates:
        # - \+? : Optionally starts with a '+' sign (for international numbers).
        # - \d : Must contain at least one digit to start the sequence.
        # - [\d' + allowed_internal_chars + ']* : Followed by zero or more characters that are
        #                                         digits OR any of the allowed internal delimiters.
        # - \d : Must end with a digit (to avoid capturing strings like "word-").
        # This pattern captures a broader string that *looks* like a phone number,
        # including its formatting characters.
        phone_candidate_pattern = r"\+?\d[" + allowed_internal_chars + r"\d]*\d"

        # Find all occurrences of the phone candidate pattern in the input string.
        potential_phone_strings = re.findall(phone_candidate_pattern, text)

        found_phones = []
        for candidate_str in potential_phone_strings:
            # Clean the extracted string: remove all non-digit characters.
            # This gives us the pure digit sequence of the potential phone number.
            cleaned_digits = re.sub(r"\D", "", candidate_str)  # \D matches any non-digit character

            # Filter by minimum length. The original function used a minimum of 5 digits.
            if len(cleaned_digits) >= 5:
                found_phones.append(cleaned_digits)

        # Return the list of found phone numbers, or None if no valid numbers were found.
        if not found_phones:
            return None
        else:
            return found_phones

    def extract_emails(self, text: str) -> list[str] | None:
        """
        Extracts email addresses from the input text.

        Uses a regular expression to identify strings that match the typical email format.

        Args:
            text (str): The input text to search for email addresses.

        Returns:
            list[str] or None: A list of found email addresses if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            emails = extractor.extract_emails("Contact support@example.com or sales@company.org")
            # Returns: ['support@example.com', 'sales@company.org']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        emails = self._get_in_text_by_pattern(text, "broad_email")
        return emails if emails else None

    def extract_mentions(self, text: str) -> list[str] | None:
        """
        Extracts mentions from the input text.

        Identifies strings starting with @ followed by word characters, like @username.

        Args:
            text (str): The input text to search for mentions.

        Returns:
            list[str] or None: A list of found mentions if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            mentions = extractor.extract_mentions("Hello @user and @admin")
            # Returns: ['@user', '@admin']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        mention_pattern = re.compile(r"@\w+")
        mentions = mention_pattern.findall(text)
        return mentions if mentions else None

    # ==================== Financial ====================

    def extract_currency(self, text: str) -> list[str] | None:
        """
        Extracts currency amounts from the input text.

        Identifies strings starting with currency symbols followed by numbers.

        Args:
            text (str): The input text to search for currency amounts.

        Returns:
            list[str] or None: A list of found currency strings if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            currencies = extractor.extract_currency("Price is $100.50 or €50")
            # Returns: ['$100.50', '€50']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        currency_pattern = re.compile(r"\b[$€£¥]\d+(?:\.\d{2})?\b")
        currencies = currency_pattern.findall(text)
        return currencies if currencies else None

    def extract_credit_cards(self, text: str) -> list[str] | None:
        """
        Extracts credit card numbers from the input text.

        Identifies 16-digit numbers, optionally with spaces or hyphens.

        Args:
            text (str): The input text to search for credit card numbers.

        Returns:
            list[str] or None: A list of found credit card numbers if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            cards = extractor.extract_credit_cards("Card 1234-5678-9012-3456")
            # Returns: ['1234-5678-9012-3456']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        card_pattern = re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b")
        cards = card_pattern.findall(text)
        return cards if cards else None

    def extract_ibans(self, text: str) -> list[str] | None:
        """
        Extracts IBAN codes from the input text.

        Identifies strings matching the IBAN format: 2 letters, 2 digits, then up to 30 alphanumeric.

        Args:
            text (str): The input text to search for IBANs.

        Returns:
            list[str] or None: A list of found IBANs if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            ibans = extractor.extract_ibans("Account IBAN ES9121000418450200051332")
            # Returns: ['ES9121000418450200051332']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        iban_pattern = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{1,30}\b")
        ibans = iban_pattern.findall(text)
        return ibans if ibans else None

    def extract_swift_bic(self, text: str) -> list[str] | None:
        """
        Extracts SWIFT BIC codes from the input text.

        Identifies 8 or 11 character codes starting with 6 letters.

        Args:
            text (str): The input text to search for SWIFT BICs.

        Returns:
            list[str] or None: A list of found BICs if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            bics = extractor.extract_swift_bic("Bank BIC ABCDUS33XXX")
            # Returns: ['ABCDUS33XXX']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        bic_pattern = re.compile(r"\b[A-Z]{6}[A-Z0-9]{2}(?:[A-Z0-9]{3})?\b")
        bics = bic_pattern.findall(text)
        return bics if bics else None

    # ==================== Identifiers ====================

    def extract_postal_codes(self, text: str, pattern: str | None = None) -> list[str] | None:
        r"""
        Extracts 5-digit or 4-digit postal codes from an address string.

        It first attempts to find all 5-digit number sequences that are whole "words".
        If no 5-digit codes are found, it then attempts to find all 4-digit number
        sequences that are whole "words".

        If a custom `pattern` is provided, it is used as the regex instead of the
        default postal code detection logic.

        Args:
            text (str): The input address string.
            pattern (str, optional): A custom regex pattern to use instead of
                the default postal code logic. Defaults to None.

        Returns:
            list[str] or None: A list of found postal codes (as strings).
                               Returns an empty list if no codes are found.
                               Returns None if the input `text` is None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            codes = extractor.extract_postal_codes("123 Main St, Anytown, 12345 USA")
            # Returns: ['12345']

            # With custom pattern (UK postcodes):
            codes = extractor.extract_postal_codes("Address SW1A 1AA London", pattern=r'\b[A-Z]{1,2}\d[A-Z\d]?\s*\d[A-Z]{2}\b')
            # Returns: ['SW1A 1AA']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        # Ensure text is treated as a string, in case it's a number or other type.
        address_str = str(text)

        # If a custom pattern is provided, use it directly
        if pattern is not None:
            custom_re = re.compile(pattern)
            found_codes = custom_re.findall(address_str)
            return found_codes if found_codes else None

        # First, try to find 5-digit postal codes
        found_codes = self._POSTAL_CODE_5_DIGIT_PATTERN.findall(address_str)

        if not found_codes:
            # If no 5-digit codes are found, try to find 4-digit postal codes
            found_codes = self._POSTAL_CODE_4_DIGIT_PATTERN.findall(address_str)

        # Return the list of found codes. If no codes are found, findall returns an empty list.
        return found_codes

    def extract_custom_ids(self, text: str) -> list[str] | None:
        """
        Extracts custom ID strings from the input text.

        Identifies strings that look like IDs, such as uppercase letters followed by digits.

        Args:
            text (str): The input text to search for custom IDs.

        Returns:
            list[str] or None: A list of found ID strings if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            ids = extractor.extract_custom_ids("User ID123 and REF456")
            # Returns: ['ID123', 'REF456']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        id_pattern = re.compile(r"\b[A-Z]+\d+\b")
        ids = id_pattern.findall(text)
        return ids if ids else None

    def extract_patient_ids(self, text: str) -> list[str] | None:
        """
        Extracts patient IDs from the input text.

        Identifies strings like PAT-12345 or similar custom formats.

        Args:
            text (str): The input text to search for patient IDs.

        Returns:
            list[str] or None: A list of found patient IDs if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            pids = extractor.extract_patient_ids("Patient PAT-12345")
            # Returns: ['PAT-12345']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        pid_pattern = re.compile(r"\bPAT-\d+\b")
        pids = pid_pattern.findall(text)
        return pids if pids else None

    def extract_nif(self, text: str) -> list[str] | None:
        """
        Extracts Spanish NIF numbers from the input text.

        Identifies 8 digits followed by a letter.

        Args:
            text (str): The input text to search for NIFs.

        Returns:
            list[str] or None: A list of found NIFs if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            nifs = extractor.extract_nif("NIF 12345678A")
            # Returns: ['12345678A']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        nif_pattern = re.compile(r"\b\d{8}[A-Z]\b")
        nifs = nif_pattern.findall(text)
        return nifs if nifs else None

    def extract_social_security(self, text: str) -> list[str] | None:
        """
        Extracts Social Security Numbers from the input text.

        Identifies strings in the format XXX-XX-XXXX.

        Args:
            text (str): The input text to search for SSNs.

        Returns:
            list[str] or None: A list of found SSNs if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            ssns = extractor.extract_social_security("SSN 123-45-6789")
            # Returns: ['123-45-6789']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        ssn_pattern = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
        ssns = ssn_pattern.findall(text)
        return ssns if ssns else None

    # ==================== Technical/Programming ====================

    def extract_ip_addresses(self, text: str) -> list[str] | None:
        """
        Extracts IPv4 addresses from the input text.

        Uses a regular expression to identify strings that match the IPv4 format.

        Args:
            text (str): The input text to search for IP addresses.

        Returns:
            list[str] or None: A list of found IP addresses if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            ips = extractor.extract_ip_addresses("Server at 192.168.1.1 and 10.0.0.1")
            # Returns: ['192.168.1.1', '10.0.0.1']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        ips = self._get_in_text_by_pattern(text, "ipv4_address")
        # Validate that each is a valid IP (0-255), but for simplicity, return as is
        return ips if ips else None

    def extract_checksums(self, text: str) -> list[str] | None:
        """
        Extracts checksum strings from the input text.

        Identifies hexadecimal strings of common lengths (MD5: 32, SHA1: 40, etc.).

        Args:
            text (str): The input text to search for checksums.

        Returns:
            list[str] or None: A list of found checksums if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            checksums = extractor.extract_checksums("Hash a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3")
            # Returns: ['a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        checksum_pattern = re.compile(r"\b[a-fA-F0-9]{32,64}\b")
        checksums = checksum_pattern.findall(text)
        return checksums if checksums else None

    def extract_cve_ids(self, text: str) -> list[str] | None:
        """
        Extracts CVE IDs from the input text.

        Identifies strings in the format CVE-YYYY-NNNN.

        Args:
            text (str): The input text to search for CVE IDs.

        Returns:
            list[str] or None: A list of found CVE IDs if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            cves = extractor.extract_cve_ids("Vulnerability CVE-2023-1234")
            # Returns: ['CVE-2023-1234']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        cve_pattern = re.compile(r"\bCVE-\d{4}-\d{4,7}\b")
        cves = cve_pattern.findall(text)
        return cves if cves else None

    def extract_version_numbers(self, text: str) -> list[str] | None:
        """
        Extracts version numbers from the input text.

        Identifies strings like 1.0.0 or 2.1.3.4.

        Args:
            text (str): The input text to search for version numbers.

        Returns:
            list[str] or None: A list of found version numbers if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            versions = extractor.extract_version_numbers("Version 1.2.3 and 4.0.1")
            # Returns: ['1.2.3', '4.0.1']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        version_pattern = re.compile(r"\b\d+(?:\.\d+)+\b")
        versions = version_pattern.findall(text)
        return versions if versions else None

    def extract_patent_numbers(self, text: str) -> list[str] | None:
        """
        Extracts patent numbers from the input text.

        Identifies strings like US1234567A1 or EP1234567B1.

        Args:
            text (str): The input text to search for patent numbers.

        Returns:
            list[str] or None: A list of found patent numbers if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            patents = extractor.extract_patent_numbers("Patent US1234567A1")
            # Returns: ['US1234567A1']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        patent_pattern = re.compile(r"\b[A-Z]{2}\d+[A-Z]\d+\b")
        patents = patent_pattern.findall(text)
        return patents if patents else None

    def extract_isbns(self, text: str) -> list[str] | None:
        """
        Extracts ISBN numbers from the input text.

        Identifies ISBN-10 (9 digits + X) or ISBN-13 (13 digits).

        Args:
            text (str): The input text to search for ISBNs.

        Returns:
            list[str] or None: A list of found ISBNs if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            isbns = extractor.extract_isbns("Book ISBN 123456789X and 9781234567890")
            # Returns: ['123456789X', '9781234567890']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        isbn_pattern = re.compile(r"\b(?:\d{9}[\dX]|\d{13})\b")
        isbns = isbn_pattern.findall(text)
        return isbns if isbns else None

    # ==================== Text Structure ====================

    def extract_urls(self, text: str) -> list[str] | None:
        """
        Extracts URLs from the input text.

        Uses a regular expression to identify strings that match common URL patterns,
        including HTTP and HTTPS.

        Args:
            text (str): The input text to search for URLs.

        Returns:
            list[str] or None: A list of found URLs if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            urls = extractor.extract_urls("Visit https://www.example.com or http://test.org/page")
            # Returns: ['https://www.example.com', 'http://test.org/page']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        urls = self._get_in_text_by_pattern(text, "basic_url")
        return urls if urls else None

    def extract_hashtags(self, text: str) -> list[str] | None:
        """
        Extracts hashtags from the input text.

        Identifies strings starting with # followed by word characters.

        Args:
            text (str): The input text to search for hashtags.

        Returns:
            list[str] or None: A list of found hashtags if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            hashtags = extractor.extract_hashtags("Check #Python and #AI")
            # Returns: ['#Python', '#AI']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        hashtag_pattern = re.compile(r"#\w+")
        hashtags = hashtag_pattern.findall(text)
        return hashtags if hashtags else None

    def extract_quotations(self, text: str) -> list[str] | None:
        """
        Extracts quoted strings from the input text.

        Identifies text enclosed in double or single quotes.

        Args:
            text (str): The input text to search for quotations.

        Returns:
            list[str] or None: A list of found quotations if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            quotes = extractor.extract_quotations('He said "Hello" and \'Goodbye\'')
            # Returns: ['"Hello"', "'Goodbye'"]

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        quote_pattern = re.compile(r'(["\'])(.*?)\1')
        quotes = quote_pattern.findall(text)
        # findall returns list of tuples, take the full match
        quotations = [f"{q[0]}{q[1]}{q[0]}" for q in quotes]
        return quotations if quotations else None

    def extract_paragraphs(self, text: str) -> list[str] | None:
        """
        Extracts paragraphs from the input text.

        Splits the text by double newlines and returns non-empty paragraphs.

        Args:
            text (str): The input text to split into paragraphs.

        Returns:
            list[str] or None: A list of paragraphs if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            paragraphs = extractor.extract_paragraphs("Para 1\n\nPara 2")
            # Returns: ['Para 1', 'Para 2']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        return paragraphs if paragraphs else None

    def extract_classification_tags(self, text: str) -> list[str] | None:
        """
        Extracts classification tags from the input text.

        Identifies strings enclosed in square brackets, like [CONFIDENTIAL].

        Args:
            text (str): The input text to search for tags.

        Returns:
            list[str] or None: A list of found tags if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            tags = extractor.extract_classification_tags("Document [SECRET] info")
            # Returns: ['[SECRET]']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        tag_pattern = re.compile(r"\[.*?\]")
        tags = tag_pattern.findall(text)
        return tags if tags else None

    # ==================== Numeric and Units ====================

    def extract_numeric(self, text: str, pattern: str | None = None) -> list[str] | None:
        r"""
        Extracts numeric values from the input text.

        Identifies sequences of digits, optionally with decimals.
        If a custom `pattern` is provided, it is used as the regex instead of the
        default numeric detection, allowing extraction of numbers matching a
        specific format (e.g., only integers, only 4-digit numbers, etc.).

        Args:
            text (str): The input text to search for numeric values.
            pattern (str, optional): A custom regex pattern to use instead of
                the default numeric extraction. Defaults to None (extract all
                numbers).

        Returns:
            list[str] or None: A list of found numeric strings if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            numbers = extractor.extract_numeric("There are 123 apples and 45.67 oranges")
            # Returns: ['123', '45.67']

            # With custom pattern (only 3-digit integers):
            numbers = extractor.extract_numeric("Codes 123 and 4567 and 89", pattern=r'\b\d{3}\b')
            # Returns: ['123']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        if pattern is not None:
            custom_re = re.compile(pattern)
            numbers = custom_re.findall(text)
            return numbers if numbers else None

        numeric_pattern = re.compile(r"\b\d+(?:\.\d+)?\b")
        numbers = numeric_pattern.findall(text)
        return numbers if numbers else None

    def extract_numeric_units(self, text: str, pattern: str | None = None) -> list[str] | None:
        r"""
        Extracts numeric values with units from the input text.

        Identifies numbers followed by alphabetic units.
        If a custom `pattern` is provided, it is used as the regex instead of the
        default detection, allowing extraction of specific unit formats.

        Args:
            text (str): The input text to search for numeric units.
            pattern (str, optional): A custom regex pattern to use instead of
                the default numeric unit extraction. Defaults to None.

        Returns:
            list[str] or None: A list of found numeric unit strings if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            units = extractor.extract_numeric_units("Weight 10kg and height 5m")
            # Returns: ['10kg', '5m']

            # With custom pattern (only kg units):
            units = extractor.extract_numeric_units("Weight 10kg and height 5m", pattern=r'\b\d+(?:\.\d+)?\s*kg\b')
            # Returns: ['10kg']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        if pattern is not None:
            custom_re = re.compile(pattern)
            units = custom_re.findall(text)
            return units if units else None

        unit_pattern = re.compile(r"\b\d+(?:\.\d+)?\s*[a-zA-Z]+\b")
        units = unit_pattern.findall(text)
        return units if units else None

    def extract_percentages(self, text: str, pattern: str | None = None) -> list[str] | None:
        r"""
        Extracts percentages from the input text.

        Identifies numbers followed by a percent sign.
        If a custom `pattern` is provided, it is used as the regex instead of the
        default detection.

        Args:
            text (str): The input text to search for percentages.
            pattern (str, optional): A custom regex pattern to use instead of
                the default percentage extraction. Defaults to None.

        Returns:
            list[str] or None: A list of found percentage strings if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            percentages = extractor.extract_percentages("Discount is 20% off and tax 8.5%")
            # Returns: ['20%', '8.5%']

            # With custom pattern (only integer percentages):
            percentages = extractor.extract_percentages("20% and 8.5%", pattern=r'\b\d+%')
            # Returns: ['20%', '8%']  # note: depends on the pattern precision

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        if pattern is not None:
            custom_re = re.compile(pattern)
            percentages = custom_re.findall(text)
            return percentages if percentages else None

        percentage_pattern = re.compile(r"\b\d+(?:\.\d+)?%\b")
        percentages = percentage_pattern.findall(text)
        return percentages if percentages else None

    def extract_dates(self, text: str, pattern: str | None = None) -> list[str] | None:
        r"""
        Extracts date strings from the input text.

        Identifies common date formats like DD/MM/YYYY or MM-DD-YY.
        If a custom `pattern` is provided, it is used as the regex instead of the
        default date detection, allowing extraction of dates in a specific format
        (e.g., only ISO format YYYY-MM-DD, or only DD/MM/YYYY).

        Args:
            text (str): The input text to search for dates.
            pattern (str, optional): A custom regex pattern to use instead of
                the default date extraction. Defaults to None (extract all
                common date formats).

        Returns:
            list[str] or None: A list of found date strings if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            dates = extractor.extract_dates("Event on 01/10/2023 and 2023-10-01")
            # Returns: ['01/10/2023', '2023-10-01']

            # With custom pattern (only ISO dates YYYY-MM-DD):
            dates = extractor.extract_dates("01/10/2023 and 2023-10-01", pattern=r'\b\d{4}-\d{2}-\d{2}\b')
            # Returns: ['2023-10-01']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        if pattern is not None:
            custom_re = re.compile(pattern)
            dates = custom_re.findall(text)
            return dates if dates else None

        date_pattern = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b")
        dates = date_pattern.findall(text)
        return dates if dates else None

    def extract_times(self, text: str, pattern: str | None = None) -> list[str] | None:
        r"""
        Extracts time strings from the input text.

        Identifies times in HH:MM format, optionally with AM/PM.
        If a custom `pattern` is provided, it is used as the regex instead of the
        default time detection.

        Args:
            text (str): The input text to search for times.
            pattern (str, optional): A custom regex pattern to use instead of
                the default time extraction. Defaults to None.

        Returns:
            list[str] or None: A list of found time strings if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            times = extractor.extract_times("Meeting at 14:30 and 2:30 PM")
            # Returns: ['14:30', '2:30']

            # With custom pattern (only 24h format HH:MM:SS):
            times = extractor.extract_times("At 14:30:00 and 2:30 PM", pattern=r'\b\d{2}:\d{2}:\d{2}\b')
            # Returns: ['14:30:00']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        if pattern is not None:
            custom_re = re.compile(pattern)
            times = custom_re.findall(text)
            return times if times else None

        time_pattern = re.compile(r"\b\d{1,2}:\d{2}(?:\s?[AP]M)?\b")
        times = time_pattern.findall(text)
        return times if times else None

    # ==================== Security ====================

    def extract_passwords(self, text: str) -> list[str] | None:
        """
        Extracts potential password strings from the input text.

        Identifies strings that look like passwords (alphanumeric with special chars, length >6).

        Args:
            text (str): The input text to search for passwords.

        Returns:
            list[str] or None: A list of found passwords if any are found,
                               otherwise None.

        Raises:
            None

        Example Usage:
            extractor = TextExtractor()
            passwords = extractor.extract_passwords("Password: P@ssw0rd123")
            # Returns: ['P@ssw0rd123']

        Cost:
            O(n), where n is the length of the input string.
        """
        if text is None:
            return None

        # Simple pattern: at least 6 chars, mix of letters, digits, special
        password_pattern = re.compile(r"\b(?=.*[a-zA-Z])(?=.*\d)(?=.*[!@#$%^&*])[a-zA-Z\d!@#$%^&*]{6,}\b")
        passwords = password_pattern.findall(text)
        return passwords if passwords else None


def get_string_between(text: str, delimiter: str) -> str:
    """
    Extracts the substring between the first and second occurrence of the specified delimiter.

    This function finds the text enclosed between two instances of the delimiter string.
    If the delimiter appears less than twice, it returns an empty string.

    Args:
        text (str): The input string from which to extract the substring.
        delimiter (str): The delimiter string that marks the boundaries of the substring.

    Returns:
        str: The substring between the first and second delimiter occurrences.
             Returns an empty string if the delimiter is not found at least twice.

    Raises:
        None

    Example Usage:
        sentence = "El texto 'entre comillas' es importante."
        result = get_string_between(sentence, "'")
        # Returns: "entre comillas"

    Cost:
        O(n), where n is the length of the input string.
    """
    start_index = text.find(delimiter)
    if start_index == -1:
        return ""
    end_index = text.find(delimiter, start_index + len(delimiter))
    if end_index == -1:
        return ""
    return text[start_index + len(delimiter) : end_index]
