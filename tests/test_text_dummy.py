"""Tests for shadetriptxt.text_dummy — TextDummy fake data generation."""

from shadetriptxt.text_dummy.text_dummy import TextDummy, fake_batch


class TestTextDummyInit:
    def test_default_locale(self):
        gen = TextDummy()
        assert gen is not None

    def test_custom_locale(self):
        gen = TextDummy(locale="en_US")
        assert gen is not None

    def test_seed_reproducibility(self):
        gen1 = TextDummy(locale="es_ES", seed=42)
        gen2 = TextDummy(locale="es_ES", seed=42)
        assert gen1.name() == gen2.name()


class TestTextDummyPersonal:
    def test_name(self):
        gen = TextDummy(locale="es_ES", seed=1)
        name = gen.name()
        assert isinstance(name, str)
        assert len(name) > 0

    def test_email(self):
        gen = TextDummy(locale="es_ES", seed=1)
        email = gen.email()
        assert isinstance(email, str)
        assert "@" in email

    def test_phone(self):
        gen = TextDummy(locale="es_ES", seed=1)
        phone = gen.phone()
        assert isinstance(phone, str)
        assert len(phone) > 0

    def test_address(self):
        gen = TextDummy(locale="es_ES", seed=1)
        addr = gen.address()
        assert isinstance(addr, str)


class TestTextDummyFinancial:
    def test_iban(self):
        gen = TextDummy(locale="es_ES", seed=1)
        iban = gen.iban()
        assert isinstance(iban, str)
        assert len(iban) > 10

    def test_credit_card(self):
        gen = TextDummy(locale="es_ES", seed=1)
        cc = gen.credit_card_number()
        assert isinstance(cc, str)


class TestTextDummyBatch:
    def test_batch_generation(self):
        batch = fake_batch("name", count=5, locale="es_ES")
        assert isinstance(batch, list)
        assert len(batch) == 5
        assert all(isinstance(v, str) for v in batch)

    def test_batch_zero(self):
        batch = fake_batch("name", count=0, locale="es_ES")
        assert batch == []
