# TextDummy — Fake Data Generator

Locale-aware fake data generation module powered by [Faker](https://faker.readthedocs.io/). Generates realistic synthetic data for testing, development, and demos across 60+ data types and 12 locales.

## Table of Contents

- [Quick Start](#quick-start)
- [Supported Locales](#supported-locales)
- [Reproducibility (seed)](#reproducibility-seed)
- [Function Categories](#function-categories)
- [Function Index](#function-index)
- [Detailed Reference](#detailed-reference)
  - [Personal Data](#personal-data)
  - [Location](#location)
  - [Company](#company)
  - [Text](#text)
  - [ID Documents](#id-documents)
  - [Financial / Banking](#financial--banking)
  - [Dates](#dates)
  - [Internet / Technology](#internet--technology)
  - [Files](#files)
  - [Extra Personal Data](#extra-personal-data)
  - [Vehicles](#vehicles)
  - [Geolocation](#geolocation)
  - [Colors](#colors)
  - [Codes / References](#codes--references)
  - [Products / Commerce](#products--commerce)
  - [Random Numbers](#random-numbers)
  - [Unique Keys](#unique-keys)
  - [Autoincrement](#autoincrement)
  - [Random Selection from Lists](#random-selection-from-lists)
  - [Custom Generators](#custom-generators)
  - [Locale Information](#locale-information)
  - [Batch Generation](#batch-generation)
  - [Pydantic Model Filling](#pydantic-model-filling)
  - [Records &amp; Columns](#records--columns)
- [TextDummy vs Faker](#textdummy-vs-faker)
- [Convenience Functions](#convenience-functions)
- [Instance Caching](#instance-caching)
- [Examples](#examples)

---

## Quick Start

```python
from shadetriptxt.text_dummy.text_dummy import TextDummy

gen = TextDummy("es_ES")       # Spanish (Spain) — default
gen.name()                     # "María García López"
gen.id_document()              # "45678123P"
gen.iban()                     # "ES9121000418450200051332"
gen.product_name()             # "Premium Keyboard"

gen_us = TextDummy("en_US")    # US English
gen_us.id_document()           # "456-78-1234"
gen_us.credit_card_number()    # "4111111111111111"

# Reproducible output with seed
gen_seed = TextDummy("es_ES", seed=42)
gen_seed.name()                # Always returns the same name
gen_seed.email()               # Always returns the same email
```

---

## Supported Locales

| Code      | Country        | Language   | Currency | ID Document     |
| --------- | -------------- | ---------- | -------- | --------------- |
| `es_ES` | Spain          | Spanish    | EUR (€) | DNI/NIF + NIE   |
| `es_MX` | Mexico         | Spanish    | MXN ($)  | CURP + RFC      |
| `es_AR` | Argentina      | Spanish    | ARS ($)  | DNI + CUIL      |
| `es_CO` | Colombia       | Spanish    | COP ($)  | Cédula         |
| `es_CL` | Chile          | Spanish    | CLP ($)  | RUT             |
| `en_US` | United States  | English    | USD ($)  | SSN + EIN       |
| `en_GB` | United Kingdom | English    | GBP (£) | NINO            |
| `pt_BR` | Brazil         | Portuguese | BRL (R$) | CPF + CNPJ      |
| `pt_PT` | Portugal       | Portuguese | EUR (€) | NIF             |
| `fr_FR` | France         | French     | EUR (€) | INSEE/NIR       |
| `de_DE` | Germany        | German     | EUR (€) | Personalausweis |
| `it_IT` | Italy          | Italian    | EUR (€) | Codice Fiscale  |

Any Faker-supported locale can also be used, but without country-specific generators (ID documents, etc.).

---

## Reproducibility (seed)

Pass `seed` to get **deterministic output** — two instances with the same seed always produce identical data, in any locale and for any generator method (names, emails, IDs, numbers, dates, passwords, etc.).

```python
gen1 = TextDummy("es_ES", seed=42)
gen2 = TextDummy("es_ES", seed=42)

gen1.name()          # "Albano Llopis Hierro"
gen2.name()          # "Albano Llopis Hierro"  ← identical

gen1.id_document()   # "95822412L"
gen2.id_document()   # "95822412L"             ← identical
```

This is essential for:
- **Reproducible tests**: a failing test can be re-run with the exact same data.
- **Deterministic demos**: documentation examples always show the same output.
- **Snapshot testing**: compare generated data across builds.

Without `seed`, each instance uses independent random state (non-deterministic).

---

## Function Categories

| Category               | Methods | Description                                           |
| ---------------------- | ------- | ----------------------------------------------------- |
| Personal Data          | 5       | Names, email, phone                                   |
| Location               | 5       | Address, city, state, postcode, country               |
| Company                | 3       | Company, job, department                              |
| Text                   | 5       | Paragraphs, sentences, words                          |
| ID Documents           | 3       | Country-specific identification                       |
| Financial / Banking    | 12      | Currency, price, IBAN, SWIFT, credit cards, crypto    |
| Dates                  | 2       | Locale-formatted dates and random dates within ranges |
| Random Numbers         | 1       | Locale-aware random numbers with masks and currency   |
| Internet / Technology  | 11      | URLs, IPs, MAC, UUID, passwords, user login           |
| Files                  | 4       | File names, extensions, MIME types, paths             |
| Extra Personal Data    | 7       | DOB, prefix, suffix, SSN, gender, age, full profile   |
| Vehicles               | 1       | License plates                                        |
| Geolocation            | 3       | Latitude, longitude, coordinates                      |
| Colors                 | 3       | Color names, hex, RGB                                 |
| Codes / References     | 4       | ISBN, EAN barcodes                                    |
| Products / Commerce    | 11      | Products, SKUs, reviews, orders, invoices             |
| Unique Keys            | 2       | Guaranteed-unique random keys with reset              |
| Autoincrement          | 2       | Sequential counters with prefix/zfill/reset           |
| Random Selection       | 3       | Random pick from user-provided lists                  |
| Custom Generators     | 4       | Register and run your own generators                  |
| Locale Information     | 2       | Locale metadata and supported locales                 |
| Pydantic Model Filling | 4       | fill_model, DummyField, batch, records/columns        |
| Batch Generation       | 1       | Generate N values of any type at once                 |

---

## Function Index

| Function                                                   | Category       | Description                    |
| ---------------------------------------------------------- | -------------- | ------------------------------ |
| [`name()`](#name)                                           | Personal       | Full name                      |
| [`first_name()`](#first_name)                               | Personal       | First name                     |
| [`last_name()`](#last_name)                                 | Personal       | Last name                      |
| [`email()`](#email)                                         | Personal       | Email address                  |
| [`phone()`](#phone)                                         | Personal       | Phone number                   |
| [`address()`](#address)                                     | Location       | Full address                   |
| [`city()`](#city)                                           | Location       | City name                      |
| [`state()`](#state)                                         | Location       | State / province               |
| [`postcode()`](#postcode)                                   | Location       | Postal code                    |
| [`country()`](#country)                                     | Location       | Country name                   |
| [`company()`](#company)                                     | Company        | Company name                   |
| [`job()`](#job)                                             | Company        | Job title                      |
| [`department()`](#department)                               | Company        | Department name                |
| [`text()`](#text-1)                                         | Text           | Free-form text                 |
| [`paragraph()`](#paragraph)                                 | Text           | Paragraph                      |
| [`sentence()`](#sentence)                                   | Text           | Sentence                       |
| [`word()`](#word)                                           | Text           | Single word                    |
| [`words()`](#words)                                         | Text           | Multiple words                 |
| [`id_document()`](#id_document)                             | ID Docs        | Primary / extra ID             |
| [`dni()`](#dni)                                             | ID Docs        | Primary ID (alias)             |
| [`available_documents()`](#available_documents)             | ID Docs        | List available doc types       |
| [`currency_code()`](#currency_code)                         | Financial      | Currency ISO code              |
| [`currency_symbol()`](#currency_symbol)                     | Financial      | Currency symbol                |
| [`price()`](#price)                                         | Financial      | Formatted price                |
| [`iban()`](#iban)                                           | Financial      | IBAN                           |
| [`bban()`](#bban)                                           | Financial      | BBAN                           |
| [`swift()`](#swift)                                         | Financial      | SWIFT/BIC                      |
| [`credit_card_number()`](#credit_card_number)               | Financial      | Card number                    |
| [`credit_card_expire()`](#credit_card_expire)               | Financial      | Card expiry                    |
| [`credit_card_provider()`](#credit_card_provider)           | Financial      | Card provider                  |
| [`credit_card_security_code()`](#credit_card_security_code) | Financial      | CVV/CVC                        |
| [`credit_card_full()`](#credit_card_full)                   | Financial      | Full card details              |
| [`cryptocurrency_code()`](#cryptocurrency_code)             | Financial      | Crypto code                    |
| [`cryptocurrency_name()`](#cryptocurrency_name)             | Financial      | Crypto name                    |
| [`date()`](#date)                                           | Dates          | Locale-formatted date          |
| [`random_date()`](#random_date)                             | Dates          | Random date within range       |
| [`random_number()`](#random_number)                         | Random Numbers | Locale-formatted random number |
| [`url()`](#url)                                             | Internet       | URL                            |
| [`domain_name()`](#domain_name)                             | Internet       | Domain name                    |
| [`username()`](#username)                                   | Internet       | Username                       |
| [`userlogin()`](#userlogin)                                 | Internet       | User login                     |
| [`password()`](#password)                                   | Internet       | Password (configurable)        |
| [`ipv4()`](#ipv4)                                           | Internet       | IPv4 address                   |
| [`ipv6()`](#ipv6)                                           | Internet       | IPv6 address                   |
| [`mac_address()`](#mac_address)                             | Internet       | MAC address                    |
| [`user_agent()`](#user_agent)                               | Internet       | Browser user agent             |
| [`slug()`](#slug)                                           | Internet       | URL slug                       |
| [`uuid4()`](#uuid4)                                         | Internet       | UUID v4                        |
| [`file_name()`](#file_name)                                 | Files          | File name                      |
| [`file_extension()`](#file_extension)                       | Files          | File extension                 |
| [`mime_type()`](#mime_type)                                 | Files          | MIME type                      |
| [`file_path()`](#file_path)                                 | Files          | File path                      |
| [`date_of_birth()`](#date_of_birth)                         | Personal Extra | Date of birth                  |
| [`prefix()`](#prefix)                                       | Personal Extra | Name prefix                    |
| [`suffix()`](#suffix)                                       | Personal Extra | Name suffix                    |
| [`ssn()`](#ssn)                                             | Personal Extra | SSN / tax ID                   |
| [`gender()`](#gender)                                       | Personal Extra | Gender (locale language)       |
| [`age()`](#age)                                             | Personal Extra | Random age                     |
| [`profile_data()`](#profile_data)                           | Personal Extra | Full profile dict              |
| [`license_plate()`](#license_plate)                         | Vehicles       | License plate                  |
| [`latitude()`](#latitude)                                   | Geolocation    | Latitude                       |
| [`longitude()`](#longitude)                                 | Geolocation    | Longitude                      |
| [`coordinate()`](#coordinate)                               | Geolocation    | Lat/lon pair                   |
| [`color_name()`](#color_name)                               | Colors         | Color name                     |
| [`hex_color()`](#hex_color)                                 | Colors         | Hex color                      |
| [`rgb_color()`](#rgb_color)                                 | Colors         | RGB color                      |
| [`isbn10()`](#isbn10)                                       | Codes          | ISBN-10                        |
| [`isbn13()`](#isbn13)                                       | Codes          | ISBN-13                        |
| [`ean13()`](#ean13)                                         | Codes          | EAN-13                         |
| [`ean8()`](#ean8)                                           | Codes          | EAN-8                          |
| [`product_name()`](#product_name)                           | Commerce       | Product name                   |
| [`product_category()`](#product_category)                   | Commerce       | Product category               |
| [`product_material()`](#product_material)                   | Commerce       | Product material               |
| [`product_sku()`](#product_sku)                             | Commerce       | Product SKU                    |
| [`product_review()`](#product_review)                       | Commerce       | Product review                 |
| [`product_full()`](#product_full)                           | Commerce       | Full product dict              |
| [`payment_method()`](#payment_method)                       | Commerce       | Payment method                 |
| [`order_status()`](#order_status)                           | Commerce       | Order status                   |
| [`tracking_number()`](#tracking_number)                     | Commerce       | Tracking number                |
| [`invoice_number()`](#invoice_number)                       | Commerce       | Invoice number                 |
| [`unique_key()`](#unique_key)                               | Unique Keys    | Unique random key              |
| [`reset_unique_keys()`](#reset_unique_keys)                 | Unique Keys    | Reset key tracking             |
| [`autoincrement()`](#autoincrement)                         | Autoincrement  | Sequential counter             |
| [`reset_autoincrement()`](#reset_autoincrement)             | Autoincrement  | Reset counter                  |
| [`random_from_list()`](#random_from_list)                   | Random         | Single random pick             |
| [`random_sample_from_list()`](#random_sample_from_list)     | Random         | Multiple random picks          |
| [`weighted_random_from_list()`](#weighted_random_from_list) | Random         | Weighted random pick           |
| [`register_custom()`](#register_custom)                     | Custom         | Register generator             |
| [`unregister_custom()`](#unregister_custom)                 | Custom         | Remove generator               |
| [`run_custom()`](#run_custom)                               | Custom         | Generate custom value          |
| [`list_custom()`](#list_custom)                             | Custom         | List registered generators     |
| [`locale_info()`](#locale_info)                             | Locale         | Current locale info            |
| [`supported_locales()`](#supported_locales)                 | Locale         | All locales                    |
| [`fill_model()`](#fill_model)                               | Pydantic       | Fill model with fake data      |
| [`fill_model_batch()`](#fill_model_batch)                   | Pydantic       | Multiple model instances       |
| [`to_records()`](#to_records)                               | Pydantic       | List of dicts (row format)     |
| [`to_columns()`](#to_columns)                               | Pydantic       | Dict of lists (column format)  |
| [`generate_batch()`](#generate_batch)                       | Batch          | Batch generation               |

---

## Detailed Reference

### Personal Data

| Function         | Description   | Example                        |
| ---------------- | ------------- | ------------------------------ |
| `name()`       | Full name     | `"María García López"`    |
| `first_name()` | First name    | `"Carlos"`                   |
| `last_name()`  | Last name     | `"Fernández"`               |
| `email()`      | Email address | `"maria.garcia@example.com"` |
| `phone()`      | Phone number  | `"+34 612 345 678"`          |

---

### Location

| Function       | Description                           | Example                            |
| -------------- | ------------------------------------- | ---------------------------------- |
| `address()`  | Full address (locale-aware)           | `"Calle Mayor 15, 28013 Madrid"` |
| `city()`     | City name                             | `"Barcelona"`                    |
| `state()`    | State / province (falls back to city) | `"Andalucía"`                   |
| `postcode()` | Postal code                           | `"28013"`                        |
| `country()`  | Country name                          | `"España"`                      |

---

### Company

| Function         | Description              | Example                       |
| ---------------- | ------------------------ | ----------------------------- |
| `company()`    | Company name             | `"Industrias García S.L."` |
| `job()`        | Job title                | `"Software Engineer"`       |
| `department()` | Department (15 built-in) | `"Technology"`              |

---

### Text

| Function       | Description     | Example                              |
| -------------- | --------------- | ------------------------------------ |
| `sentence()` | Single sentence | `"A randomly generated sentence."` |
| `word()`     | Single word     | `"casa"`                           |

#### `text(max_nb_chars=200)`

Generate free-form text. Returns `str`.

```python
gen.text(100)  # "Lorem ipsum dolor sit amet..."
```

#### `paragraph(nb_sentences=3)`

Generate a paragraph. Returns `str`.

```python
gen.paragraph(2)  # "Two sentences here. And here."
```

#### `words(nb=5)`

Generate a list of words. Returns `List[str]`.

```python
gen.words(3)  # ["casa", "perro", "sol"]
```

---

### ID Documents

#### `id_document(doc_type=None)`

Generate a country-specific fake ID. Returns `str`. Raises `ValueError` if locale has no profile.

```python
gen_es = TextDummy("es_ES")
gen_es.id_document()          # "45678123P"   (DNI/NIF)
gen_es.id_document("NIE")     # "X1234567L"

gen_us = TextDummy("en_US")
gen_us.id_document()          # "456-78-1234" (SSN)
gen_us.id_document("EIN")     # "12-3456789"

gen_br = TextDummy("pt_BR")
gen_br.id_document()          # "123.456.789-09" (CPF)
gen_br.id_document("CNPJ")    # "12.345.678/0001-95"
```

| Function                  | Description                               | Example                |
| ------------------------- | ----------------------------------------- | ---------------------- |
| `dni()`                 | Alias for `id_document()` (primary ID)  | `"45678123P"`        |
| `available_documents()` | List doc types for locale →`List[str]` | `["DNI/NIF", "NIE"]` |

---

### Financial / Banking

| Function                        | Description                   | Example                        |
| ------------------------------- | ----------------------------- | ------------------------------ |
| `currency_code()`             | ISO currency code             | `"EUR"`                      |
| `currency_symbol()`           | Currency symbol               | `"€"`                       |
| `iban()`                      | IBAN                          | `"ES9121000418450200051332"` |
| `bban()`                      | BBAN                          | `"21000418450200051332"`     |
| `swift()`                     | SWIFT/BIC code                | `"CAIXESBBXXX"`              |
| `credit_card_number()`        | Card number                   | `"4111111111111111"`         |
| `credit_card_expire()`        | Card expiry                   | `"12/26"`                    |
| `credit_card_provider()`      | Card provider                 | `"Visa"`                     |
| `credit_card_security_code()` | CVV/CVC                       | `"123"`                      |
| `credit_card_full()`          | Full card details (multiline) | `"Visa\nJohn Doe\n4111..."`  |
| `cryptocurrency_code()`       | Crypto code                   | `"BTC"`                      |
| `cryptocurrency_name()`       | Crypto name                   | `"Bitcoin"`                  |

#### `price(min_val=1.0, max_val=1000.0, decimals=2)`

Generate formatted price with locale currency. Returns `str`.

```python
gen.price()               # "€347.52"
gen.price(10, 50, 0)      # "€35"
```

---

### Dates

#### `date(pattern=None)`

Locale-formatted date. Returns `str`.

```python
gen_es = TextDummy("es_ES")
gen_es.date()               # "15/03/2023"  (dd/mm/yyyy)
gen_us = TextDummy("en_US")
gen_us.date()               # "03/15/2023"  (mm/dd/yyyy)
gen_es.date("%Y-%m-%d")     # "2023-03-15"  (custom override)
```

#### `random_date(start=None, end=None, pattern=None, mask=None)`

Random date within a range with locale-aware formatting. Returns `str`.

- `start` / `end`: `"YYYY-MM-DD"` (defaults: `"1970-01-01"` / today)
- `mask`: output template with `{date}`, `{year}`, `{month}`, `{day}`, `{quarter}` tokens

```python
gen.random_date()                                    # "15/03/1998"
gen.random_date("2020-01-01", "2025-12-31")          # "22/07/2023"
gen.random_date(mask="FEC-{year}{month}{day}")       # "FEC-19980315"
gen.random_date("2020-01-01", "2025-12-31",
                mask="Report_{year}-Q{quarter}")     # "Report_2023-Q3"
```

**Aliases**: `random_date`, `fecha`, `fecha_inicio`, `fecha_fin`, `start_date`, `end_date`, `created_at`, `updated_at`.

---

### Internet / Technology

| Function          | Description        | Example                   |
| ----------------- | ------------------ | ------------------------- |
| `url()`         | URL                | `"https://example.com"` |
| `domain_name()` | Domain name        | `"example.com"`         |
| `username()`    | Username           | `"maria_garcia"`        |
| `userlogin()`   | User login         | `"mgarcia"`             |
| `ipv4()`        | IPv4 address       | `"192.168.1.100"`       |
| `ipv6()`        | IPv6 address       | `"2001:0db8:85a3:..."`  |
| `mac_address()` | MAC address        | `"00:1B:44:11:3A:B7"`   |
| `user_agent()`  | Browser User-Agent | `"Mozilla/5.0 ..."`     |
| `slug()`        | URL slug           | `"my-example-page"`     |
| `uuid4()`       | UUID v4            | `"a1b2c3d4-e5f6-..."`   |

#### `password(length=12, upper=True, lower=True, digits=True, special=True)`

Configurable password. Guarantees at least one char from each enabled set. Returns `str`. Raises `ValueError` if all flags are `False`.

```python
gen.password()                                    # "gD)G{>P@?Z]1"
gen.password(length=20)                           # "xK9#mP2$vR4!aB7@cD1%"
gen.password(length=6, upper=False, lower=False,
             special=False)                       # "847251"  (PIN)
```

**Aliases**: `password`, `pwd`, `pass_word`, `contrasena`, `clave_acceso`.

---

### Files

| Function             | Description    | Example                               |
| -------------------- | -------------- | ------------------------------------- |
| `file_name()`      | File name      | `"document.pdf"`                    |
| `file_extension()` | File extension | `"pdf"`                             |
| `mime_type()`      | MIME type      | `"application/pdf"`                 |
| `file_path()`      | File path      | `"/home/user/documents/report.pdf"` |

---

### Extra Personal Data

| Function           | Description                                      | Example                             |
| ------------------ | ------------------------------------------------ | ----------------------------------- |
| `prefix()`       | Name prefix                                      | `"Sr."`                           |
| `suffix()`       | Name suffix                                      | `"Jr."`                           |
| `ssn()`          | SSN / tax ID (falls back to `id_document()`)   | `"45678123P"`                     |
| `profile_data()` | Full profile →`Dict` (name, email, phone, …) | `{"name": "María García", ...}` |

#### `date_of_birth(min_age=18, max_age=80)`

Locale-formatted date of birth. Returns `str`.

```python
gen.date_of_birth()          # "15/03/1985"
gen.date_of_birth(25, 35)    # "22/07/1992"
```

#### `gender(abbreviated=False)`

Random gender label in the locale's language. Returns `str`.

When `abbreviated=True`, returns a short abbreviation (`"M"` / `"F"`, or `"M"` / `"W"` for German).

```python
TextDummy("es_ES").gender()                     # "Femenino"
TextDummy("en_US").gender()                     # "Male"
TextDummy("fr_FR").gender()                     # "Masculin"
TextDummy("es_ES").gender(abbreviated=True)     # "M" or "F"
TextDummy("de_DE").gender(abbreviated=True)     # "M" or "W"
```

**Aliases**: `gender`, `genero`, `sexo`, `sex`.

#### `age(min_val=18, max_val=80)`

Random age. Returns `int`. DummyField: `DummyField("age", min_val=6, max_val=18)`.

```python
gen.age()                       # 42
gen.age(min_val=25, max_val=35) # 29
```

**Aliases**: `age`, `edad`, `years_old`.

---

### Vehicles

| Function            | Description                                 | Example        |
| ------------------- | ------------------------------------------- | -------------- |
| `license_plate()` | Vehicle license plate (native or synthetic) | `"1234 BCD"` |

---

### Geolocation

| Function         | Description  | Example                    |
| ---------------- | ------------ | -------------------------- |
| `latitude()`   | Latitude     | `"40.416775"`            |
| `longitude()`  | Longitude    | `"-3.703790"`            |
| `coordinate()` | Lat/lon pair | `"40.416775, -3.703790"` |

---

### Colors

| Function         | Description | Example              |
| ---------------- | ----------- | -------------------- |
| `color_name()` | Color name  | `"MediumSeaGreen"` |
| `hex_color()`  | Hex color   | `"#3cb371"`        |
| `rgb_color()`  | RGB color   | `"60,179,113"`     |

---

### Codes / References

| Function     | Description    | Example                 |
| ------------ | -------------- | ----------------------- |
| `isbn10()` | ISBN-10        | `"0-306-40615-2"`     |
| `isbn13()` | ISBN-13        | `"978-0-306-40615-7"` |
| `ean13()`  | EAN-13 barcode | `"5901234123457"`     |
| `ean8()`   | EAN-8 barcode  | `"96385074"`          |

---

### Products / Commerce

| Function               | Description                     | Example                |
| ---------------------- | ------------------------------- | ---------------------- |
| `product_name()`     | Adjective + noun                | `"Smart Monitor"`    |
| `product_category()` | Category (20 built-in)          | `"Electronics"`      |
| `product_material()` | Material (20 built-in)          | `"Stainless Steel"`  |
| `product_sku()`      | SKU `ABCD-A3X9-2847`          | `"ELEC-A3X9-2847"`   |
| `payment_method()`   | Payment method (12 built-in)    | `"Credit Card"`      |
| `order_status()`     | Order status (10 built-in)      | `"Shipped"`          |
| `tracking_number()`  | Tracking number (locale suffix) | `"AB123456789012ES"` |
| `invoice_number()`   | Invoice `INV-YYYY-NNNNN`      | `"INV-2025-00342"`   |

#### `product_review()`

Full review → `Dict` with `rating`, `title`, `comment`, `author`, `date`, `verified_purchase`.

```python
gen.product_review()  # {"rating": 4, "title": "Great product overall", ...}
```

#### `product_full()`

Complete product → `Dict` with `name`, `sku`, `category`, `material`, `price`, `ean`, `description`, `brand`, `in_stock`, `stock_qty`, `weight_kg`.

```python
gen.product_full()  # {"name": "Premium Keyboard", "sku": "ELEC-A3X9-2847", ...}
```

---

### Random Numbers

#### `random_number(number_type="integer", digits=6, decimals=2, min_val=None, max_val=None, mask=None, currency=False)`

Locale-aware formatted random number. Returns `str`.

| Parameter                 | Type              | Default       | Description                                          |
| ------------------------- | ----------------- | ------------- | ---------------------------------------------------- |
| `number_type`           | `str`           | `"integer"` | `"integer"` or `"float"`                         |
| `digits`                | `int`           | `6`         | Approximate significant digits                       |
| `decimals`              | `int`           | `2`         | Decimal places (floats)                              |
| `min_val` / `max_val` | `Optional`      | `None`      | Explicit range (overrides digits)                    |
| `mask`                  | `Optional[str]` | `None`      | `#` for digit, `{value}` / `{currency}` tokens |
| `currency`              | `bool`          | `False`     | Add locale currency symbol                           |

```python
gen_es = TextDummy("es_ES")
gen_es.random_number()                                 # "483.291"
gen_es.random_number("float", digits=5, decimals=2)    # "48.329,15"
gen_es.random_number(currency=True)                    # "483.291 €"
gen_es.random_number(mask="REF-{value}")               # "REF-483.291"

gen_us = TextDummy("en_US")
gen_us.random_number("float", decimals=2, currency=True) # "$48,329.15"
```

**Aliases**: `random_number`, `numero`, `number`, `importe`, `amount`, `quantity`, `cantidad`.

---

### Unique Keys

#### `unique_key(length=8, key_type="alphanumeric", prefix="", suffix="", separator="", segment_length=0, uppercase=True, group="_default")`

Guaranteed-unique random key tracked per group. Returns `str`.

| Parameter               | Type     | Default            | Description                                                           |
| ----------------------- | -------- | ------------------ | --------------------------------------------------------------------- |
| `length`              | `int`  | `8`              | Character count                                                       |
| `key_type`            | `str`  | `"alphanumeric"` | `"alphanumeric"`, `"alpha"`, `"numeric"`, `"hex"`, `"uuid"` |
| `prefix` / `suffix` | `str`  | `""`             | Fixed string prepended/appended                                       |
| `separator`           | `str`  | `""`             | Segment separator                                                     |
| `segment_length`      | `int`  | `0`              | Chars per segment                                                     |
| `uppercase`           | `bool` | `True`           | Force uppercase (except UUID)                                         |
| `group`               | `str`  | `"_default"`     | Uniqueness namespace                                                  |

```python
gen.unique_key()                                        # "K4M9X2B7"
gen.unique_key(prefix="USR-", length=6)                 # "USR-T3N8Q1"
gen.unique_key(key_type="hex", length=12,
               separator="-", segment_length=4)         # "A3F1-7B2E-9C04"
gen.unique_key(key_type="uuid")                         # "f47ac10b-58cc-..."
```

**Aliases**: `unique_key`, `key`, `clave`, `clave_unica`, `unique_id`, `codigo`, `code`, `token`, `ref`, `reference`, `referencia`.
DummyField: `DummyField("unique_key", prefix="ORD-", length=8, key_type="hex")`.

#### `reset_unique_keys(group=None)`

Clear tracked keys. `None` resets all groups.

---

### Autoincrement

#### `autoincrement(start=1, step=1, prefix="", suffix="", zfill=0, group="_default")`

Sequential counter per group. Returns `str`.

| Parameter               | Type    | Default        | Description                     |
| ----------------------- | ------- | -------------- | ------------------------------- |
| `start`               | `int` | `1`          | Initial value                   |
| `step`                | `int` | `1`          | Increment per call              |
| `prefix` / `suffix` | `str` | `""`         | Fixed string prepended/appended |
| `zfill`               | `int` | `0`          | Zero-pad width                  |
| `group`               | `str` | `"_default"` | Counter namespace               |

```python
gen.autoincrement()                                 # "1"
gen.autoincrement()                                 # "2"
gen.autoincrement(prefix="EMP-", zfill=5)           # "EMP-00003"
gen.autoincrement(start=1000, step=10, group="inv") # "1000"
gen.autoincrement(group="inv")                      # "1010"
```

**Aliases**: `autoincrement`, `id`, `consecutivo`, `secuencia`, `sequence`, `seq`, `counter`, `contador`, `row_id`, `row_number`, `numero_fila`.
DummyField: `DummyField("autoincrement", start=1000, prefix="EMP-", zfill=5)`.

#### `reset_autoincrement(group=None)`

Reset counters. `None` resets all groups.

---

### Random Selection from Lists

Static methods — callable without an instance.

#### `random_from_list(values)`

Single random element. Returns `Any`. Raises `ValueError` if empty.

```python
TextDummy.random_from_list(["red", "green", "blue"])  # "green"
```

#### `random_sample_from_list(values, count=1, allow_duplicates=True)`

Multiple random elements. Returns `List[Any]`.

```python
TextDummy.random_sample_from_list(["A", "B", "C", "D"], count=3)                        # ["B", "A", "D"]
TextDummy.random_sample_from_list(["A", "B", "C"], count=2, allow_duplicates=False)      # ["C", "A"]
```

#### `weighted_random_from_list(values, weights)`

Weighted random element. Returns `Any`.

```python
TextDummy.weighted_random_from_list(["common", "uncommon", "rare"], [0.7, 0.25, 0.05])   # "common"
```

---

### Custom Generators

#### `register_custom(name, source)`

Register a custom generator. `source`: list of values or a callable.

```python
gen.register_custom("priority", ["Low", "Medium", "High", "Critical"])
gen.register_custom("order_code", lambda: f"ORD-{random.randint(10000,99999)}")
```

| Function                  | Description                           | Returns            |
| ------------------------- | ------------------------------------- | ------------------ |
| `unregister_custom(name)` | Remove a registered generator         | —                 |
| `run_custom(name)`        | Generate value from registered source | `Any`            |
| `list_custom()`           | List registered generators            | `Dict[str, str]` |

```python
gen.run_custom("priority")  # "High"
gen.list_custom()           # {"priority": "list[4]", "order_code": "callable"}
```

---

### Locale Information

#### `locale_info()`

Locale metadata → `Dict` with `locale`, `country`, `language`, `currency`, `phone_prefix`, `date_format`, `id_document`, `extra_documents`, `has_state_province`.

```python
gen.locale_info()
# {"locale": "es_ES", "country": "Spain", "language": "Spanish", "currency": "EUR (€)", ...}
```

#### `supported_locales()` *(static)*

All locale codes with country names → `Dict[str, str]`.

```python
TextDummy.supported_locales()  # {"es_ES": "Spain", "es_MX": "Mexico", ...}
```

---

### Batch Generation

#### `generate_batch(data_type, count=10)`

Generate multiple values of any built-in or custom type. Returns `List[str]`.

```python
gen.generate_batch("email", count=5)         # ["ana@example.com", ...]
gen.generate_batch("product_name", count=3)  # ["Smart Monitor", "Eco Bottle", ...]
```

Supports all method names plus registered custom types.

---

### Pydantic Model Filling

#### `DummyField(generator, **kwargs)`

Annotation marker for explicit field→generator mapping. Use with `Annotated`.

```python
class Employee(BaseModel):
    codigo: Annotated[str, DummyField("uuid4")]
    ref: Annotated[str, DummyField("unique_key", prefix="ORD-", length=8)]
```

#### `fill_model(model_class, overrides=None)`

Fill a Pydantic BaseModel with fake data. Returns model instance.

**Resolution order**: overrides → `DummyField` → field name (~120 aliases) → type fallback.
Supports: nested models, `Optional[X]`, `List[X]`, `Enum`, `Decimal`, `datetime`, `date`, `bytes`.

```python
user = gen.fill_model(User)
user = gen.fill_model(User, overrides={"active": True, "age": 30})
user = gen.fill_model(User, overrides={"age": lambda: 25})
```

#### `fill_model_batch(model_class, count=10, overrides=None)`

Multiple model instances. Returns `list`.

---

### Records & Columns

#### `to_records(model_class, count=1000, overrides=None)`

List of dicts (one per row). Returns `List[Dict[str, Any]]`.

```python
rows = gen.to_records(User, count=5)
# [{"name": "María García", "email": "maria@example.com", "age": 34}, ...]
```

#### `to_columns(model_class, count=1000, overrides=None)`

Dict of lists (one per field). Returns `Dict[str, list]`. Ideal for DataFrames.

```python
cols = gen.to_columns(User, count=1000)
import pandas as pd
df = pd.DataFrame(gen.to_columns(User, count=1000))
```

---

## TextDummy vs Faker

TextDummy wraps [Faker](https://faker.readthedocs.io/) for basic generators and adds a layer of exclusive features on top.

### What Faker provides (wrapped by TextDummy)

Basic fake data generators available in Faker that TextDummy exposes with the same API:

| Category  | Functions                                                                                                                       |
| --------- | ------------------------------------------------------------------------------------------------------------------------------- |
| Personal  | `name`, `first_name`, `last_name`, `email`, `phone`, `prefix`, `suffix`, `ssn`                                  |
| Location  | `address`, `city`, `state`, `postcode`, `country`, `latitude`, `longitude`                                        |
| Company   | `company`, `job`                                                                                                            |
| Text      | `text`, `paragraph`, `sentence`, `word`, `words`                                                                      |
| Financial | `currency_code`, `currency_symbol`, `iban`, `bban`, `swift`, `credit_card_*`, `cryptocurrency_*`                  |
| Internet  | `url`, `domain_name`, `username`, `ipv4`, `ipv6`, `mac_address`, `user_agent`, `slug`, `uuid4`                |
| Files     | `file_name`, `file_extension`, `mime_type`, `file_path`                                                                 |
| Other     | `date_of_birth`, `license_plate`, `color_name`, `hex_color`, `rgb_color`, `isbn10`, `isbn13`, `ean13`, `ean8` |

### TextDummy exclusive features

Features built by TextDummy that are **not available in Faker**:

| Feature                         | Description                                                                                                  |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **12 locale profiles**    | Deep config per country: date format, currency, phone prefix, ID documents                                   |
| **ID documents**          | Country-specific: DNI/NIF, NIE, SSN, EIN, CPF, CNPJ, CURP, RFC, RUT, NINO, etc.                              |
| **Locale-aware dates**    | `date()` respects locale format (dd/mm/yyyy vs mm/dd/yyyy)                                                 |
| **Random dates**          | `random_date()` with range, pattern, mask tokens (`{year}`, `{quarter}`, …)                           |
| **Random numbers**        | `random_number()` with locale separators, currency symbols, masks                                          |
| **Enhanced password**     | Configurable character sets (upper/lower/digits/special) with guarantees                                     |
| **Gender labels**         | `gender()` in locale language (Masculino, Male, Männlich…) with optional `abbreviated=True` (M/F, M/W)   |
| **Age**                   | `age()` with configurable min/max range                                                                    |
| **Price formatting**      | `price()` with locale currency symbol                                                                      |
| **Department**            | `department()` from 15 built-in departments                                                                |
| **User login**            | `userlogin()` realistic login generation                                                                   |
| **Profile data**          | `profile_data()` structured dict with 13 fields                                                            |
| **Products / Commerce**   | 11 generators: name, SKU, category, material, review, full product, payment, order status, tracking, invoice |
| **Unique keys**           | `unique_key()` with 5 key types, segments, groups, uniqueness guarantee                                    |
| **Autoincrement**         | `autoincrement()` sequential counters with prefix/zfill/step/groups                                        |
| **Random from lists**     | `random_from_list`, `random_sample_from_list`, `weighted_random_from_list`                             |
| **Custom generators**     | `register_custom` with list-backed or callable sources                                                     |
| **Pydantic integration**  | `fill_model`, `DummyField`, ~120 field-name aliases (EN + ES)                                            |
| **Records / Columns**     | `to_records`, `to_columns` (DataFrame-ready output)                                                      |
| **Batch generation**      | `generate_batch` for any type                                                                              |
| **Instance caching**      | `get_generator()` auto-caches per locale                                                                   |
| **Convenience functions** | 30+`fake_*()` module-level shortcuts                                                                       |

---

## Convenience Functions

Module-level shortcuts that create/cache `TextDummy` instances internally.
Functions marked with **✦** are **TextDummy exclusives** — not available in Faker.

### Faker-wrapped generators

| TextDummy Method                   | Convenience Shortcut             |
| ---------------------------------- | -------------------------------- |
| `TextDummy.name()`               | `fake_name(locale)`            |
| `TextDummy.email()`              | `fake_email(locale)`           |
| `TextDummy.phone()`              | `fake_phone(locale)`           |
| `TextDummy.address()`            | `fake_address(locale)`         |
| `TextDummy.text(max_chars)`      | `fake_text(max_chars, locale)` |
| `TextDummy.credit_card_number()` | `fake_credit_card(locale)`     |
| `TextDummy.iban()`               | `fake_iban(locale)`            |
| `TextDummy.swift()`              | `fake_swift(locale)`           |
| `TextDummy.ipv4()`               | `fake_ipv4(locale)`            |
| `TextDummy.license_plate()`      | `fake_license_plate(locale)`   |
| `TextDummy.date_of_birth()`      | `fake_date_of_birth(locale)`   |

### TextDummy exclusive generators ✦

| TextDummy Method                               | Convenience Shortcut                                    |
| ---------------------------------------------- | ------------------------------------------------------- |
| `TextDummy.id_document(doc_type)`            | `fake_id_document(locale, doc_type)`                  |
| `TextDummy.dni()`                            | `fake_dni(locale)`                                    |
| `TextDummy.userlogin()`                      | `fake_userlogin(locale)`                              |
| `TextDummy.password(length, upper, …)`      | `fake_password(length, upper, …, locale)`            |
| `TextDummy.gender()`                         | `fake_gender(locale)`                                 |
| `TextDummy.age(min_val, max_val)`            | `fake_age(min_val, max_val, locale)`                  |
| `TextDummy.random_number(…)`                | `fake_random_number(number_type, digits, …, locale)` |
| `TextDummy.random_date(start, end, …)`      | `fake_random_date(start, end, pattern, mask, locale)` |
| `TextDummy.unique_key(length, key_type, …)` | `fake_unique_key(length, key_type, …, locale)`       |
| `TextDummy.autoincrement(start, step, …)`   | `fake_autoincrement(start, step, …, locale)`         |
| `TextDummy.profile_data()`                   | `fake_profile(locale)`                                |
| `TextDummy.product_full()`                   | `fake_product(locale)`                                |
| `TextDummy.product_name()`                   | `fake_product_name(locale)`                           |

### Batch & random selection ✦

| TextDummy Method                                  | Convenience Shortcut                                         |
| ------------------------------------------------- | ------------------------------------------------------------ |
| `TextDummy.generate_batch(data_type, count)`    | `fake_batch(data_type, count, locale)`                     |
| `TextDummy.random_from_list(values)`            | `random_from_list(values)`                                 |
| `TextDummy.random_sample_from_list(values, …)` | `random_sample_from_list(values, count, allow_duplicates)` |

> `random_from_list` and `random_sample_from_list` are **static methods** — they also work as `TextDummy.random_from_list(…)` without an instance.

### Pydantic / bulk output ✦

| TextDummy Method                                 | Convenience Shortcut                                        |
| ------------------------------------------------ | ----------------------------------------------------------- |
| `TextDummy.fill_model(model, overrides)`       | `fake_model(model_class, locale, overrides)`              |
| `TextDummy.fill_model_batch(model, count, …)` | `fake_model_batch(model_class, count, locale, overrides)` |
| `TextDummy.to_records(model, count, …)`       | `fake_records(model_class, count, locale, overrides)`     |
| `TextDummy.to_columns(model, count, …)`       | `fake_columns(model_class, count, locale, overrides)`     |

```python
from shadetriptxt.text_dummy.text_dummy import fake_name, fake_email, fake_batch

fake_name("en_US")              # "John Smith"
fake_email("pt_BR")             # "joao@example.com.br"
fake_batch("phone", 5, "es_MX") # ["+52 55 1234 5678", ...]
```

---

## Instance Caching

Use `get_generator(locale)` to reuse cached instances across calls:

```python
from shadetriptxt.text_dummy.text_dummy import get_generator

gen = get_generator("es_ES")  # Creates once, reuses on subsequent calls
gen.name()
gen.email()
```

All convenience functions (`fake_name`, `fake_email`, etc.) use `get_generator()` internally, so instances are automatically cached per locale.

---

## Examples

Complete runnable examples are available in `shadetriptxt/text_dummy/examples/`, organized by category matching the sections above:

| File | Description |
|------|-------------|
| `personal_data.py` | Name, email, phone, DOB, gender, age, password, profile |
| `location_company_text.py` | Address, city, company, job, words, sentences |
| `id_documents.py` | DNI, SSN, CPF, CURP, RUT, NINO… (12 locales) |
| `financial_banking.py` | Currency, price, IBAN, SWIFT, credit cards, crypto |
| `dates_numbers.py` | Locale-aware dates, random ranges, masks, numbers |
| `internet_files.py` | URLs, IPs, MAC, UUID, passwords, file names |
| `vehicles_geo_colors_codes.py` | License plates, coordinates, colors, ISBN/EAN |
| `products_commerce.py` | Products, SKU, reviews, orders, payments, invoices |
| `unique_keys_autoincrement.py` | Unique keys, autoincrement, groups, Pydantic |
| `custom_types_random.py` | Custom types, random/weighted selection from lists |
| `pydantic_models.py` | fill_model, DummyField, overrides, Records & Columns |
| `locales.py` | Locale info, side-by-side comparison (12 locales) |
| `batch_convenience.py` | Batch generation, all `fake_*()` convenience functions |

---

## Related Documentation

| Document | Description |
|----------|-------------|
| [TextParser](../text_parser/README.md) | Text extraction, normalization, and ID validation (shares locale profiles) |
| [TextAnonymizer](../text_anonymizer/README_TextAnonymizer.md) | PII detection and anonymization |
| [TextMatcher](../text_matcher/README.md) | Fuzzy text comparison and deduplication |
