"""
Text Dummy — locale-aware fake data generation.

Generate realistic fake PII, financial, identity, and product data
across 12 locales for testing and development.

Quick start::

    from shadetriptxt.text_dummy import TextDummy, fake_name, fake_email

    gen = TextDummy(locale="es_ES")
    print(gen.name())

    print(fake_name("en_US"))
    print(fake_email("pt_BR"))
"""

from .text_dummy import (
    # Classes
    TextDummy,
    DummyField,
    LocaleProfile,
    # Factory
    get_generator,
    # Convenience — personal
    fake_name,
    fake_email,
    fake_phone,
    fake_address,
    fake_text,
    fake_id_document,
    fake_dni,
    fake_credit_card,
    fake_iban,
    fake_swift,
    fake_ipv4,
    fake_userlogin,
    fake_license_plate,
    fake_date_of_birth,
    fake_profile,
    fake_gender,
    fake_age,
    fake_password,
    # Convenience — commerce
    fake_product,
    fake_product_name,
    # Convenience — batch / model
    fake_batch,
    fake_model,
    fake_model_batch,
    fake_records,
    fake_columns,
    # Convenience — numbers / dates / keys
    fake_random_number,
    fake_random_date,
    fake_unique_key,
    fake_autoincrement,
    # Utilities
    random_from_list,
    random_sample_from_list,
    # Constants
    LOCALE_PROFILES,
)

from .config import (
    Config,
    ConfigSchema,
    ConfigValue,
    ConfigSource,
    ConfigFormat,
    load_config,
    create_sample_config,
)
