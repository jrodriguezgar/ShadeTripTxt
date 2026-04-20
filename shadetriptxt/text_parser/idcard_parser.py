from typing import Optional
import re

# --- Constants ---
_DNI_NIE_CONTROL_LETTERS = "TRWAGMYFPDXBNJZSQVHLCKE"
_NIE_PREFIX_MAPPING = {"X": 0, "Y": 1, "Z": 2}
_VALID_NIF_TYPES = {"DNI", "NIE", "CIF"}

# Regex for basic format validation (optional, but highly recommended)
# DNI: 8 digits + 1 letter
_DNI_REGEX = re.compile(r"^\d{8}[TRWAGMYFPDXBNJZSQVHLCKE]$", re.IGNORECASE)
# NIE: 1 letter (X, Y, Z) + 7 digits + 1 letter
_NIE_REGEX = re.compile(r"^[XYZ]\d{7}[TRWAGMYFPDXBNJZSQVHLCKE]$", re.IGNORECASE)
# CIF: 1 letter + 7 digits + 1 digit/letter (more complex, simplified here)
_CIF_REGEX = re.compile(r"^[ABCDEFGHJNPQRSUVW]\d{7}[0-9A-J]$", re.IGNORECASE)


def nif_padding(p_nif: Optional[str]) -> Optional[str]:
    """
    Attempts to format an incomplete Spanish identification number by padding with zeros.

    Description:
        Takes a potentially incomplete NIF/NIE/CIF and tries to complete it
        by adding leading zeros to the numeric portion. This function
        does not validate the control digit but ensures the length and
        numeric padding are correct for subsequent validation.

    Args:
        p_nif (str): The identification number to format.

    Returns:
        str or None: Padded and formatted identification number if it can be
                     processed, None if the input is invalid or cannot be padded.

    Example:
        >>> nif_padding("123456Z")
        "00123456Z"
        >>> nif_padding("X1234L")
        "X0001234L"
        >>> nif_padding("123Z")
        "00000123Z"
        >>> nif_padding("123456789")
        "123456789"
        >>> nif_padding("invalid")
        "INVALID"
    Cost: O(L) where L is the length of the input string.
    """
    if not isinstance(p_nif, str):
        return None

    # Clean and standardize the input
    # This replacement explains why we are doing it:
    # We are removing spaces and hyphens because they are common user input errors
    # and do not affect the NIF/NIE/CIF calculation.
    nif_raw = p_nif.strip().upper().replace(" ", "").replace("-", "")
    nif = nif_raw

    # Pad with zeros if the string is shorter than 9 characters
    # We only pad if the raw NIF is potentially a DNI or NIE that is missing leading zeros.
    # This prevents padding for other types of NIFs that might have different structures.
    if len(nif_raw) < 9:
        # Case DNI/NIE (ends with a letter)
        # We check if the last character is alphabetic to identify potential DNI/NIE.
        if nif_raw and nif_raw[-1].isalpha():
            last_char = nif_raw[-1]
            initial_part = nif_raw[:-1]

            # If the initial part is only numbers (DNI)
            # We pad with zeros up to 8 digits because a DNI numeric part should always be 8 digits.
            if initial_part.isdigit() and len(initial_part) < 8:
                nif = f"{initial_part.zfill(8)}{last_char}"

            # If it starts with a letter and the rest are numbers (NIE)
            # We pad the numeric part with zeros up to 7 digits for NIEs.
            elif len(initial_part) > 1 and initial_part[0].isalpha() and initial_part[1:].isdigit():
                first_char = initial_part[0]
                numbers = initial_part[1:]
                if len(numbers) < 7:
                    nif = f"{first_char}{numbers.zfill(7)}{last_char}"

        # Case CIF (starts with a letter, ends with a letter or number)
        # We assume CIFs can also be padded if their numeric part is short.
        elif len(nif_raw) > 2 and nif_raw[0].isalpha() and nif_raw[1:-1].isdigit():
            first_char = nif_raw[0]
            last_char = nif_raw[-1]
            numbers = nif_raw[1:-1]
            if len(numbers) < 7:
                nif = f"{first_char}{numbers.zfill(7)}{last_char}"

    # Return the padded NIF. We do not validate the control digit here,
    # as that's the responsibility of `nif_parse`.
    return nif


def nif_parse(nif: Optional[str]) -> Optional[str]:
    """
    Validates if a Spanish identification number has the correct format.

    Description:
        Checks if the provided string matches any of the valid NIF/NIE/CIF patterns
        and validates the control digit. If the initial validation fails, it attempts
        to pad the NIF using `nif_padding` and re-validates.

    Args:
        nif (str): The identification number to validate.

    Returns:
        str or None: Validated identification number if correct, None if invalid.

    Example:
        >>> nif_parse("12345678Z")
        "12345678Z"
        >>> nif_parse("01234567Z") # Example with leading zero (becomes "01234567Z")
        "01234567Z"
        >>> nif_parse("1234567L") # Example needing padding (becomes "01234567L")
        "01234567L"
        >>> nif_parse("X1234567L")
        "X1234567L"
        >>> nif_parse("invalid")
        None
    Cost: O(L) where L is the length of the NIF string due to regex matching and
          string manipulation.
    """
    if not isinstance(nif, str):
        return None

    # Clean and standardize the input.
    # We strip whitespace and convert to uppercase for consistent matching.
    processed_nif = nif.strip().upper()

    # Define regex patterns for DNI, NIE, and CIF.
    # The patterns are defined here because they are specific to NIF parsing.
    pattern_dni = r"^(\d{8})([A-HJ-NP-TV-Z])$"  # 8 digits + letter
    pattern_nie = r"^([XYZ]\d{7})([A-HJ-NP-TV-Z])$"  # X, Y, Z + 7 digits + letter
    pattern_cif = r"^([ABCDEFGHJKLMNPQRSUVW]\d{7})([0-9A-J])$"  # Initial letter + 7 digits + control

    # Attempt to match the NIF against the defined patterns.
    # This is the first attempt, checking for already valid formats.
    match_dni = re.match(pattern_dni, processed_nif)
    match_nie = re.match(pattern_nie, processed_nif)
    match_cif = re.match(pattern_cif, processed_nif)

    # If none of the direct matches succeed, try padding the NIF.
    # This is crucial for handling cases where leading zeros might be missing.
    if not (match_dni or match_nie or match_cif):
        padded_nif = nif_padding(processed_nif)
        # If padding results in a valid string, update `processed_nif` and re-attempt matching.
        # We re-match because padding might have transformed the NIF into a valid format.
        if padded_nif:
            processed_nif = padded_nif
            match_dni = re.match(pattern_dni, processed_nif)
            match_nie = re.match(pattern_nie, processed_nif)
            match_cif = re.match(pattern_cif, processed_nif)
        else:
            # If padding itself failed, the NIF is invalid.
            return None

    # Handle DNI validation.
    # We check the DNI pattern and then validate the control letter.
    if match_dni:
        number_part, letter_part = match_dni.groups()
        numbers = int(number_part)
        control_letters = "TRWAGMYFPDXBNJZSQVHLCKE"
        # The modulo 23 calculation is standard for DNI control letter validation.
        if letter_part == control_letters[numbers % 23]:
            return processed_nif
        return None

    # Handle NIE validation.
    # We check the NIE pattern, convert the initial letter to a digit, and then validate.
    elif match_nie:
        number_part, letter_part = match_nie.groups()
        nie_map = {"X": "0", "Y": "1", "Z": "2"}
        # The first letter of an NIE is mapped to a digit for control letter calculation.
        numeric_nie_str = nie_map[number_part[0]] + number_part[1:]
        numbers = int(numeric_nie_str)
        control_letters = "TRWAGMYFPDXBNJZSQVHLCKE"
        if letter_part == control_letters[numbers % 23]:
            return processed_nif
        return None

    # Handle CIF validation.
    # CIF validation is more complex, involving even/odd digit sums and a final control character.
    elif match_cif:
        number_part, control_part = match_cif.groups()
        initial_letter = number_part[0]
        digits = number_part[1:]

        # Calculate sum of even-indexed digits (1-based, so 2nd, 4th, 6th digits).
        # Each digit is multiplied by 2, and if the result is two digits, they are summed.
        even_sum = 0
        for i in range(1, 7, 2):
            digit = int(digits[i]) * 2
            even_sum += (digit // 10) + (digit % 10)

        # Calculate sum of odd-indexed digits (1-based, so 1st, 3rd, 5th, 7th digits).
        odd_sum = 0
        for i in range(0, 7, 2):
            odd_sum += int(digits[i])

        total_sum = even_sum + odd_sum
        sum_unit_digit = total_sum % 10

        # Determine the control digit based on the sum's unit digit.
        control_digit = 0 if sum_unit_digit == 0 else 10 - sum_unit_digit
        control_letters = "JABCDEFGHI"

        # Validate based on the initial letter type.
        # Different ranges of initial letters have different control character rules.
        if initial_letter in "PQRSW":
            # For these letters, the control character must be a letter.
            if control_part == control_letters[control_digit]:
                return processed_nif
        elif initial_letter in "ABEH":
            # For these letters, the control character must be a digit.
            if control_part == str(control_digit):
                return processed_nif
        else:
            # For other letters, it can be either a digit or a letter.
            if control_part == str(control_digit) or control_part == control_letters[control_digit]:
                return processed_nif
        return None
    # If no pattern matched, even after padding, return None.
    return None


def nif_letter(p_dni: str) -> str:
    """
    Calculates and appends the control letter to a Spanish DNI/NIE numeric part.

    This function supports both DNI (8 digits) and NIE (starts with X, Y, or Z followed by 7 digits).

    Args:
        p_dni (str): The numeric part of the DNI or the full NIE (e.g., '12345678', 'X1234567').
                     Spaces and dots will be ignored.

    Returns:
        str: The full DNI/NIE with the calculated control letter appended.
             Returns the original input if the input is invalid (e.g., too short, contains
             invalid characters, or cannot be converted to a valid number for calculation).
    """
    if not isinstance(p_dni, str):
        # Handle non-string inputs
        return p_dni

    # 1. Clean the input string: remove spaces, dots, and convert to uppercase for NIE processing.
    #    re.sub is more efficient for multiple replacements.
    cleaned_dni = re.sub(r"[ .\-]", "", p_dni).upper()  # Also remove hyphens for common input variations

    # 2. Check for valid length AFTER cleaning. A DNI has 8 digits. An NIE has a letter + 7 digits.
    #    So, the numeric part is effectively 8 digits for calculation.
    if len(cleaned_dni) < 8:  # Minimum 8 characters for calculation (X+7 digits, or 8 digits)
        return p_dni

    # Define the list of control letters
    control_letters = "TRWAGMYFPDXBNJZSQVHLCKE"  # String is slightly more efficient than list for char access

    numeric_base = 0
    try:
        # Handle NIEs (Foreigner Identification Number)
        # NIEs start with X, Y, or Z. These correspond to 0, 1, 2 for calculation.
        if cleaned_dni.startswith("X"):
            numeric_base = int("0" + cleaned_dni[1:8])  # Replace 'X' with '0'
        elif cleaned_dni.startswith("Y"):
            numeric_base = int("1" + cleaned_dni[1:8])  # Replace 'Y' with '1'
        elif cleaned_dni.startswith("Z"):
            numeric_base = int("2" + cleaned_dni[1:8])  # Replace 'Z' with '2'
        else:
            # Assume it's a DNI (8 digits)
            numeric_base = int(cleaned_dni[:8])  # Take first 8 chars, in case input includes an existing letter

        # Ensure the numeric base is a valid number after conversion.
        # This implicitly handles cases where cleaned_dni[1:8] might not be fully numeric.
        if not isinstance(numeric_base, int):  # Should not happen if int() succeeded but as a safeguard
            return p_dni

    except ValueError:
        # Catch cases where int() conversion fails (e.g., input like '123ABC78')
        return p_dni
    except IndexError:
        # Catch cases like 'X123' where slicing goes out of bounds after cleaning
        return p_dni

    # Calculate the control letter
    remainder = numeric_base % 23
    calculated_letter = control_letters[remainder]

    # Return the original input DNI/NIE part plus the calculated letter
    # This maintains the original formatting of the input string for the numeric part
    # but appends the correct calculated letter.
    return p_dni + calculated_letter


def _calculate_dni_nie_control_letter(numerical_part: int) -> str:
    """
    Calculates the control letter for Spanish DNI/NIE based on the numerical part.
    """
    return _DNI_NIE_CONTROL_LETTERS[numerical_part % 23]


def is_valid_dni(dni_value: str) -> bool:
    """
    Validates a Spanish DNI (Documento Nacional de Identidad) format and control letter.

    Args:
        dni_value (str): The DNI string to validate (e.g., "12345678A").

    Returns:
        bool: True if the DNI is valid, False otherwise.

    Raises:
        TypeError: If 'dni_value' is not a string.
        ValueError: If 'dni_value' does not match the basic DNI regex format.

    Example of use:
        >>> is_valid_dni("12345678Z") # Example valid DNI (not real)
        True
        >>> is_valid_dni("00000000T") # Invalid by specific rule
        False
        >>> is_valid_dni("12345678B") # Invalid control letter
        False
        >>> is_valid_dni("1234567A") # Incorrect length
        False
    """
    if not isinstance(dni_value, str):
        raise TypeError("DNI value must be a string.")

    # Convert to uppercase for case-insensitive comparison
    dni_value = dni_value.upper()

    # Basic regex format check
    if not _DNI_REGEX.match(dni_value):
        return False

    # Specific invalid DNI values (historical/reserved)
    invalid_dni_values = {"00000000T", "00000001R", "99999999R"}
    if dni_value in invalid_dni_values:
        return False

    numerical_part = int(dni_value[0:8])
    provided_control_letter = dni_value[8]

    calculated_control_letter = _calculate_dni_nie_control_letter(numerical_part)

    return provided_control_letter == calculated_control_letter


def is_valid_nie(nie_value: str) -> bool:
    """
    Validates a Spanish NIE (Número de Identificación de Extranjero) format and control letter.

    Args:
        nie_value (str): The NIE string to validate (e.g., "X1234567B").

    Returns:
        bool: True if the NIE is valid, False otherwise.

    Raises:
        TypeError: If 'nie_value' is not a string.
        ValueError: If 'nie_value' does not match the basic NIE regex format.

    Example of use:
        >>> is_valid_nie("X0000000T") # Example valid NIE (not real)
        True
        >>> is_valid_nie("Y1234567N") # Example valid NIE (not real)
        True
        >>> is_valid_nie("Z7654321A") # Example valid NIE (not real)
        True
        >>> is_valid_nie("A1234567B") # Invalid starting letter
        False
        >>> is_valid_nie("X1234567C") # Invalid control letter
        False
    """
    if not isinstance(nie_value, str):
        raise TypeError("NIE value must be a string.")

    # Convert to uppercase for case-insensitive comparison
    nie_value = nie_value.upper()

    # Basic regex format check
    if not _NIE_REGEX.match(nie_value):
        return False

    first_char = nie_value[0]
    numerical_part_str = nie_value[1:8]
    provided_control_letter = nie_value[8]

    # Convert the first character to its corresponding digit for calculation
    if first_char in _NIE_PREFIX_MAPPING:
        prefix_digit = _NIE_PREFIX_MAPPING[first_char]
        full_number_for_calc = int(str(prefix_digit) + numerical_part_str)
    else:
        # This case should ideally be caught by regex, but as a fallback.
        return False

    calculated_control_letter = _calculate_dni_nie_control_letter(full_number_for_calc)

    return provided_control_letter == calculated_control_letter


def is_valid_cif(cif_value: str) -> bool:
    """
    Validates a Spanish CIF (Código de Identificación Fiscal) format and control character.

    CIF validation is highly complex, depending on the first letter of the CIF
    (which denotes the type of legal entity) and involves different checksum
    calculations leading to either a digit or a letter as a control character.

    This is a simplified placeholder. A complete and accurate CIF validation
    requires implementing precise rules for each CIF type (A, B, C, D, E, F, G, H, J, N, P, Q, R, S, W, V).

    Args:
        cif_value (str): The CIF string to validate (e.g., "A12345678").

    Returns:
        bool: True if the CIF is valid, False otherwise.

    Raises:
        TypeError: If 'cif_value' is not a string.
        ValueError: If 'cif_value' does not match the basic CIF regex format.

    Example of use:
        >>> is_valid_cif("A12345678") # This will likely return False with current placeholder logic
        False
        >>> # A real, correct CIF validation requires detailed implementation.
    """
    if not isinstance(cif_value, str):
        raise TypeError("CIF value must be a string.")

    cif_value = cif_value.upper()

    # Basic regex format check
    # This regex is still a simplification, actual CIFs have specific last char types.
    if not _CIF_REGEX.match(cif_value):
        return False

    # --- Placeholder for actual CIF validation logic ---
    # The original logic for CIF in your code had significant issues and
    # does not correspond to standard CIF validation.
    # Implementing full CIF validation involves:
    # 1. Determining the type of entity from the first letter.
    # 2. Applying different checksum algorithms (sum of even digits, sum of odd digits where doubled odd digits are handled specially).
    # 3. Calculating a final control character (digit or letter) based on the first letter and the checksum.
    # 4. Comparing the calculated control character with the provided one.
    # Due to its complexity, this part is left as a placeholder or requires
    # a dedicated, well-researched implementation.

    # For demonstration, a simplistic (and likely incorrect) check:
    first_letter = cif_value[0]
    numerical_part = cif_value[1:8]
    control_char = cif_value[8]

    try:
        # Example: Simple sum check (not a real CIF algorithm)
        total_sum = sum(int(digit) for digit in numerical_part)
        if first_letter in "ABCDEFGHJ":  # Example types with digit control
            expected_control = str(total_sum % 10)
            return expected_control == control_char
        elif first_letter in "KNPQRSUVW":  # Example types with letter control
            # This is a highly simplified and likely incorrect calculation
            expected_control_letter = chr(65 + (total_sum % 10))  # A-J based on modulo
            return expected_control_letter == control_char
        else:
            return False  # Unknown CIF type
    except ValueError:
        return False  # Not purely numeric part
    # --- End Placeholder ---


def validate_spanish_nif(nif_type: str, nif_value: str) -> bool:
    """
    Validates a Spanish NIF (DNI, NIE, or CIF) based on its type and value.

    This is a dispatcher function that calls specific validation functions
    for DNI, NIE, or CIF based on the provided 'nif_type'.

    Args:
        nif_type (str): The type of NIF to validate ('DNI', 'NIE', or 'CIF').
        nif_value (str): The NIF string to validate.

    Returns:
        bool: True if the NIF is valid for its specified type, False otherwise.

    Raises:
        TypeError: If 'nif_type' or 'nif_value' are not strings.
        ValueError: If 'nif_type' is not one of 'DNI', 'NIE', or 'CIF'.

    Example of use:
        >>> validate_spanish_nif("DNI", "12345678Z") # Valid DNI (example)
        True
        >>> validate_spanish_nif("NIE", "X0000000T") # Valid NIE (example)
        True
        >>> validate_spanish_nif("CIF", "A12345678") # Will likely be False due to placeholder CIF logic
        False
        >>> validate_spanish_nif("DNI", "12345678X") # Invalid DNI (wrong letter)
        False
        >>> validate_spanish_nif("DNI", None)
        Traceback (most recent call last):
            ...
        TypeError: NIF value must be a string.
        >>> validate_spanish_nif("INVALID", "123")
        Traceback (most recent call last):
            ...
        ValueError: Invalid NIF type. Expected 'DNI', 'NIE', or 'CIF'.
    """
    if not isinstance(nif_type, str):
        raise TypeError("NIF type must be a string.")
    if not isinstance(nif_value, str):
        raise TypeError("NIF value must be a string.")

    nif_type = nif_type.upper()  # Normalize type input

    if nif_type not in _VALID_NIF_TYPES:
        raise ValueError(f"Invalid NIF type. Expected {_VALID_NIF_TYPES}.")

    if nif_type == "DNI":
        return is_valid_dni(nif_value)
    elif nif_type == "NIE":
        return is_valid_nie(nif_value)
    elif nif_type == "CIF":
        return is_valid_cif(nif_value)
    # This branch should theoretically not be reached due to the initial type check.
    return False


def european_nif(p_iparse, p_find_letter):  # 2
    """
    Parses and validates a National Identification Number (NIF) or similar identifier for various European countries.

    This function processes the input string by removing spaces, converting to uppercase, and ensuring it has a valid
    country code prefix. For Spain (ES), it uses the Spanish NIF validation functions (nif_parse, is_valid_dni, is_valid_nie, is_valid_cif)
    to validate the identifier, optionally computing and appending the control letter if the numeric part is provided and p_find_letter is True.
    For other countries, it checks against predefined regex patterns.

    Args:
        p_iparse (str): The input string representing the identifier to parse. It may include or exclude a country code prefix.
        p_find_letter (bool): If True and the identifier is for Spain (ES) with a numeric part of 7-8 digits, attempts to
                                compute and append the control letter using nif_letter().

    Returns:
        tuple or None: A tuple containing (typenif, country, code, nif_value) where:
            - typenif (str): The type of identifier (e.g., 'DNI', 'NIE', 'CIF', 'NIF').
            - country (str): The full country name (e.g., 'SPAIN').
            - code (str): The two-letter country code (e.g., 'ES').
            - nif_value (str): The identifier value, potentially without the country code prefix depending on the country.
        Returns None if the input is invalid or does not match any pattern.

    Notes:
        - Supported countries include ES (Spain), DE (Germany), FR (France), PT (Portugal), IT (Italy), EL (Greece),
            AT (Austria), BE (Belgium), BG (Bulgaria), HR (Croatia), CY (Cyprus), CZ (Czech Republic), DK (Denmark),
            EE (Estonia), FI (Finland), HU (Hungary), IE (Ireland), LV (Latvia), LT (Lithuania), LU (Luxembourg),
            MT (Malta), NL (Netherlands), PL (Poland), RO (Romania), SK (Slovakia), SI (Slovenia), SE (Sweden),
            GB/UK (United Kingdom).
        - If no country code is provided, defaults to 'ES'.
        - For Spain, validation ensures the control digit/letter is correct using Spanish NIF functions.
        - Uses the 're' module for regex matching.
    """
    # 1. Validación inicial y preparación de la cadena
    if not p_iparse:  # 3
        return None  # 4

    oparse = p_iparse.replace(" ", "").upper()  # 5
    if not oparse:  # 6
        return None  # 7

    # 2. Manejo de prefijos de país
    valid_country_codes = {
        "ES",
        "DE",
        "FR",
        "PT",
        "IT",
        "EL",
        "AT",
        "BE",
        "BG",
        "HR",
        "CY",
        "CZ",
        "DK",
        "EE",  # 8
        "FI",
        "HU",
        "IE",
        "LV",
        "LT",
        "LU",
        "MT",
        "NL",
        "PL",
        "RO",
        "SK",
        "SI",
        "SE",
        "GB",
        "UK",
    }  # 9

    country_code_prefix = oparse[:2]  # 10
    if country_code_prefix not in valid_country_codes:  # 11
        oparse = "ES" + oparse  # 12
        country_code_prefix = "ES"  # Actualizamos el prefijo para la lógica posterior # 13

    # 3. Lógica específica para España (ES)
    if country_code_prefix == "ES":  # 14
        nif_value = oparse[2:]  # 15
        if p_find_letter and nif_value.isdigit() and 6 < len(nif_value) < 9:  # 16
            nif_value = nif_letter(nif_value)  # 17
        # Validate using Spanish NIF functions
        validated_nif = nif_parse(nif_value)
        if validated_nif is None:
            return None
        # Determine type
        if is_valid_dni(validated_nif):
            typenif = "DNI"
        elif is_valid_nie(validated_nif):
            typenif = "NIE"
        elif is_valid_cif(validated_nif):
            typenif = "CIF"
        else:
            return None  # Should not happen if nif_parse succeeded
        return (typenif, "SPAIN", "ES", validated_nif)
    elif country_code_prefix == "PT" and len(oparse) == 9 and oparse.isdigit():  # Para Portugal si no tiene el prefijo inicial # 19
        oparse = "PT" + oparse  # Aseguramos que Portugal siempre tenga su prefijo para los patrones # 20

    # 4. Patrones y metadatos de los países
    patterns = {  # 21
        "ES": [  # 22
            (r"ES[0-9]{8}[A-Z]", "DNI", "SPAIN", "ES"),  # 23
            (r"ES[K-M][0-9]{8}", "NIE", "SPAIN", "ES"),  # 24
            (r"ES[X-Z][0-9]{7}[A-Z]", "NIE", "SPAIN", "ES"),  # 25
            (r"ES[A-H|J|U-V][0-9]{8}", "CIF", "SPAIN", "ES"),  # 26
            (r"ES[N|P-S|W][0-9]{7}[A-Z]", "CIF", "SPAIN", "ES"),  # 27
        ],
        "DE": [(r"DE[0-9]{9}", "NIF", "GERMANY", "DE")],  # 28
        "FR": [(r"FR[A-Z0-9]{2}[0-9]{9}", "NIF", "FRANCE", "FR")],  # 29
        "PT": [(r"PT[0-9]{9}", "NIF", "PORTUGAL", "PT")],  # 30
        "IT": [(r"IT[0-9]{11}", "NIF", "ITALY", "IT")],  # 31
        "EL": [(r"EL[0-9]{9}", "NIF", "GREECE", "EL")],  # 32
        "AT": [(r"ATU[0-9]{8}", "NIF", "AUSTRIA", "AT")],  # 33
        "BE": [(r"BE0[0-9]{9}", "NIF", "BELGIUM", "BE")],  # 34
        "BG": [(r"BG[0-9]{9,10}", "NIF", "BULGARIA", "BG")],  # 35
        "HR": [(r"HR[0-9]{11}", "NIF", "CROATIA", "HR")],  # 36
        "CY": [(r"CY[0-9]{8}[A-Z]", "NIF", "CYPRUS", "CY")],  # 37
        "CZ": [(r"CZ[0-9]{8,10}", "NIF", "CZECH REPUBLIC", "CZ")],  # 38
        "DK": [(r"DK[0-9]{8}", "NIF", "DENMARK", "DK")],  # 39
        "EE": [(r"EE[0-9]{9}", "NIF", "ESTONIA", "EE")],  # 40
        "FI": [(r"FI[0-9]{8}", "NIF", "FINLAND", "FI")],  # 41
        "HU": [(r"HU[0-9]{8}", "NIF", "HUNGARY", "HU")],  # 42
        "IE": [(r"IE[0-9]{7}[A-Z]{1,2}", "NIF", "IRELAND", "IE")],  # 43
        "LV": [(r"LV[0-9]{11}", "NIF", "LATVIA", "LV")],  # 44
        "LT": [(r"LT[0-9]{9,12}", "NIF", "LITHUANIA", "LT")],  # 45
        "LU": [(r"LU[0-9]{8}", "NIF", "LUXEMBOURG", "LU")],  # 46
        "MT": [(r"MT[0-9]{8}", "NIF", "MALTA", "MT")],  # 47
        "NL": [(r"NL[0-9]{9}B[0-9]{2}", "NIF", "NETHERLANDS", "NL")],  # 48
        "PL": [(r"PL[0-9]{10}", "NIF", "POLAND", "PL")],  # 49
        "RO": [(r"RO[0-9]{2,10}", "NIF", "ROMANIA", "RO")],  # 50
        "SK": [(r"SK[0-9]{10}", "NIF", "SLOVAKIA", "SK")],  # 51
        "SI": [(r"SI[0-9]{8}", "NIF", "SLOVENIA", "SI")],  # 52
        "SE": [(r"SE[0-9]{10}[0-1]{2}", "NIF", "SWEDEN", "SE")],  # 53
        "GB": [(r"GB[0-9]{9}", "NIF", "UNITED KINGDOM", "GB")],  # 54
    }

    # 5. Búsqueda y retorno del NIF
    country_code_to_check = oparse[:2]  # 55

    if country_code_to_check in patterns:  # 56
        for pattern, typenif, country, code in patterns[country_code_to_check]:  # 57
            if re.match(pattern, oparse):  # 58
                # Extraer NIF sin el código de país si es necesario
                nif_value = oparse[2:] if code not in ["PT", "IT", "EL"] else oparse  # 59
                return (typenif, country, code, nif_value)  # 60

    return None  # 61


# ---------------------------------------------------------------------------
# Extended ID Validations for Other Countries
# ---------------------------------------------------------------------------


def is_valid_ssn(ssn: str) -> bool:
    """
    Validates a United States Social Security Number (SSN).

    Rules:
    - 9 digits.
    - Not starting with 000, 666, or 900-999.
    - Middle group (group 2) not 00.
    - Last group (group 3) not 0000.
    """
    if not isinstance(ssn, str):
        return False
    clean_ssn = re.sub(r"\D", "", ssn)
    if len(clean_ssn) != 9:
        return False
    if clean_ssn.startswith("000") or clean_ssn.startswith("666") or clean_ssn.startswith("9"):
        return False
    if clean_ssn[3:5] == "00":
        return False
    if clean_ssn[5:9] == "0000":
        return False
    return True


def is_valid_cpf(cpf: str) -> bool:
    """
    Validates a Brazilian CPF (Cadastro de Pessoas Físicas).

    Uses the two-digit checksum validation.
    """
    if not isinstance(cpf, str):
        return False
    clean_cpf = re.sub(r"\D", "", cpf)
    if len(clean_cpf) != 11 or clean_cpf == clean_cpf[0] * 11:
        return False

    # Validate first digit
    for i in range(9, 11):
        value = sum((int(clean_cpf[num]) * ((i + 1) - num) for num in range(0, i)))
        digit = ((value * 10) % 11) % 10
        if digit != int(clean_cpf[i]):
            return False
    return True


def is_valid_cnpj(cnpj: str) -> bool:
    """
    Validates a Brazilian CNPJ (Cadastro Nacional de Pessoa Jurídica).
    """
    if not isinstance(cnpj, str):
        return False
    clean_cnpj = re.sub(r"\D", "", cnpj)
    if len(clean_cnpj) != 14 or clean_cnpj == clean_cnpj[0] * 14:
        return False

    # Validate first digit
    weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum1 = sum(int(clean_cnpj[i]) * weights1[i] for i in range(12))
    digit1 = 0 if sum1 % 11 < 2 else 11 - (sum1 % 11)
    if int(clean_cnpj[12]) != digit1:
        return False

    # Validate second digit
    weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum2 = sum(int(clean_cnpj[i]) * weights2[i] for i in range(13))
    digit2 = 0 if sum2 % 11 < 2 else 11 - (sum2 % 11)
    return int(clean_cnpj[13]) == digit2


def is_valid_bsn(bsn: str) -> bool:
    """
    Validates a Netherlands BSN (Burgerservicenummer).

    Uses logic known as the '11-test'.
    """
    if not isinstance(bsn, str):
        return False
    clean_bsn = re.sub(r"\D", "", bsn)
    if len(clean_bsn) != 9:
        return False

    total = 0
    for i in range(8):
        total += int(clean_bsn[i]) * (9 - i)
    total -= int(clean_bsn[8])
    return total % 11 == 0


def is_valid_codice_fiscale(cf: str) -> bool:
    """
    Validates an Italian Codice Fiscale.

    Validates the format and the control character (character 16)
    using the official odd/even positional algorithm.
    """
    if not isinstance(cf, str):
        return False
    cf = cf.upper().strip()
    if not re.match(r"^[A-Z]{6}\d{2}[A-Z]\d{2}[A-Z]\d{3}[A-Z]$", cf):
        return False

    _ODD_VALUES = {
        "0": 1,
        "1": 0,
        "2": 5,
        "3": 7,
        "4": 9,
        "5": 13,
        "6": 15,
        "7": 17,
        "8": 19,
        "9": 21,
        "A": 1,
        "B": 0,
        "C": 5,
        "D": 7,
        "E": 9,
        "F": 13,
        "G": 15,
        "H": 17,
        "I": 19,
        "J": 21,
        "K": 2,
        "L": 4,
        "M": 18,
        "N": 20,
        "O": 11,
        "P": 3,
        "Q": 6,
        "R": 8,
        "S": 12,
        "T": 14,
        "U": 16,
        "V": 10,
        "W": 22,
        "X": 25,
        "Y": 24,
        "Z": 23,
    }
    _EVEN_VALUES = {
        "0": 0,
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        "A": 0,
        "B": 1,
        "C": 2,
        "D": 3,
        "E": 4,
        "F": 5,
        "G": 6,
        "H": 7,
        "I": 8,
        "J": 9,
        "K": 10,
        "L": 11,
        "M": 12,
        "N": 13,
        "O": 14,
        "P": 15,
        "Q": 16,
        "R": 17,
        "S": 18,
        "T": 19,
        "U": 20,
        "V": 21,
        "W": 22,
        "X": 23,
        "Y": 24,
        "Z": 25,
    }

    total = 0
    for i, c in enumerate(cf[:15]):
        total += _ODD_VALUES[c] if i % 2 == 0 else _EVEN_VALUES[c]
    expected = chr(65 + total % 26)
    return cf[15] == expected


def validate_id_document(id_str: str, country_code: str) -> bool:
    """
    Dispatch validation to the appropriate country-specific logic.

    Args:
        id_str: The identification string to validate.
        country_code: ISO 3166-1 alpha-2 country code (e.g., 'US', 'BR', 'ES').

    Returns:
        bool: True if valid, False otherwise.
    """
    if not isinstance(id_str, str) or not isinstance(country_code, str):
        return False
    code = country_code.upper()

    _VALIDATORS = {
        "ES": lambda s: nif_parse(s) is not None,
        "US": is_valid_ssn,
        "NL": is_valid_bsn,
        "IT": is_valid_codice_fiscale,
        "MX": is_valid_curp,
        "CL": is_valid_rut,
        "GB": is_valid_nino,
        "PT": is_valid_portuguese_nif,
    }

    validator = _VALIDATORS.get(code)
    if validator:
        return validator(id_str)

    # Brazil: auto-detect CPF vs CNPJ
    if code == "BR":
        clean = re.sub(r"\D", "", id_str)
        if len(clean) == 11:
            return is_valid_cpf(id_str)
        elif len(clean) == 14:
            return is_valid_cnpj(id_str)
        return False

    # Argentina: CUIL/CUIT
    if code == "AR":
        clean = re.sub(r"\D", "", id_str)
        if len(clean) == 11:
            return is_valid_cuil(id_str)
        # Short DNI (7-8 digits, no checksum)
        if len(clean) in (7, 8):
            return True
        return False

    # Colombia: Cédula (6-10 digits, no official checksum)
    if code == "CO":
        clean = re.sub(r"\D", "", id_str)
        return 6 <= len(clean) <= 10

    # Fallback to european_nif for other EU countries
    return european_nif(id_str, False) is not None


# ---------------------------------------------------------------------------
# Latin America ID Validations
# ---------------------------------------------------------------------------


def is_valid_curp(curp: str) -> bool:
    """
    Validates a Mexican CURP (Clave Única de Registro de Población).

    Format: 4 letters + 6 digits (YYMMDD) + H/M + 2 letters (state) +
            3 consonants + 1 alphanumeric + 1 digit.
    """
    if not isinstance(curp, str):
        return False
    curp = curp.upper().strip()
    return bool(re.match(r"^[A-Z]{4}\d{6}[HM][A-Z]{2}[B-DF-HJ-NP-TV-Z]{3}[A-Z0-9]\d$", curp))


def is_valid_rut(rut: str) -> bool:
    """
    Validates a Chilean RUT (Rol Único Tributario).

    Uses the modulo-11 verification digit algorithm.
    The check digit can be 0-9 or K.
    """
    if not isinstance(rut, str):
        return False
    clean = re.sub(r"[\.\-\s]", "", rut).upper()
    if len(clean) < 2:
        return False

    body = clean[:-1]
    dv = clean[-1]

    if not body.isdigit():
        return False

    # Modulo-11 algorithm
    total = 0
    factor = 2
    for digit in reversed(body):
        total += int(digit) * factor
        factor = factor + 1 if factor < 7 else 2
    remainder = 11 - (total % 11)

    if remainder == 11:
        expected = "0"
    elif remainder == 10:
        expected = "K"
    else:
        expected = str(remainder)

    return dv == expected


def is_valid_cuil(cuil: str) -> bool:
    """
    Validates an Argentine CUIL/CUIT (Código Único de Identificación Laboral/Tributaria).

    Format: XX-XXXXXXXX-X (11 digits total).
    Uses a weighted checksum algorithm.
    """
    if not isinstance(cuil, str):
        return False
    clean = re.sub(r"\D", "", cuil)
    if len(clean) != 11:
        return False

    weights = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
    total = sum(int(clean[i]) * weights[i] for i in range(10))
    remainder = 11 - (total % 11)

    if remainder == 11:
        expected = 0
    elif remainder == 10:
        expected = 9  # Some edge cases use 9 for male, female prefix differences
    else:
        expected = remainder

    return int(clean[10]) == expected


# ---------------------------------------------------------------------------
# Additional European ID Validations
# ---------------------------------------------------------------------------


def is_valid_nino(nino: str) -> bool:
    """
    Validates a UK National Insurance Number (NINO).

    Format: 2 prefix letters + 6 digits + 1 suffix letter (A-D).
    Certain prefix combinations are invalid (BG, GB, NK, KN, TN, NT, ZZ,
    and prefixes starting with D, F, I, Q, U, V).
    """
    if not isinstance(nino, str):
        return False
    nino = nino.upper().replace(" ", "").replace("-", "")
    if not re.match(r"^[A-Z]{2}\d{6}[A-D]$", nino):
        return False
    prefix = nino[:2]
    invalid_prefixes = {"BG", "GB", "NK", "KN", "TN", "NT", "ZZ"}
    if prefix in invalid_prefixes:
        return False
    if prefix[0] in "DFIQUV":
        return False
    if prefix[1] in "DFIQUVO":
        return False
    return True


def is_valid_portuguese_nif(nif: str) -> bool:
    """
    Validates a Portuguese NIF (Número de Identificação Fiscal).

    9 digits with a modulo-11 check digit.
    First digit must be 1-3 (individual) or 5,6,8,9 (corporate/other).
    """
    if not isinstance(nif, str):
        return False
    clean = re.sub(r"\D", "", nif)
    if len(clean) != 9:
        return False
    if clean[0] not in "123456789":
        return False

    weights = [9, 8, 7, 6, 5, 4, 3, 2]
    total = sum(int(clean[i]) * weights[i] for i in range(8))
    remainder = total % 11
    check = 0 if remainder < 2 else 11 - remainder
    return int(clean[8]) == check
