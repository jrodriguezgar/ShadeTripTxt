"""
Text Dummy Generator - Fake data generation tool powered by Faker.

This module provides functions to generate fake data of various types,
useful for testing, development, and demos. Supports multiple locales
(country/language) with country-specific generators (ID documents, phone
formats, currency, postal codes, etc.).
"""

from __future__ import annotations

from typing import Optional, List, Dict, Any, Callable, Union, Sequence, TYPE_CHECKING
from dataclasses import dataclass, field
import random as _random

from shadetriptxt.utils._locale import BaseLocaleProfile
import string
import datetime
import uuid
import unicodedata

if TYPE_CHECKING:
    from faker import Faker


class DummyField:
    """
    Annotation marker to specify which generator to use for a Pydantic field.

    Use with ``typing.Annotated`` when the field name does not match the
    desired generator. The generator name must be a valid TextDummy method
    or a registered custom generator.

    Example:
        from typing import Annotated
        from pydantic import BaseModel
        from shadetriptxt.text_dummy.text_dummy import DummyField

        class Employee(BaseModel):
            codigo: Annotated[str, DummyField("uuid4")]
            referencia: Annotated[str, DummyField("product_sku")]
            contacto: Annotated[str, DummyField("email")]
            nivel: Annotated[int, DummyField("age", min_val=18, max_val=65)]
    """

    def __init__(self, generator: str, **kwargs: Any):
        """
        Args:
            generator: Name of the TextDummy method or custom generator.
            **kwargs: Extra keyword arguments passed to the generator method.
        """
        self.generator = generator
        self.kwargs = kwargs

    def __repr__(self) -> str:
        kw = ", ".join(f"{k}={v!r}" for k, v in self.kwargs.items())
        args = self.generator if not kw else f"{self.generator}, {kw}"
        return f"DummyField({args})"


# ---------------------------------------------------------------------------
# Locale profiles: metadata and capabilities per country/language
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LocaleProfile(BaseLocaleProfile):
    """Profile for a supported locale with its capabilities."""

    currency_code: str
    currency_symbol: str
    phone_prefix: str
    id_document_name: str
    id_document_method: str  # Faker method or internal name
    date_format: str = "%d/%m/%Y"
    has_state_province: bool = True
    extra_id_documents: Dict[str, str] = field(default_factory=dict)


LOCALE_PROFILES: Dict[str, LocaleProfile] = {
    # --- Spanish ---
    "es_ES": LocaleProfile(
        code="es_ES",
        country="Spain",
        language="Spanish",
        currency_code="EUR",
        currency_symbol="€",
        phone_prefix="+34",
        id_document_name="DNI/NIF",
        id_document_method="nif",
        date_format="%d/%m/%Y",
        has_state_province=True,
        extra_id_documents={"NIE": "nie"},
    ),
    "es_MX": LocaleProfile(
        code="es_MX",
        country="Mexico",
        language="Spanish",
        currency_code="MXN",
        currency_symbol="$",
        phone_prefix="+52",
        id_document_name="CURP",
        id_document_method="curp",
        date_format="%d/%m/%Y",
        has_state_province=True,
        extra_id_documents={"RFC": "rfc"},
    ),
    "es_AR": LocaleProfile(
        code="es_AR",
        country="Argentina",
        language="Spanish",
        currency_code="ARS",
        currency_symbol="$",
        phone_prefix="+54",
        id_document_name="DNI",
        id_document_method="dni",
        date_format="%d/%m/%Y",
        has_state_province=True,
        extra_id_documents={"CUIL": "cuil"},
    ),
    "es_CO": LocaleProfile(
        code="es_CO",
        country="Colombia",
        language="Spanish",
        currency_code="COP",
        currency_symbol="$",
        phone_prefix="+57",
        id_document_name="Cédula",
        id_document_method="cedula",
        date_format="%d/%m/%Y",
        has_state_province=True,
    ),
    "es_CL": LocaleProfile(
        code="es_CL",
        country="Chile",
        language="Spanish",
        currency_code="CLP",
        currency_symbol="$",
        phone_prefix="+56",
        id_document_name="RUT",
        id_document_method="rut",
        date_format="%d/%m/%Y",
        has_state_province=True,
    ),
    # --- English ---
    "en_US": LocaleProfile(
        code="en_US",
        country="United States",
        language="English",
        currency_code="USD",
        currency_symbol="$",
        phone_prefix="+1",
        id_document_name="SSN",
        id_document_method="ssn",
        date_format="%m/%d/%Y",
        has_state_province=True,
        extra_id_documents={"EIN": "ein"},
    ),
    "en_GB": LocaleProfile(
        code="en_GB",
        country="United Kingdom",
        language="English",
        currency_code="GBP",
        currency_symbol="£",
        phone_prefix="+44",
        id_document_name="NINO",
        id_document_method="nino",
        date_format="%d/%m/%Y",
        has_state_province=False,
    ),
    # --- Portuguese ---
    "pt_BR": LocaleProfile(
        code="pt_BR",
        country="Brazil",
        language="Portuguese",
        currency_code="BRL",
        currency_symbol="R$",
        phone_prefix="+55",
        id_document_name="CPF",
        id_document_method="cpf",
        date_format="%d/%m/%Y",
        has_state_province=True,
        extra_id_documents={"CNPJ": "cnpj"},
    ),
    "pt_PT": LocaleProfile(
        code="pt_PT",
        country="Portugal",
        language="Portuguese",
        currency_code="EUR",
        currency_symbol="€",
        phone_prefix="+351",
        id_document_name="NIF",
        id_document_method="nif",
        date_format="%d/%m/%Y",
        has_state_province=False,
    ),
    # --- French ---
    "fr_FR": LocaleProfile(
        code="fr_FR",
        country="France",
        language="French",
        currency_code="EUR",
        currency_symbol="€",
        phone_prefix="+33",
        id_document_name="INSEE/NIR",
        id_document_method="nir",
        date_format="%d/%m/%Y",
        has_state_province=False,
    ),
    # --- German ---
    "de_DE": LocaleProfile(
        code="de_DE",
        country="Germany",
        language="German",
        currency_code="EUR",
        currency_symbol="€",
        phone_prefix="+49",
        id_document_name="Personalausweis",
        id_document_method="personalausweis",
        date_format="%d.%m.%Y",
        has_state_province=True,
    ),
    # --- Italian ---
    "it_IT": LocaleProfile(
        code="it_IT",
        country="Italy",
        language="Italian",
        currency_code="EUR",
        currency_symbol="€",
        phone_prefix="+39",
        id_document_name="Codice Fiscale",
        id_document_method="codice_fiscale",
        date_format="%d/%m/%Y",
        has_state_province=True,
    ),
}


# ---------------------------------------------------------------------------
# Internal ID document generators per country
# ---------------------------------------------------------------------------


def _generate_id_document(fake: Faker, profile: LocaleProfile, doc_type: Optional[str] = None, rng: Optional[_random.Random] = None) -> str:
    """
    Generate a fake ID document based on the locale.

    First attempts to use Faker's native provider; if unavailable,
    generates a valid synthetic value.
    """
    random = rng if rng is not None else _random.Random()
    method_name = doc_type or profile.id_document_method

    # Resolve extra document aliases
    if doc_type and doc_type.upper() in profile.extra_id_documents:
        method_name = profile.extra_id_documents[doc_type.upper()]

    # Try Faker's native provider (skip when seeded — some Faker providers
    # ignore seed_instance() and produce non-deterministic results)
    if rng is None:
        faker_method = getattr(fake, method_name, None)
        if faker_method and callable(faker_method):
            return faker_method()

    # — Synthetic fallbacks per locale —
    code = profile.code

    if code == "es_ES":
        if method_name in ("nif", "dni"):
            num = random.randint(10_000_000, 99_999_999)
            return f"{num}{'TRWAGMYFPDXBNJZSQVHLCKE'[num % 23]}"
        if method_name == "nie":
            prefix = random.choice("XYZ")
            num = random.randint(1_000_000, 9_999_999)
            full = "XYZ".index(prefix) * 10_000_000 + num
            return f"{prefix}{num}{'TRWAGMYFPDXBNJZSQVHLCKE'[full % 23]}"

    if code == "es_MX":
        if method_name == "curp":
            letters = "".join(random.choices(string.ascii_uppercase, k=4))
            date = f"{random.randint(70, 99):02d}{random.randint(1, 12):02d}{random.randint(1, 28):02d}"
            sex = random.choice("HM")
            state = random.choice(
                [
                    "AS",
                    "BC",
                    "BS",
                    "CC",
                    "CL",
                    "CM",
                    "CS",
                    "CH",
                    "DF",
                    "DG",
                    "GT",
                    "GR",
                    "HG",
                    "JC",
                    "MC",
                    "MN",
                    "MS",
                    "NT",
                    "NL",
                    "OC",
                    "PL",
                    "QT",
                    "QR",
                    "SP",
                    "SL",
                    "SR",
                    "TC",
                    "TS",
                    "TL",
                    "VZ",
                    "YN",
                    "ZS",
                ]
            )
            cons = "".join(random.choices(string.ascii_uppercase, k=3))
            digit = str(random.randint(0, 9))
            check = str(random.randint(0, 9))
            return f"{letters}{date}{sex}{state}{cons}{digit}{check}"
        if method_name == "rfc":
            letters = "".join(random.choices(string.ascii_uppercase, k=4))
            date = f"{random.randint(70, 99):02d}{random.randint(1, 12):02d}{random.randint(1, 28):02d}"
            homoclave = "".join(random.choices(string.ascii_uppercase + string.digits, k=3))
            return f"{letters}{date}{homoclave}"

    if code == "es_AR":
        if method_name == "dni":
            return str(random.randint(10_000_000, 99_999_999))
        if method_name == "cuil":
            prefix = random.choice(["20", "23", "24", "27"])
            dni = f"{random.randint(10_000_000, 99_999_999)}"
            return f"{prefix}-{dni}-{random.randint(0, 9)}"

    if code == "es_CO":
        if method_name == "cedula":
            return str(random.randint(1_000_000_000, 1_999_999_999))

    if code == "es_CL":
        if method_name == "rut":
            num = random.randint(5_000_000, 25_000_000)
            s = 0
            mul = 2
            for d in reversed(str(num)):
                s += int(d) * mul
                mul = mul + 1 if mul < 7 else 2
            rem = 11 - (s % 11)
            dv = "0" if rem == 11 else "K" if rem == 10 else str(rem)
            formatted = f"{num:,}".replace(",", ".")
            return f"{formatted}-{dv}"

    if code == "en_US":
        if method_name == "ssn":
            return f"{random.randint(100, 899):03d}-{random.randint(10, 99):02d}-{random.randint(1000, 9999):04d}"
        if method_name == "ein":
            return f"{random.randint(10, 99):02d}-{random.randint(1000000, 9999999):07d}"

    if code == "en_GB":
        if method_name == "nino":
            p1 = "".join(random.choices("ABCEGHJKLMNPRSTWXYZ", k=2))
            nums = f"{random.randint(10, 99):02d}{random.randint(10, 99):02d}{random.randint(10, 99):02d}"
            suffix = random.choice("ABCD")
            return f"{p1}{nums}{suffix}"

    if code == "pt_BR":
        if method_name == "cpf":
            nums = [random.randint(0, 9) for _ in range(9)]
            s1 = sum((10 - i) * nums[i] for i in range(9))
            d1 = 11 - (s1 % 11)
            d1 = 0 if d1 >= 10 else d1
            nums.append(d1)
            s2 = sum((11 - i) * nums[i] for i in range(10))
            d2 = 11 - (s2 % 11)
            d2 = 0 if d2 >= 10 else d2
            nums.append(d2)
            n = "".join(map(str, nums))
            return f"{n[:3]}.{n[3:6]}.{n[6:9]}-{n[9:]}"
        if method_name == "cnpj":
            base = [random.randint(0, 9) for _ in range(8)] + [0, 0, 0, 1]
            weights1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
            s1 = sum(base[i] * weights1[i] for i in range(12))
            d1 = 11 - (s1 % 11)
            d1 = 0 if d1 >= 10 else d1
            base.append(d1)
            weights2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
            s2 = sum(base[i] * weights2[i] for i in range(13))
            d2 = 11 - (s2 % 11)
            d2 = 0 if d2 >= 10 else d2
            base.append(d2)
            n = "".join(map(str, base))
            return f"{n[:2]}.{n[2:5]}.{n[5:8]}/{n[8:12]}-{n[12:]}"

    if code == "pt_PT":
        if method_name == "nif":
            prefix = random.choice(["1", "2", "5", "6", "8", "9"])
            nums = [int(prefix)] + [random.randint(0, 9) for _ in range(7)]
            s = sum(nums[i] * (9 - i) for i in range(8))
            check = 11 - (s % 11)
            check = 0 if check >= 10 else check
            return "".join(map(str, nums)) + str(check)

    if code == "it_IT":
        if method_name == "codice_fiscale":
            letters = "".join(random.choices(string.ascii_uppercase, k=6))
            date_part = f"{random.randint(50, 99):02d}{random.choice('ABCDEHLMPRST')}{random.randint(1, 28):02d}"
            code_part = random.choice("FMZH") + f"{random.randint(100, 999)}"
            check = random.choice(string.ascii_uppercase)
            return f"{letters}{date_part}{code_part}{check}"

    if code == "de_DE":
        if method_name == "personalausweis":
            return "".join(random.choices(string.ascii_uppercase + string.digits, k=10))

    if code == "fr_FR":
        if method_name == "nir":
            sex = random.choice(["1", "2"])
            year = f"{random.randint(50, 99):02d}"
            month = f"{random.randint(1, 12):02d}"
            dept = f"{random.randint(1, 95):02d}"
            commune = f"{random.randint(1, 999):03d}"
            order = f"{random.randint(1, 999):03d}"
            base = int(f"{sex}{year}{month}{dept}{commune}{order}")
            key = f"{97 - (base % 97):02d}"
            return f"{sex} {year} {month} {dept} {commune} {order} {key}"

    # Fallback — generic
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=12))


# ---------------------------------------------------------------------------
# Field name to generator mapping for Pydantic model filling
# ---------------------------------------------------------------------------

_FIELD_NAME_GENERATORS: Dict[str, str] = {
    # Direct method names
    "name": "name",
    "first_name": "first_name",
    "last_name": "last_name",
    "email": "email",
    "phone": "phone",
    "address": "address",
    "city": "city",
    "state": "state",
    "postcode": "postcode",
    "country": "country",
    "company": "company",
    "job": "job",
    "department": "department",
    "url": "url",
    "domain_name": "domain_name",
    "username": "username",
    "userlogin": "userlogin",
    "password": "password",
    "ipv4": "ipv4",
    "ipv6": "ipv6",
    "iban": "iban",
    "bban": "bban",
    "swift": "swift",
    "date": "date",
    "latitude": "latitude",
    "longitude": "longitude",
    "coordinate": "coordinate",
    "color_name": "color_name",
    "hex_color": "hex_color",
    "rgb_color": "rgb_color",
    "license_plate": "license_plate",
    "mac_address": "mac_address",
    "user_agent": "user_agent",
    "slug": "slug",
    "uuid4": "uuid4",
    "file_name": "file_name",
    "file_extension": "file_extension",
    "mime_type": "mime_type",
    "file_path": "file_path",
    "date_of_birth": "date_of_birth",
    "prefix": "prefix",
    "suffix": "suffix",
    "ssn": "ssn",
    "credit_card_number": "credit_card_number",
    "product_name": "product_name",
    "product_category": "product_category",
    "product_material": "product_material",
    "product_sku": "product_sku",
    "order_status": "order_status",
    "tracking_number": "tracking_number",
    "invoice_number": "invoice_number",
    "payment_method": "payment_method",
    "dni": "dni",
    "id_document": "id_document",
    "cryptocurrency_code": "cryptocurrency_code",
    "cryptocurrency_name": "cryptocurrency_name",
    "random_number": "random_number",
    "random_date": "random_date",
    "unique_key": "unique_key",
    "autoincrement": "autoincrement",
    "gender": "gender",
    "age": "age",
    # Common aliases
    "full_name": "name",
    "fullname": "name",
    "nombre": "name",
    "firstname": "first_name",
    "nombre_propio": "first_name",
    "lastname": "last_name",
    "surname": "last_name",
    "family_name": "last_name",
    "apellido": "last_name",
    "mail": "email",
    "email_address": "email",
    "correo": "email",
    "phone_number": "phone",
    "telephone": "phone",
    "tel": "phone",
    "mobile": "phone",
    "cell": "phone",
    "telefono": "phone",
    "zip_code": "postcode",
    "zip": "postcode",
    "postal_code": "postcode",
    "zipcode": "postcode",
    "codigo_postal": "postcode",
    "street": "address",
    "street_address": "address",
    "direccion": "address",
    "ciudad": "city",
    "town": "city",
    "provincia": "state",
    "region": "state",
    "province": "state",
    "pais": "country",
    "nation": "country",
    "empresa": "company",
    "organization": "company",
    "org": "company",
    "job_title": "job",
    "position": "job",
    "cargo": "job",
    "departamento": "department",
    "dept": "department",
    "website": "url",
    "site": "url",
    "webpage": "url",
    "web": "url",
    "domain": "domain_name",
    "host": "domain_name",
    "dominio": "domain_name",
    "user": "username",
    "login": "userlogin",
    "user_name": "username",
    "user_login": "userlogin",
    "signin": "userlogin",
    "ip": "ipv4",
    "ip_address": "ipv4",
    "title": "sentence",
    "titulo": "sentence",
    "description": "sentence",
    "descripcion": "sentence",
    "bio": "sentence",
    "about": "sentence",
    "comment": "sentence",
    "note": "sentence",
    "nif": "dni",
    "document": "id_document",
    "documento": "id_document",
    "credit_card": "credit_card_number",
    "card_number": "credit_card_number",
    "tarjeta": "credit_card_number",
    "uuid": "uuid4",
    "guid": "uuid4",
    "product": "product_name",
    "producto": "product_name",
    "category": "product_category",
    "categoria": "product_category",
    "material": "product_material",
    "sku": "product_sku",
    "price": "price",
    "precio": "price",
    "tracking": "tracking_number",
    "invoice": "invoice_number",
    "factura": "invoice_number",
    "dob": "date_of_birth",
    "birthdate": "date_of_birth",
    "birth_date": "date_of_birth",
    "fecha_nacimiento": "date_of_birth",
    "mac": "mac_address",
    "filename": "file_name",
    "archivo": "file_name",
    "extension": "file_extension",
    "mime": "mime_type",
    "isbn": "isbn13",
    "ean": "ean13",
    "barcode": "ean13",
    "color": "color_name",
    "lat": "latitude",
    "lng": "longitude",
    "lon": "longitude",
    "status": "order_status",
    "estado": "order_status",
    "payment": "payment_method",
    "pago": "payment_method",
    "crypto": "cryptocurrency_code",
    "matricula": "license_plate",
    "plate": "license_plate",
    "numero": "random_number",
    "number": "random_number",
    "importe": "random_number",
    "amount": "random_number",
    "quantity": "random_number",
    "cantidad": "random_number",
    "fecha": "random_date",
    "fecha_inicio": "random_date",
    "fecha_fin": "random_date",
    "start_date": "random_date",
    "end_date": "random_date",
    "created_at": "random_date",
    "updated_at": "random_date",
    "key": "unique_key",
    "clave": "unique_key",
    "clave_unica": "unique_key",
    "unique_id": "unique_key",
    "codigo": "unique_key",
    "code": "unique_key",
    "token": "unique_key",
    "ref": "unique_key",
    "reference": "unique_key",
    "referencia": "unique_key",
    "id": "autoincrement",
    "consecutivo": "autoincrement",
    "secuencia": "autoincrement",
    "sequence": "autoincrement",
    "seq": "autoincrement",
    "counter": "autoincrement",
    "contador": "autoincrement",
    "row_id": "autoincrement",
    "row_number": "autoincrement",
    "numero_fila": "autoincrement",
    "genero": "gender",
    "sexo": "gender",
    "sex": "gender",
    "edad": "age",
    "years_old": "age",
    "pwd": "password",
    "pass_word": "password",
    "contrasena": "password",
    "clave_acceso": "password",
}


# ---------------------------------------------------------------------------
# Main class
# ---------------------------------------------------------------------------


class TextDummy:
    """Locale-configurable fake data generator."""

    def __init__(self, locale: str = "es_ES", seed: Optional[int] = None):
        """
        Initialize the fake data generator.

        Args:
            locale: Language/country code (e.g. 'es_ES', 'en_US', 'fr_FR').
                   Defaults to Spanish (Spain).
            seed: Optional seed for reproducible data generation. When set,
                 both Faker and all internal random generators produce
                 deterministic output across executions.
        """
        self.locale = locale
        self.seed = seed
        self._rng = _random.Random(seed)
        from faker import Faker  # lazy

        self.fake = Faker(locale)
        if seed is not None:
            self.fake.seed_instance(seed)
        self.profile = LOCALE_PROFILES.get(locale)
        self._custom_functions: Dict[str, Union[List[Any], Callable[[], Any]]] = {}
        self._used_keys: Dict[str, set] = {}
        self._counters: Dict[str, int] = {}

    # --- Personal data ---

    def name(self) -> str:
        """Generate a fake full name."""
        return self.fake.name()

    def first_name(self) -> str:
        """Generate a fake first name."""
        return self.fake.first_name()

    def last_name(self) -> str:
        """Generate a fake last name."""
        return self.fake.last_name()

    def email(self) -> str:
        """Generate a fake email address."""
        return self.fake.email()

    def phone(self) -> str:
        """Generate a fake phone number."""
        return self.fake.phone_number()

    # --- Location ---

    def address(self) -> str:
        """Generate a fake full address."""
        return self.fake.address()

    def city(self) -> str:
        """Generate a fake city name."""
        return self.fake.city()

    def state(self) -> str:
        """Generate a fake state / province / region name."""
        try:
            return self.fake.state()
        except AttributeError:
            return self.fake.city()

    def postcode(self) -> str:
        """Generate a fake postal code for the current locale."""
        return self.fake.postcode()

    def country(self) -> str:
        """Generate a fake country name."""
        return self.fake.country()

    # --- Company ---

    def company(self) -> str:
        """Generate a fake company name."""
        return self.fake.company()

    def job(self) -> str:
        """Generate a fake job title."""
        return self.fake.job()

    # --- Text ---

    def text(self, max_nb_chars: int = 200) -> str:
        """
        Generate fake text.

        Args:
            max_nb_chars: Maximum number of characters.
        """
        return self.fake.text(max_nb_chars=max_nb_chars)

    def paragraph(self, nb_sentences: int = 3) -> str:
        """
        Generate a fake paragraph.

        Args:
            nb_sentences: Number of sentences in the paragraph.
        """
        return self.fake.paragraph(nb_sentences=nb_sentences)

    def sentence(self) -> str:
        """Generate a fake sentence."""
        return self.fake.sentence()

    def word(self) -> str:
        """Generate a fake word."""
        return self.fake.word()

    def words(self, nb: int = 5) -> List[str]:
        """
        Generate a list of fake words.

        Args:
            nb: Number of words to generate.
        """
        return self.fake.words(nb=nb)

    # --- ID documents (locale-aware) ---

    def id_document(self, doc_type: Optional[str] = None) -> str:
        """
        Generate a fake ID document based on the configured locale.

        Without arguments, generates the country's primary document:
          - es_ES -> DNI/NIF
          - en_US -> SSN
          - pt_BR -> CPF
          - etc.

        Args:
            doc_type: Specific document type (e.g. 'NIE', 'CNPJ',
                     'CUIL', 'RFC', 'EIN'). None for the primary one.

        Raises:
            ValueError: If the locale has no configured profile.
        """
        if not self.profile:
            raise ValueError(f"Locale '{self.locale}' has no document profile. Supported locales: {list(LOCALE_PROFILES.keys())}")
        return _generate_id_document(self.fake, self.profile, doc_type, rng=self._rng)

    def dni(self) -> str:
        """Generate a DNI / primary ID document for the current locale."""
        return self.id_document()

    def available_documents(self) -> List[str]:
        """Return the available document types for the current locale."""
        if not self.profile:
            return []
        docs = [self.profile.id_document_name]
        docs.extend(self.profile.extra_id_documents.keys())
        return docs

    # --- Financial / banking ---

    def currency_code(self) -> str:
        """Return the locale's currency code (e.g. 'EUR', 'USD')."""
        if self.profile:
            return self.profile.currency_code
        return self.fake.currency_code()

    def currency_symbol(self) -> str:
        """Return the locale's currency symbol (e.g. '\u20ac', '$')."""
        if self.profile:
            return self.profile.currency_symbol
        return "$"

    def price(self, min_val: float = 1.0, max_val: float = 1000.0, decimals: int = 2) -> str:
        """
        Generate a fake price formatted with the local currency symbol.

        Args:
            min_val: Minimum value.
            max_val: Maximum value.
            decimals: Number of decimal places.
        """
        value = round(self._rng.uniform(min_val, max_val), decimals)
        symbol = self.currency_symbol()
        return f"{symbol}{value:,.{decimals}f}"

    def iban(self) -> str:
        """Generate a fake IBAN (available for European locales)."""
        try:
            return self.fake.iban()
        except AttributeError:
            return self.fake.bban() if hasattr(self.fake, "bban") else "N/A"

    def bban(self) -> str:
        """Generate a fake Basic Bank Account Number (BBAN)."""
        try:
            return self.fake.bban()
        except AttributeError:
            return "".join(str(self._rng.randint(0, 9)) for _ in range(20))

    def swift(self) -> str:
        """Generate a fake SWIFT/BIC code."""
        try:
            return self.fake.swift()
        except AttributeError:
            bank = "".join(self._rng.choices(string.ascii_uppercase, k=4))
            country = self.locale[-2:].upper() if len(self.locale) >= 2 else "XX"
            location = "".join(self._rng.choices(string.ascii_uppercase + string.digits, k=2))
            branch = "".join(self._rng.choices(string.ascii_uppercase + string.digits, k=3))
            return f"{bank}{country}{location}{branch}"

    def credit_card_number(self) -> str:
        """Generate a fake credit card number."""
        return self.fake.credit_card_number()

    def credit_card_expire(self) -> str:
        """Generate a fake credit card expiration date (MM/YY)."""
        return self.fake.credit_card_expire()

    def credit_card_provider(self) -> str:
        """Generate a fake credit card provider (Visa, MasterCard, etc.)."""
        return self.fake.credit_card_provider()

    def credit_card_security_code(self) -> str:
        """Generate a fake security code (CVV/CVC)."""
        return self.fake.credit_card_security_code()

    def credit_card_full(self) -> str:
        """Generate full fake card details: provider, number, expiry, CVV."""
        return self.fake.credit_card_full()

    def cryptocurrency_code(self) -> str:
        """Generate a fake cryptocurrency code (BTC, ETH, etc.)."""
        return self.fake.cryptocurrency_code()

    def cryptocurrency_name(self) -> str:
        """Generate a fake cryptocurrency name."""
        return self.fake.cryptocurrency_name()

    # --- Dates with locale format ---

    def date(self, pattern: Optional[str] = None) -> str:
        """
        Generate a fake date with locale-aware format.

        Args:
            pattern: Date format string. If None, uses the locale's format.
        """
        fmt = pattern or (self.profile.date_format if self.profile else "%Y-%m-%d")
        return self.fake.date(pattern=fmt)

    # --- Random numbers (locale-aware) ---

    # Locale-specific number formatting rules
    _NUMBER_FORMATS: Dict[str, Dict[str, str]] = {
        # decimal_sep, thousands_sep, currency_position ("before"/"after")
        "es_ES": {"decimal": ",", "thousands": ".", "cur_pos": "after", "cur_space": True},
        "es_MX": {"decimal": ".", "thousands": ",", "cur_pos": "before", "cur_space": False},
        "es_AR": {"decimal": ",", "thousands": ".", "cur_pos": "before", "cur_space": True},
        "es_CO": {"decimal": ",", "thousands": ".", "cur_pos": "before", "cur_space": True},
        "es_CL": {"decimal": ",", "thousands": ".", "cur_pos": "before", "cur_space": True},
        "en_US": {"decimal": ".", "thousands": ",", "cur_pos": "before", "cur_space": False},
        "en_GB": {"decimal": ".", "thousands": ",", "cur_pos": "before", "cur_space": False},
        "pt_BR": {"decimal": ",", "thousands": ".", "cur_pos": "before", "cur_space": True},
        "pt_PT": {"decimal": ",", "thousands": ".", "cur_pos": "after", "cur_space": True},
        "fr_FR": {"decimal": ",", "thousands": " ", "cur_pos": "after", "cur_space": True},
        "de_DE": {"decimal": ",", "thousands": ".", "cur_pos": "after", "cur_space": True},
        "it_IT": {"decimal": ",", "thousands": ".", "cur_pos": "after", "cur_space": True},
    }

    def _get_number_format(self) -> Dict[str, Any]:
        """Return number formatting rules for the current locale."""
        return self._NUMBER_FORMATS.get(
            self.locale,
            {"decimal": ".", "thousands": ",", "cur_pos": "before", "cur_space": False},
        )

    def _format_number_locale(
        self,
        value: Union[int, float],
        decimals: Optional[int] = None,
    ) -> str:
        """Format a number according to the current locale's conventions."""
        nf = self._get_number_format()
        if isinstance(value, float) and decimals is not None:
            # Format with decimals using standard '.' then replace
            formatted = f"{value:,.{decimals}f}"
        elif isinstance(value, float):
            formatted = f"{value:,.2f}"
        else:
            formatted = f"{value:,}"

        # Standard format uses ',' for thousands and '.' for decimal.
        # Replace in two steps via placeholder to avoid collisions.
        formatted = formatted.replace(",", "\x00").replace(".", "\x01")
        formatted = formatted.replace("\x00", nf["thousands"]).replace("\x01", nf["decimal"])
        return formatted

    def random_number(
        self,
        number_type: str = "integer",
        digits: int = 6,
        decimals: int = 2,
        min_val: Optional[Union[int, float]] = None,
        max_val: Optional[Union[int, float]] = None,
        mask: Optional[str] = None,
        currency: bool = False,
    ) -> str:
        """
        Generate a random number with locale-aware formatting.

        Args:
            number_type: ``"integer"`` or ``"float"``.
            digits: Approximate number of significant digits (ignored when
                   *min_val*/*max_val* are provided).
            decimals: Number of decimal places (only for floats).
            min_val: Explicit minimum value (overrides *digits*).
            max_val: Explicit maximum value (overrides *digits*).
            mask: Optional format mask.  Use ``#`` for digit positions and
                 any literal characters you like.  Special tokens:
                 ``{value}`` is replaced by the locale-formatted number and
                 ``{currency}`` by the locale's currency symbol.
                 Examples: ``"${value}"``, ``"{value} €"``,
                 ``"###-###-##"`` (each ``#`` becomes a random digit),
                 ``"REF-{value}"``.
            currency: If ``True`` the number is prefixed/suffixed with the
                     locale's currency symbol using the locale's convention
                     (position and spacing). Ignored when *mask* is
                     provided.

        Returns:
            Formatted number string.

        Examples:
            gen = TextDummy("es_ES")
            gen.random_number()                              # "482.193"
            gen.random_number("float", decimals=2)           # "482.193,45"
            gen.random_number("integer", digits=4)           # "7.391"
            gen.random_number("float", min_val=0, max_val=100, decimals=3)
                                                             # "57,482"
            gen.random_number("float", currency=True)        # "482.193,45 €"
            gen.random_number("integer", mask="INV-######")  # "INV-482193"
            gen.random_number("float", decimals=2,
                              mask="{currency}{value}")      # "€482.193,45"
        """
        # ── determine raw value ──────────────────────────────
        if min_val is not None and max_val is not None:
            if number_type == "float":
                raw = round(self._rng.uniform(float(min_val), float(max_val)), decimals)
            else:
                raw = self._rng.randint(int(min_val), int(max_val))
        else:
            lo = 10 ** (digits - 1)
            hi = (10**digits) - 1
            if number_type == "float":
                raw = round(self._rng.uniform(float(lo), float(hi)), decimals)
            else:
                raw = self._rng.randint(lo, hi)

        # ── mask with '#' placeholders (digit-by-digit) ──────
        if mask and "#" in mask:
            result = []
            for ch in mask:
                if ch == "#":
                    result.append(str(self._rng.randint(0, 9)))
                else:
                    result.append(ch)
            return "".join(result)

        # ── locale-formatted value ───────────────────────────
        if number_type == "float":
            formatted = self._format_number_locale(raw, decimals)
        else:
            formatted = self._format_number_locale(raw)

        # ── mask with {value} / {currency} tokens ────────────
        if mask:
            symbol = self.currency_symbol() if self.profile else "$"
            return mask.replace("{value}", formatted).replace("{currency}", symbol)

        # ── currency formatting (locale-aware position) ──────
        if currency:
            nf = self._get_number_format()
            symbol = self.currency_symbol() if self.profile else "$"
            space = " " if nf.get("cur_space") else ""
            if nf["cur_pos"] == "after":
                return f"{formatted}{space}{symbol}"
            return f"{symbol}{space}{formatted}"

        return formatted

    # --- Random dates ---

    def random_date(
        self,
        start: Optional[str] = None,
        end: Optional[str] = None,
        pattern: Optional[str] = None,
        mask: Optional[str] = None,
    ) -> str:
        """
        Generate a random date within a range with locale-aware formatting.

        Args:
            start: Start date as ``"YYYY-MM-DD"`` string.
                  Defaults to ``"1970-01-01"``.
            end: End date as ``"YYYY-MM-DD"`` string.
                Defaults to today.
            pattern: Output date format (strftime). If ``None``, uses the
                    locale's default format (e.g. ``"%d/%m/%Y"`` for
                    ``es_ES``, ``"%m/%d/%Y"`` for ``en_US``).
            mask: Optional output mask.  Use ``{date}`` as placeholder for
                 the formatted date, plus any literal text.
                 ``{year}``, ``{month}``, ``{day}`` are also available for
                 individual components.
                 Examples: ``"FEC-{year}{month}{day}"``,
                 ``"Date: {date}"``.

        Returns:
            Formatted date string.

        Examples:
            gen = TextDummy("es_ES")
            gen.random_date()
                # "15/03/1998"
            gen.random_date("2020-01-01", "2025-12-31")
                # "22/07/2023"
            gen.random_date(pattern="%Y-%m-%d")
                # "1998-03-15"
            gen.random_date(mask="FEC-{year}{month}{day}")
                # "FEC-19980315"
            gen.random_date("2020-01-01", "2025-12-31",
                           mask="Report_{year}-Q{quarter}")
                # "Report_2023-Q3"

            gen_us = TextDummy("en_US")
            gen_us.random_date()
                # "03/15/1998"  (mm/dd/yyyy)
        """
        start_date = datetime.datetime.strptime(start, "%Y-%m-%d").date() if start else datetime.date(1970, 1, 1)
        end_date = datetime.datetime.strptime(end, "%Y-%m-%d").date() if end else datetime.date.today()

        delta_days = (end_date - start_date).days
        if delta_days < 0:
            start_date, end_date = end_date, start_date
            delta_days = -delta_days
        random_day = start_date + datetime.timedelta(days=self._rng.randint(0, delta_days))

        fmt = pattern or (self.profile.date_format if self.profile else "%Y-%m-%d")
        formatted = random_day.strftime(fmt)

        if mask:
            quarter = (random_day.month - 1) // 3 + 1
            return (
                mask.replace("{date}", formatted)
                .replace("{year}", f"{random_day.year:04d}")
                .replace("{month}", f"{random_day.month:02d}")
                .replace("{day}", f"{random_day.day:02d}")
                .replace("{quarter}", str(quarter))
            )

        return formatted

    # --- Unique keys ---

    def unique_key(
        self,
        length: int = 8,
        key_type: str = "alphanumeric",
        prefix: str = "",
        suffix: str = "",
        separator: str = "",
        segment_length: int = 0,
        uppercase: bool = True,
        group: str = "_default",
    ) -> str:
        """
        Generate a guaranteed-unique random key.

        Each generated key is tracked per *group* so that subsequent calls
        never return duplicates within the same ``TextDummy`` instance.

        Args:
            length: Number of random characters (excluding prefix/suffix).
            key_type: Character pool:
                ``"alphanumeric"`` – letters + digits (default),
                ``"alpha"``       – letters only,
                ``"numeric"``     – digits only,
                ``"hex"``         – hexadecimal (0-9, A-F),
                ``"uuid"``        – full UUID-4 (ignores *length*).
            prefix: Fixed string prepended to the key
                   (e.g. ``"USR-"``).
            suffix: Fixed string appended to the key.
            separator: If set together with *segment_length* > 0,
                      inserts *separator* every *segment_length* chars
                      (e.g. ``separator="-", segment_length=4`` →
                      ``"A1B2-C3D4-E5F6"``).
            segment_length: See *separator*.
            uppercase: If ``True`` (default) letters are uppercase.
            group: Namespace for uniqueness tracking. Different groups
                  maintain independent sets of used keys. Useful when
                  generating multiple key columns simultaneously.

        Returns:
            A unique key string.

        Examples:
            gen = TextDummy("es_ES")
            gen.unique_key()
                # "K4M9X2B7"
            gen.unique_key(prefix="USR-", length=6)
                # "USR-T3N8Q1"
            gen.unique_key(key_type="hex", length=12,
                          separator="-", segment_length=4)
                # "A3F1-7B2E-9C04"
            gen.unique_key(key_type="uuid")
                # "f47ac10b-58cc-4372-a567-0e02b2c3d479"
            gen.unique_key(key_type="numeric", length=10, prefix="INV-")
                # "INV-4829173056"
        """
        if group not in self._used_keys:
            self._used_keys[group] = set()

        seen = self._used_keys[group]

        if key_type == "uuid":
            for _ in range(10_000):
                raw = str(uuid.uuid4())
                candidate = f"{prefix}{raw}{suffix}"
                if candidate not in seen:
                    seen.add(candidate)
                    return candidate
            raise RuntimeError("Could not generate a unique UUID key after 10 000 attempts.")

        pools = {
            "alphanumeric": string.ascii_letters + string.digits,
            "alpha": string.ascii_letters,
            "numeric": string.digits,
            "hex": string.digits + "abcdef",
        }
        pool = pools.get(key_type)
        if pool is None:
            raise ValueError(f"Unknown key_type '{key_type}'. Valid options: {sorted(pools.keys()) + ['uuid']}")

        max_attempts = 100_000
        for _ in range(max_attempts):
            raw = "".join(self._rng.choices(pool, k=length))
            if uppercase:
                raw = raw.upper()
            else:
                raw = raw.lower()
            if separator and segment_length > 0:
                parts = [raw[i : i + segment_length] for i in range(0, len(raw), segment_length)]
                raw = separator.join(parts)
            candidate = f"{prefix}{raw}{suffix}"
            if candidate not in seen:
                seen.add(candidate)
                return candidate

        raise RuntimeError(f"Could not generate a unique key after {max_attempts:,} attempts. Consider increasing 'length' or changing 'key_type'.")

    def reset_unique_keys(self, group: Optional[str] = None) -> None:
        """
        Clear tracked unique keys so they can be reused.

        Args:
            group: Reset only a specific group. If ``None``, resets all.
        """
        if group is None:
            self._used_keys.clear()
        else:
            self._used_keys.pop(group, None)

    # --- Autoincrement ---

    def autoincrement(
        self,
        start: int = 1,
        step: int = 1,
        prefix: str = "",
        suffix: str = "",
        zfill: int = 0,
        group: str = "_default",
    ) -> str:
        """
        Return the next value in an auto-incrementing sequence.

        Uses a per-*group* counter so multiple independent sequences
        can coexist within one ``TextDummy`` instance.

        Args:
            start: First value when the counter is initialised.
            step: Increment applied after each call.
            prefix: Fixed string prepended (e.g. ``"EMP-"``).
            suffix: Fixed string appended.
            zfill: Pad the numeric part with leading zeros to this width.
                  ``zfill=5`` → ``"00001"``, ``"00002"``, etc.
            group: Namespace for the counter. Different groups maintain
                  independent sequences. Useful for multiple autoincrement
                  columns.

        Returns:
            The next sequential value as a string.

        Examples:
            gen = TextDummy()
            gen.autoincrement()                   # "1"
            gen.autoincrement()                   # "2"
            gen.autoincrement(prefix="EMP-", zfill=5)
                # "EMP-00003"
            gen.autoincrement(start=1000, group="invoices")
                # "1000"
            gen.autoincrement(group="invoices")
                # "1001"
            gen.autoincrement(start=100, step=10, group="batch")
                # "100"
            gen.autoincrement(group="batch")
                # "110"
        """
        if group not in self._counters:
            self._counters[group] = (start, step)
        current, stored_step = self._counters[group]
        self._counters[group] = (current + stored_step, stored_step)
        num_str = str(current).zfill(zfill) if zfill else str(current)
        return f"{prefix}{num_str}{suffix}"

    def reset_autoincrement(self, group: Optional[str] = None) -> None:
        """
        Reset autoincrement counters.

        Args:
            group: Reset only a specific group. If ``None``, resets all.
        """
        if group is None:
            self._counters.clear()
        else:
            self._counters.pop(group, None)

    # --- Internet / technology ---

    def url(self) -> str:
        """Generate a fake URL."""
        return self.fake.url()

    def domain_name(self) -> str:
        """Generate a fake domain name."""
        return self.fake.domain_name()

    def username(self) -> str:
        """Generate a fake username."""
        return self.fake.user_name()

    def userlogin(self) -> str:
        """Generate a fake user login in a realistic format.

        Produces login identifiers like 'jsmith', 'maria.garcia',
        'mgarcia01', 'carlos_lopez', etc.
        """
        first = self.fake.first_name().lower()
        last = self.fake.last_name().lower()
        # Remove accents / non-ASCII for login safety
        first = unicodedata.normalize("NFKD", first).encode("ascii", "ignore").decode()
        last = unicodedata.normalize("NFKD", last).encode("ascii", "ignore").decode()
        fmt = self._rng.choice(
            [
                f"{first[0]}{last}",  # jsmith
                f"{first}.{last}",  # maria.garcia
                f"{first[0]}{last}{self._rng.randint(1, 99):02d}",  # mgarcia01
                f"{first}_{last}",  # carlos_lopez
                f"{first}{last[0]}",  # mariag
                f"{last}.{first[0]}",  # garcia.m
            ]
        )
        return fmt

    def password(
        self,
        length: int = 12,
        upper: bool = True,
        lower: bool = True,
        digits: bool = True,
        special: bool = True,
    ) -> str:
        """Generate a fake password.

        Args:
            length: Total password length (default 12).
            upper: Include uppercase letters.
            lower: Include lowercase letters.
            digits: Include digits.
            special: Include special characters.

        At least one character-set flag must be ``True``.
        The generated password is guaranteed to contain at least one
        character from every enabled set (when *length* permits).
        """
        pools: List[str] = []
        required: List[str] = []
        if upper:
            pools.append(string.ascii_uppercase)
            required.append(self._rng.choice(string.ascii_uppercase))
        if lower:
            pools.append(string.ascii_lowercase)
            required.append(self._rng.choice(string.ascii_lowercase))
        if digits:
            pools.append(string.digits)
            required.append(self._rng.choice(string.digits))
        if special:
            sp = "!@#$%^&*()-_=+[]{}|;:,.<>?"
            pools.append(sp)
            required.append(self._rng.choice(sp))
        if not pools:
            raise ValueError("At least one character-set flag must be True.")
        combined = "".join(pools)
        remaining = max(0, length - len(required))
        chars = required + [self._rng.choice(combined) for _ in range(remaining)]
        self._rng.shuffle(chars)
        return "".join(chars[:length])

    def ipv4(self) -> str:
        """Generate a fake IPv4 address."""
        return self.fake.ipv4()

    def ipv6(self) -> str:
        """Generate a fake IPv6 address."""
        return self.fake.ipv6()

    def mac_address(self) -> str:
        """Generate a fake MAC address."""
        return self.fake.mac_address()

    def user_agent(self) -> str:
        """Generate a fake browser User-Agent string."""
        return self.fake.user_agent()

    def slug(self) -> str:
        """Generate a fake URL slug."""
        return self.fake.slug()

    def uuid4(self) -> str:
        """Generate a fake UUID v4."""
        return self.fake.uuid4()

    # --- Files ---

    def file_name(self) -> str:
        """Generate a fake file name."""
        return self.fake.file_name()

    def file_extension(self) -> str:
        """Generate a fake file extension."""
        return self.fake.file_extension()

    def mime_type(self) -> str:
        """Generate a fake MIME type."""
        return self.fake.mime_type()

    def file_path(self) -> str:
        """Generate a fake file path."""
        return self.fake.file_path()

    # --- Extra personal data ---

    def date_of_birth(self, min_age: int = 18, max_age: int = 80) -> str:
        """
        Generate a fake date of birth with locale-aware format.

        Args:
            min_age: Minimum age.
            max_age: Maximum age.
        """
        dob = self.fake.date_of_birth(minimum_age=min_age, maximum_age=max_age)
        fmt = self.profile.date_format if self.profile else "%Y-%m-%d"
        return dob.strftime(fmt)

    def prefix(self) -> str:
        """Generate a fake name prefix (Mr., Mrs., Dr., etc.)."""
        return self.fake.prefix()

    def suffix(self) -> str:
        """Generate a fake name suffix (Jr., III, etc.)."""
        return self.fake.suffix()

    def ssn(self) -> str:
        """Generate a fake social security / tax ID number."""
        try:
            return self.fake.ssn()
        except AttributeError:
            return self.id_document()

    def gender(self, abbreviated: bool = False) -> str:
        """Generate a random gender using the locale language.

        Args:
            abbreviated: If ``True``, returns a short abbreviation
                (e.g. ``"M"`` / ``"F"``) instead of the full label.

        Returns locale-appropriate labels:
        ``es_*`` → Masculino / Femenino (M / F),
        ``en_*`` → Male / Female (M / F),
        ``fr_FR`` → Masculin / Féminin (M / F),
        ``de_DE`` → Männlich / Weiblich (M / W),
        ``it_IT`` → Maschio / Femmina (M / F),
        ``pt_*`` → Masculino / Feminino (M / F).
        """
        _GENDER_LABELS: Dict[str, tuple] = {
            "es": ("Masculino", "Femenino"),
            "en": ("Male", "Female"),
            "fr": ("Masculin", "Féminin"),
            "de": ("Männlich", "Weiblich"),
            "it": ("Maschio", "Femmina"),
            "pt": ("Masculino", "Feminino"),
        }
        _GENDER_ABBR: Dict[str, tuple] = {
            "es": ("M", "F"),
            "en": ("M", "F"),
            "fr": ("M", "F"),
            "de": ("M", "W"),
            "it": ("M", "F"),
            "pt": ("M", "F"),
        }
        lang = self.locale[:2] if self.locale else "en"
        if abbreviated:
            labels = _GENDER_ABBR.get(lang, ("M", "F"))
        else:
            labels = _GENDER_LABELS.get(lang, ("Male", "Female"))
        return self._rng.choice(labels)

    def age(self, min_val: int = 18, max_val: int = 80) -> int:
        """Generate a random age.

        Args:
            min_val: Minimum age (default 18).
            max_val: Maximum age (default 80).

        Returns:
            Random integer between *min_val* and *max_val*.
        """
        return self._rng.randint(min_val, max_val)

    def profile_data(self) -> Dict[str, Any]:
        """
        Generate a complete fake personal profile.

        Returns:
            Dict with name, address, email, phone, company, etc.
        """
        return {
            "name": self.name(),
            "first_name": self.first_name(),
            "last_name": self.last_name(),
            "email": self.email(),
            "phone": self.phone(),
            "address": self.address(),
            "city": self.city(),
            "postcode": self.postcode(),
            "country": self.country(),
            "company": self.company(),
            "job": self.job(),
            "date_of_birth": self.date_of_birth(),
            "username": self.username(),
        }

    # --- Vehicles ---

    def license_plate(self) -> str:
        """Generate a fake license plate number."""
        try:
            return self.fake.license_plate()
        except AttributeError:
            return "".join(self._rng.choices(string.ascii_uppercase, k=3)) + "-" + "".join(str(self._rng.randint(0, 9)) for _ in range(4))

    # --- Geolocation ---

    def latitude(self) -> str:
        """Generate a fake latitude."""
        return self.fake.latitude()

    def longitude(self) -> str:
        """Generate a fake longitude."""
        return self.fake.longitude()

    def coordinate(self) -> str:
        """Generate a fake coordinate pair (lat, lon)."""
        return f"{self.fake.latitude()}, {self.fake.longitude()}"

    # --- Colors ---

    def color_name(self) -> str:
        """Generate a fake color name."""
        return self.fake.color_name()

    def hex_color(self) -> str:
        """Generate a fake hexadecimal color (#RRGGBB)."""
        return self.fake.hex_color()

    def rgb_color(self) -> str:
        """Generate a fake RGB color."""
        return self.fake.rgb_color()

    # --- Codes and references ---

    def isbn10(self) -> str:
        """Generate a fake ISBN-10."""
        return self.fake.isbn10()

    def isbn13(self) -> str:
        """Generate a fake ISBN-13."""
        return self.fake.isbn13()

    def ean13(self) -> str:
        """Generate a fake EAN-13 barcode."""
        return self.fake.ean13()

    def ean8(self) -> str:
        """Generate a fake EAN-8 barcode."""
        return self.fake.ean8()

    # --- Products / commerce ---

    def product_name(self) -> str:
        """Generate a fake product name."""
        try:
            return self.fake.ecommerce_name()
        except AttributeError:
            adjectives = [
                "Premium",
                "Eco",
                "Smart",
                "Pro",
                "Ultra",
                "Lite",
                "Classic",
                "Deluxe",
                "Essential",
                "Elite",
                "Natural",
                "Organic",
                "Digital",
                "Portable",
                "Compact",
            ]
            nouns = [
                "Headphones",
                "Camera",
                "Laptop",
                "Watch",
                "Backpack",
                "Chair",
                "Lamp",
                "Keyboard",
                "Monitor",
                "Speaker",
                "Battery",
                "Charger",
                "Tablet",
                "Printer",
                "Router",
                "Sneakers",
                "Bottle",
                "Thermos",
                "Glasses",
                "Case",
            ]
            return f"{self._rng.choice(adjectives)} {self._rng.choice(nouns)}"

    def product_category(self) -> str:
        """Generate a fake product category."""
        try:
            return self.fake.ecommerce_category()
        except AttributeError:
            categories = [
                "Electronics",
                "Home & Garden",
                "Fashion",
                "Sports",
                "Food & Beverage",
                "Health & Beauty",
                "Toys",
                "Books",
                "Automotive",
                "Garden",
                "Computers",
                "Mobile",
                "Appliances",
                "Office",
                "Pets",
                "Baby",
                "DIY",
                "Music",
                "Video Games",
                "Stationery",
            ]
            return self._rng.choice(categories)

    def product_material(self) -> str:
        """Generate a fake product material."""
        materials = [
            "Cotton",
            "Plastic",
            "Wood",
            "Stainless Steel",
            "Aluminum",
            "Leather",
            "Silicone",
            "Glass",
            "Ceramic",
            "Bamboo",
            "Polyester",
            "Nylon",
            "Titanium",
            "Carbon Fiber",
            "Linen",
            "Rubber",
            "Cork",
            "Marble",
            "Granite",
            "ABS",
        ]
        return self._rng.choice(materials)

    def product_sku(self) -> str:
        """Generate a fake product SKU (e.g. 'ELEC-A3X9-2847')."""
        prefix = "".join(self._rng.choices(string.ascii_uppercase, k=4))
        mid = "".join(self._rng.choices(string.ascii_uppercase + string.digits, k=4))
        suffix = "".join(str(self._rng.randint(0, 9)) for _ in range(4))
        return f"{prefix}-{mid}-{suffix}"

    def product_review(self) -> Dict[str, Any]:
        """Generate a fake product review."""
        rating = self._rng.randint(1, 5)
        return {
            "rating": rating,
            "title": self.fake.sentence(nb_words=self._rng.randint(3, 8)),
            "comment": self.fake.paragraph(nb_sentences=self._rng.randint(1, 4)),
            "author": self.name(),
            "date": self.date(),
            "verified_purchase": self._rng.choice([True, False]),
        }

    def product_full(self) -> Dict[str, Any]:
        """Generate a complete fake product with all details."""
        return {
            "name": self.product_name(),
            "sku": self.product_sku(),
            "category": self.product_category(),
            "material": self.product_material(),
            "price": self.price(),
            "ean": self.ean13(),
            "description": self.fake.paragraph(nb_sentences=3),
            "brand": self.company(),
            "in_stock": self._rng.choice([True, False]),
            "stock_qty": self._rng.randint(0, 500),
            "weight_kg": round(self._rng.uniform(0.1, 25.0), 2),
        }

    def department(self) -> str:
        """Generate a fake company department name."""
        departments = [
            "Sales",
            "Marketing",
            "Human Resources",
            "Finance",
            "Technology",
            "Operations",
            "Legal",
            "Customer Service",
            "Logistics",
            "Procurement",
            "Quality",
            "R&D",
            "Production",
            "Administration",
            "Communications",
        ]
        return self._rng.choice(departments)

    def payment_method(self) -> str:
        """Generate a fake payment method."""
        methods = [
            "Credit Card",
            "Debit Card",
            "PayPal",
            "Bank Transfer",
            "Cash",
            "Apple Pay",
            "Google Pay",
            "Direct Debit",
            "Cash on Delivery",
            "Cryptocurrency",
            "Financing",
            "Wire Transfer",
        ]
        return self._rng.choice(methods)

    def order_status(self) -> str:
        """Generate a fake order status."""
        statuses = [
            "Pending",
            "Confirmed",
            "Processing",
            "Shipped",
            "In Transit",
            "Delivered",
            "Returned",
            "Cancelled",
            "Refunded",
            "On Hold",
        ]
        return self._rng.choice(statuses)

    def tracking_number(self) -> str:
        """Generate a fake shipping tracking number."""
        prefix = "".join(self._rng.choices(string.ascii_uppercase, k=2))
        digits = "".join(str(self._rng.randint(0, 9)) for _ in range(12))
        country = self.locale[-2:].upper() if len(self.locale) >= 2 else "XX"
        return f"{prefix}{digits}{country}"

    def invoice_number(self) -> str:
        """Generate a fake invoice number (e.g. 'INV-2026-00342')."""
        from datetime import datetime

        year = datetime.now().year
        seq = self._rng.randint(1, 99999)
        return f"INV-{year}-{seq:05d}"

    # --- Random selection from lists ---

    @staticmethod
    def random_from_list(values: Sequence[Any]) -> Any:
        """
        Return a random element from the given sequence.

        Args:
            values: Sequence of values (list, tuple, etc.).

        Raises:
            ValueError: If the sequence is empty.
        """
        if not values:
            raise ValueError("The values sequence must not be empty.")
        return _random.choice(values)

    @staticmethod
    def random_sample_from_list(
        values: Sequence[Any],
        count: int = 1,
        allow_duplicates: bool = True,
    ) -> List[Any]:
        """
        Return multiple random elements from the given sequence.

        Args:
            values: Sequence of values.
            count: Number of elements to return.
            allow_duplicates: If True, allows repetitions (choices).
                             If False, no repetition (sample); count
                             cannot exceed len(values).

        Raises:
            ValueError: If the sequence is empty or count > len(values)
                       without duplicates.
        """
        if not values:
            raise ValueError("The values sequence must not be empty.")
        if allow_duplicates:
            return _random.choices(values, k=count)
        return _random.sample(list(values), k=count)

    @staticmethod
    def weighted_random_from_list(
        values: Sequence[Any],
        weights: Sequence[float],
    ) -> Any:
        """
        Return a weighted random element from the given sequence.

        Args:
            values: Sequence of values.
            weights: Corresponding weight for each value.
        """
        if not values:
            raise ValueError("The values sequence must not be empty.")
        return _random.choices(values, weights=weights, k=1)[0]

    # --- Custom generators ---

    def register_custom(
        self,
        name: str,
        source: Union[List[Any], Callable[[], Any]],
    ) -> None:
        """
        Register a custom generator.

        The generator can be backed by a list (random selection) or a
        callable with no arguments that produces a value.

        Args:
            name: Unique name for the generator.
            source: List of possible values, or callable that returns a value.

        Raises:
            TypeError: If *source* is neither a list nor callable.

        Example:
            gen = TextDummy("es_ES")
            gen.register_custom("t_shirt_size", ["XS", "S", "M", "L", "XL"])
            gen.register_custom("ticket", lambda: f"TK-{random.randint(1000,9999)}")

            print(gen.run_custom("t_shirt_size"))  # "M"
            print(gen.run_custom("ticket"))        # "TK-4821"
        """
        if not (isinstance(source, list) or callable(source)):
            raise TypeError(f"source must be a list or callable, got {type(source).__name__}")
        self._custom_functions[name] = source

    def unregister_custom(self, name: str) -> None:
        """Remove a registered custom generator."""
        self._custom_functions.pop(name, None)

    def run_custom(self, name: str) -> Any:
        """
        Generate a value from a registered custom generator.

        Args:
            name: Name of the registered generator.

        Returns:
            Generated value.

        Raises:
            ValueError: If *name* is not registered.
        """
        if name not in self._custom_functions:
            raise ValueError(f"Custom generator '{name}' not registered. Registered: {list(self._custom_functions.keys())}")
        source = self._custom_functions[name]
        if callable(source):
            return source()
        return self._rng.choice(source)

    def list_custom(self) -> Dict[str, str]:
        """
        List registered custom generators.

        Returns:
            Dict mapping name to type description ('list[N]' or 'callable').
        """
        result = {}
        for name, source in self._custom_functions.items():
            if callable(source):
                result[name] = "callable"
            else:
                result[name] = f"list[{len(source)}]"
        return result

    # --- Pydantic model filling ---

    def fill_model(
        self,
        model_class: type,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """
        Fill a Pydantic BaseModel subclass with fake data.

        Introspects field names and type annotations to choose appropriate
        generators. Field names are matched first against known generator
        methods and common aliases, then resolved by type annotation.
        Supports nested models, Optional, List, Enum, and primitive types.

        Fields can be explicitly mapped to generators in three ways:

        1. **Annotated + DummyField** (recommended for reusable models):
           Use ``Annotated[type, DummyField("generator")]`` in the model.

        2. **overrides with a string** (generator name):
           Pass ``{"field": "generator_name"}`` — the string will be
           resolved as a TextDummy method or custom generator.

        3. **overrides with a value or callable** (fixed values):
           Pass ``{"field": value}`` or ``{"field": lambda: ...}``.

        Args:
            model_class: A Pydantic BaseModel subclass (the class itself).
            overrides: Dict of field_name -> value, callable, or generator
                      name (str matching a TextDummy method). Callables
                      are invoked; strings matching a known generator are
                      used to produce the value; other values are used
                      directly.

        Returns:
            An instance of model_class populated with fake data.

        Raises:
            TypeError: If model_class is not a Pydantic BaseModel subclass.
            ImportError: If pydantic is not installed.

        Example:
            from pydantic import BaseModel
            from typing import Annotated

            class User(BaseModel):
                name: str
                email: str
                age: int
                active: bool

            gen = TextDummy("es_ES")
            user = gen.fill_model(User)
            # User(name='María García', email='maria@example.com', age=42, active=True)

            # Using DummyField for fields whose name doesn't match a generator:
            class Employee(BaseModel):
                codigo: Annotated[str, DummyField("uuid4")]
                ref: Annotated[str, DummyField("product_sku")]
                contacto: Annotated[str, DummyField("email")]
                responsable: Annotated[str, DummyField("name")]

            emp = gen.fill_model(Employee)

            # Using overrides with generator names:
            class Record(BaseModel):
                code: str
                ref: str

            rec = gen.fill_model(Record, overrides={"code": "uuid4", "ref": "iban"})

            # Nested models:
            class Address(BaseModel):
                street: str
                city: str
                postcode: str

            class Customer(BaseModel):
                name: str
                email: str
                address: Address

            customer = gen.fill_model(Customer)

            # With value overrides:
            user = gen.fill_model(User, overrides={"active": True, "age": lambda: 25})
        """
        try:
            from pydantic import BaseModel
        except ImportError:
            raise ImportError("pydantic is required for fill_model(). Install it with: pip install pydantic")

        if not (isinstance(model_class, type) and issubclass(model_class, BaseModel)):
            raise TypeError(f"model_class must be a Pydantic BaseModel subclass, got {type(model_class)}")

        overrides = overrides or {}
        field_values = {}

        for field_name, field_info in model_class.model_fields.items():
            if field_name in overrides:
                val = overrides[field_name]
                if callable(val):
                    field_values[field_name] = val()
                elif isinstance(val, str) and self._is_generator_name(val):
                    field_values[field_name] = self._call_generator(val)
                else:
                    field_values[field_name] = val
            else:
                # Check for DummyField in Pydantic field metadata
                dummy_marker = None
                for meta in getattr(field_info, "metadata", []):
                    if isinstance(meta, DummyField):
                        dummy_marker = meta
                        break
                if dummy_marker:
                    field_values[field_name] = self._call_generator(dummy_marker.generator, **dummy_marker.kwargs)
                else:
                    field_values[field_name] = self._resolve_field_value(field_name, field_info.annotation)

        return model_class(**field_values)

    def fill_model_batch(
        self,
        model_class: type,
        count: int = 10,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> list:
        """
        Generate multiple instances of a Pydantic model with fake data.

        Args:
            model_class: A Pydantic BaseModel subclass.
            count: Number of instances to generate.
            overrides: Dict of field_name -> value or callable.

        Returns:
            List of model instances.
        """
        return [self.fill_model(model_class, overrides) for _ in range(count)]

    def to_records(
        self,
        model_class: type,
        count: int = 1000,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Generate fake data in record (row) format.

        Each element is a dict representing one row, with field names as
        keys. Equivalent to a list of dicts / JSON array of objects.

        Args:
            model_class: A Pydantic BaseModel subclass defining the schema.
            count: Number of records to generate (default 1000).
            overrides: Dict of field_name -> value, callable, or generator name.

        Returns:
            List of dicts, one per record.

        Example:
            class User(BaseModel):
                name: str
                email: str
                age: int

            gen = TextDummy("es_ES")
            rows = gen.to_records(User, count=5)
            # [
            #   {"name": "María García", "email": "maria@example.com", "age": 34},
            #   {"name": "Carlos López", "email": "carlos@example.com", "age": 28},
            #   ...
            # ]
        """
        instances = self.fill_model_batch(model_class, count, overrides)
        return [inst.model_dump() for inst in instances]

    def to_columns(
        self,
        model_class: type,
        count: int = 1000,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, list]:
        """
        Generate fake data in column format.

        Returns a dict where each key is a field name and each value is a
        list of all generated values for that field. This format is ideal
        for creating DataFrames (``pd.DataFrame(gen.to_columns(Model))``).

        Args:
            model_class: A Pydantic BaseModel subclass defining the schema.
            count: Number of values per column (default 1000).
            overrides: Dict of field_name -> value, callable, or generator name.

        Returns:
            Dict of field_name -> list of values.

        Example:
            class User(BaseModel):
                name: str
                email: str
                age: int

            gen = TextDummy("es_ES")
            cols = gen.to_columns(User, count=5)
            # {
            #   "name":  ["María García", "Carlos López", ...],
            #   "email": ["maria@example.com", "carlos@example.com", ...],
            #   "age":   [34, 28, ...],
            # }

            # Direct DataFrame creation:
            import pandas as pd
            df = pd.DataFrame(gen.to_columns(User, count=1000))
        """
        records = self.to_records(model_class, count, overrides)
        if not records:
            return {}
        return {key: [r[key] for r in records] for key in records[0]}

    def _is_generator_name(self, name: str) -> bool:
        """Check if a string is a valid generator method or custom generator."""
        return hasattr(self, name) and callable(getattr(self, name)) or name in self._custom_functions

    def _call_generator(self, name: str, **kwargs: Any) -> Any:
        """Call a generator method by name, with optional kwargs."""
        if name in self._custom_functions:
            return self.run_custom(name)
        method = getattr(self, name, None)
        if method and callable(method):
            return method(**kwargs) if kwargs else method()
        raise ValueError(f"Unknown generator '{name}'. Use a TextDummy method name or a registered custom generator.")

    def _resolve_field_value(self, field_name: str, annotation: Any) -> Any:
        """Resolve a fake value for a model field based on its name and type."""
        import enum as _enum
        import typing as _typing
        from typing import get_origin, get_args

        if annotation is None or annotation is type(None):
            return None

        # Check for DummyField in Annotated metadata (non-Pydantic usage)
        if hasattr(annotation, "__metadata__"):
            for meta in annotation.__metadata__:
                if isinstance(meta, DummyField):
                    return self._call_generator(meta.generator, **meta.kwargs)
            # No DummyField found — unwrap to inner type
            args = get_args(annotation)
            if args:
                return self._resolve_field_value(field_name, args[0])

        origin = get_origin(annotation)

        # Handle Optional[X] / Union[X, None]
        if origin is Union:
            non_none = [a for a in get_args(annotation) if a is not type(None)]
            if non_none:
                return self._resolve_field_value(field_name, non_none[0])
            return None

        # Python 3.10+ union syntax (X | Y)
        try:
            import types as _types

            if isinstance(annotation, _types.UnionType):
                non_none = [a for a in get_args(annotation) if a is not type(None)]
                if non_none:
                    return self._resolve_field_value(field_name, non_none[0])
                return None
        except AttributeError:
            pass

        # Handle List[X]
        if origin is list:
            inner = get_args(annotation)[0] if get_args(annotation) else str
            count = self._rng.randint(1, 3)
            return [self._resolve_field_value(f"{field_name}_item", inner) for _ in range(count)]

        # Handle Dict[K, V]
        if origin is dict:
            return {}

        # Handle Set[X]
        if origin is set:
            inner = get_args(annotation)[0] if get_args(annotation) else str
            count = self._rng.randint(1, 3)
            return {self._resolve_field_value(f"{field_name}_item", inner) for _ in range(count)}

        # Nested Pydantic model
        try:
            from pydantic import BaseModel as _BaseModel

            if isinstance(annotation, type) and issubclass(annotation, _BaseModel):
                return self.fill_model(annotation)
        except (ImportError, TypeError):
            pass

        # Enum
        if isinstance(annotation, type) and issubclass(annotation, _enum.Enum):
            members = list(annotation)
            return self._rng.choice(members) if members else None

        # Field name match (only for str or Any-typed fields)
        if annotation is str or annotation is _typing.Any:
            generator_name = _FIELD_NAME_GENERATORS.get(field_name.lower())
            if generator_name:
                gen_method = getattr(self, generator_name, None)
                if gen_method:
                    return gen_method()

        # Field name match for numeric/bool types (e.g. age → age())
        if annotation in (int, float, bool):
            generator_name = _FIELD_NAME_GENERATORS.get(field_name.lower())
            if generator_name:
                gen_method = getattr(self, generator_name, None)
                if gen_method:
                    return gen_method()

        # Primitive type fallbacks
        if annotation is str or annotation is _typing.Any:
            return self.word()
        if annotation is int:
            return self._rng.randint(0, 1000)
        if annotation is float:
            return round(self._rng.uniform(0.0, 1000.0), 2)
        if annotation is bool:
            return self._rng.choice([True, False])
        if annotation is datetime.date:
            return self.fake.date_object()
        if annotation is datetime.datetime:
            return self.fake.date_time()

        try:
            from decimal import Decimal

            if annotation is Decimal:
                return Decimal(str(round(self._rng.uniform(0.0, 1000.0), 2)))
        except ImportError:
            pass

        if annotation is bytes:
            return self._rng.randbytes(16)

        # Fallback
        return self.word()

    # --- Locale information ---

    def locale_info(self) -> Dict[str, Any]:
        """
        Return information about the current locale.

        Returns:
            Dict with locale metadata (country, language, currency,
            available documents, etc.).
        """
        if not self.profile:
            return {
                "locale": self.locale,
                "has_profile": False,
                "note": "Faker still works but without country-specific generators.",
            }
        p = self.profile
        return {
            "locale": p.code,
            "country": p.country,
            "language": p.language,
            "currency": f"{p.currency_code} ({p.currency_symbol})",
            "phone_prefix": p.phone_prefix,
            "date_format": p.date_format,
            "id_document": p.id_document_name,
            "extra_documents": list(p.extra_id_documents.keys()) or None,
            "has_state_province": p.has_state_province,
        }

    # --- Batch generation ---

    def generate_batch(self, data_type: str, count: int = 10) -> List[str]:
        """
        Generate multiple values of the same type.

        Args:
            data_type: Data type name (e.g. 'name', 'email', 'phone',
                      'address', 'city', 'company', 'product_name',
                      'iban', 'credit_card_number', or any custom generator).
            count: Number of items to generate.

        Returns:
            List of generated values.
        """
        generators = {
            # Personal data
            "name": self.name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "phone": self.phone,
            "date_of_birth": self.date_of_birth,
            "prefix": self.prefix,
            "suffix": self.suffix,
            "ssn": self.ssn,
            # Location
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "postcode": self.postcode,
            "country": self.country,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "coordinate": self.coordinate,
            # Company
            "company": self.company,
            "job": self.job,
            "department": self.department,
            # Text
            "sentence": self.sentence,
            "word": self.word,
            # ID documents
            "dni": self.dni,
            "id_document": self.id_document,
            # Financial / banking
            "price": self.price,
            "iban": self.iban,
            "bban": self.bban,
            "swift": self.swift,
            "credit_card_number": self.credit_card_number,
            "credit_card_expire": self.credit_card_expire,
            "credit_card_provider": self.credit_card_provider,
            "credit_card_security_code": self.credit_card_security_code,
            "credit_card_full": self.credit_card_full,
            "cryptocurrency_code": self.cryptocurrency_code,
            "cryptocurrency_name": self.cryptocurrency_name,
            "payment_method": self.payment_method,
            "invoice_number": self.invoice_number,
            # Internet / technology
            "url": self.url,
            "domain_name": self.domain_name,
            "username": self.username,
            "userlogin": self.userlogin,
            "password": self.password,
            "ipv4": self.ipv4,
            "ipv6": self.ipv6,
            "mac_address": self.mac_address,
            "user_agent": self.user_agent,
            "slug": self.slug,
            "uuid4": self.uuid4,
            # Files
            "file_name": self.file_name,
            "file_extension": self.file_extension,
            "mime_type": self.mime_type,
            "file_path": self.file_path,
            # Dates
            "date": self.date,
            "random_date": self.random_date,
            # Numbers
            "random_number": self.random_number,
            # Vehicles
            "license_plate": self.license_plate,
            # Colors
            "color_name": self.color_name,
            "hex_color": self.hex_color,
            "rgb_color": self.rgb_color,
            # Codes / references
            "isbn10": self.isbn10,
            "isbn13": self.isbn13,
            "ean13": self.ean13,
            "ean8": self.ean8,
            # Products / commerce
            "product_name": self.product_name,
            "product_category": self.product_category,
            "product_material": self.product_material,
            "product_sku": self.product_sku,
            "order_status": self.order_status,
            "tracking_number": self.tracking_number,
            # Unique keys / autoincrement
            "unique_key": self.unique_key,
            "autoincrement": self.autoincrement,
            # Gender / age
            "gender": self.gender,
            "age": self.age,
        }

        # Check if it is a registered custom generator
        if data_type in self._custom_functions:
            return [self.run_custom(data_type) for _ in range(count)]

        if data_type not in generators:
            raise ValueError(
                f"Unsupported data type: {data_type}. Valid options: {sorted(list(generators.keys()) + list(self._custom_functions.keys()))}"
            )

        return [generators[data_type]() for _ in range(count)]

    # --- Class methods ---

    @staticmethod
    def supported_locales() -> Dict[str, str]:
        """
        Return the supported locales with full profiles.

        Returns:
            Dict with locale code as key and country name as value.
        """
        return {code: p.country for code, p in LOCALE_PROFILES.items()}


# ---------------------------------------------------------------------------
# Default instance cache
# ---------------------------------------------------------------------------

_generators: Dict[str, TextDummy] = {}


def get_generator(locale: str = "es_ES", seed: Optional[int] = None) -> TextDummy:
    """
    Get (or create and cache) a generator instance for the given locale.

    Args:
        locale: Language/country code.
        seed: Optional seed for reproducible generation. When provided,
             a new (non-cached) instance is returned to avoid polluting
             the shared cache.

    Returns:
        TextDummy instance.
    """
    if seed is not None:
        return TextDummy(locale, seed=seed)
    if locale not in _generators:
        _generators[locale] = TextDummy(locale)
    return _generators[locale]


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


def fake_name(locale: str = "es_ES") -> str:
    """Generate a fake full name."""
    return get_generator(locale).name()


def fake_email(locale: str = "es_ES") -> str:
    """Generate a fake email address."""
    return get_generator(locale).email()


def fake_phone(locale: str = "es_ES") -> str:
    """Generate a fake phone number."""
    return get_generator(locale).phone()


def fake_address(locale: str = "es_ES") -> str:
    """Generate a fake address."""
    return get_generator(locale).address()


def fake_text(max_chars: int = 200, locale: str = "es_ES") -> str:
    """Generate fake text."""
    return get_generator(locale).text(max_nb_chars=max_chars)


def fake_id_document(locale: str = "es_ES", doc_type: Optional[str] = None) -> str:
    """
    Generate a fake ID document for the given locale.

    Args:
        locale: Language/country code.
        doc_type: Specific document type (e.g. 'NIE', 'RFC', 'CNPJ').
    """
    return get_generator(locale).id_document(doc_type)


def fake_dni(locale: str = "es_ES") -> str:
    """Generate a primary ID document for the given locale."""
    return get_generator(locale).dni()


def fake_credit_card(locale: str = "es_ES") -> str:
    """Generate a fake credit card number."""
    return get_generator(locale).credit_card_number()


def fake_iban(locale: str = "es_ES") -> str:
    """Generate a fake IBAN."""
    return get_generator(locale).iban()


def fake_swift(locale: str = "es_ES") -> str:
    """Generate a fake SWIFT/BIC code."""
    return get_generator(locale).swift()


def fake_ipv4(locale: str = "es_ES") -> str:
    """Generate a fake IPv4 address."""
    return get_generator(locale).ipv4()


def fake_userlogin(locale: str = "es_ES") -> str:
    """Generate a fake user login."""
    return get_generator(locale).userlogin()


def fake_license_plate(locale: str = "es_ES") -> str:
    """Generate a fake license plate."""
    return get_generator(locale).license_plate()


def fake_date_of_birth(locale: str = "es_ES") -> str:
    """Generate a fake date of birth."""
    return get_generator(locale).date_of_birth()


def fake_profile(locale: str = "es_ES") -> Dict[str, Any]:
    """Generate a complete fake personal profile."""
    return get_generator(locale).profile_data()


def fake_product(locale: str = "es_ES") -> Dict[str, Any]:
    """Generate a complete fake product."""
    return get_generator(locale).product_full()


def fake_product_name(locale: str = "es_ES") -> str:
    """Generate a fake product name."""
    return get_generator(locale).product_name()


def random_from_list(values: Sequence[Any]) -> Any:
    """Return a random element from the given sequence."""
    return TextDummy.random_from_list(values)


def random_sample_from_list(
    values: Sequence[Any],
    count: int = 1,
    allow_duplicates: bool = True,
) -> List[Any]:
    """
    Return multiple random elements from the given sequence.

    Args:
        values: Sequence of values.
        count: Number of elements.
        allow_duplicates: If True allows repetitions.
    """
    return TextDummy.random_sample_from_list(values, count, allow_duplicates)


def fake_batch(data_type: str, count: int = 10, locale: str = "es_ES") -> List[str]:
    """
    Generate multiple fake values of the same type.

    Args:
        data_type: Data type to generate.
        count: Number of items.
        locale: Language/country code.
    """
    return get_generator(locale).generate_batch(data_type, count)


def fake_model(
    model_class: type,
    locale: str = "es_ES",
    overrides: Optional[Dict[str, Any]] = None,
) -> Any:
    """
    Fill a Pydantic BaseModel subclass with fake data.

    Args:
        model_class: A Pydantic BaseModel subclass.
        locale: Language/country code.
        overrides: Dict of field_name -> value or callable.
    """
    return get_generator(locale).fill_model(model_class, overrides)


def fake_model_batch(
    model_class: type,
    count: int = 10,
    locale: str = "es_ES",
    overrides: Optional[Dict[str, Any]] = None,
) -> list:
    """
    Generate multiple instances of a Pydantic model with fake data.

    Args:
        model_class: A Pydantic BaseModel subclass.
        count: Number of instances to generate.
        locale: Language/country code.
        overrides: Dict of field_name -> value or callable.
    """
    return get_generator(locale).fill_model_batch(model_class, count, overrides)


def fake_records(
    model_class: type,
    count: int = 1000,
    locale: str = "es_ES",
    overrides: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Generate fake data in record (row) format.

    Args:
        model_class: A Pydantic BaseModel subclass defining the schema.
        count: Number of records (default 1000).
        locale: Language/country code.
        overrides: Dict of field_name -> value, callable, or generator name.
    """
    return get_generator(locale).to_records(model_class, count, overrides)


def fake_columns(
    model_class: type,
    count: int = 1000,
    locale: str = "es_ES",
    overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, list]:
    """
    Generate fake data in column format.

    Args:
        model_class: A Pydantic BaseModel subclass defining the schema.
        count: Number of values per column (default 1000).
        locale: Language/country code.
        overrides: Dict of field_name -> value, callable, or generator name.
    """
    return get_generator(locale).to_columns(model_class, count, overrides)


def fake_random_number(
    number_type: str = "integer",
    digits: int = 6,
    decimals: int = 2,
    min_val: Optional[Union[int, float]] = None,
    max_val: Optional[Union[int, float]] = None,
    mask: Optional[str] = None,
    currency: bool = False,
    locale: str = "es_ES",
) -> str:
    """Generate a random locale-formatted number."""
    return get_generator(locale).random_number(
        number_type=number_type,
        digits=digits,
        decimals=decimals,
        min_val=min_val,
        max_val=max_val,
        mask=mask,
        currency=currency,
    )


def fake_random_date(
    start: Optional[str] = None,
    end: Optional[str] = None,
    pattern: Optional[str] = None,
    mask: Optional[str] = None,
    locale: str = "es_ES",
) -> str:
    """Generate a random locale-formatted date."""
    return get_generator(locale).random_date(
        start=start,
        end=end,
        pattern=pattern,
        mask=mask,
    )


def fake_unique_key(
    length: int = 8,
    key_type: str = "alphanumeric",
    prefix: str = "",
    suffix: str = "",
    separator: str = "",
    segment_length: int = 0,
    uppercase: bool = True,
    group: str = "_default",
    locale: str = "es_ES",
) -> str:
    """Generate a guaranteed-unique random key."""
    return get_generator(locale).unique_key(
        length=length,
        key_type=key_type,
        prefix=prefix,
        suffix=suffix,
        separator=separator,
        segment_length=segment_length,
        uppercase=uppercase,
        group=group,
    )


def fake_autoincrement(
    start: int = 1,
    step: int = 1,
    prefix: str = "",
    suffix: str = "",
    zfill: int = 0,
    group: str = "_default",
    locale: str = "es_ES",
) -> str:
    """Generate the next value in an auto-incrementing sequence."""
    return get_generator(locale).autoincrement(
        start=start,
        step=step,
        prefix=prefix,
        suffix=suffix,
        zfill=zfill,
        group=group,
    )


def fake_password(
    length: int = 12,
    upper: bool = True,
    lower: bool = True,
    digits: bool = True,
    special: bool = True,
    locale: str = "es_ES",
) -> str:
    """Generate a fake password."""
    return get_generator(locale).password(
        length=length,
        upper=upper,
        lower=lower,
        digits=digits,
        special=special,
    )


def fake_gender(locale: str = "es_ES", abbreviated: bool = False) -> str:
    """Generate a random gender label in the locale language."""
    return get_generator(locale).gender(abbreviated=abbreviated)


def fake_age(
    min_val: int = 18,
    max_val: int = 80,
    locale: str = "es_ES",
) -> int:
    """Generate a random age."""
    return get_generator(locale).age(min_val=min_val, max_val=max_val)
