"""
Pydantic Models
=================
Automatic Pydantic model filling with fake data: fill_model,
DummyField annotations, overrides (values, callables, generator
names), nested/Optional/List/Enum models, batch generation,
and to_records / to_columns output formats.

README sections: Pydantic Model Filling, Records & Columns

Requires: pip install pydantic
"""

from enum import Enum
from typing import Annotated, List, Optional
from pydantic import BaseModel
from shadetriptxt.text_dummy.text_dummy import TextDummy, DummyField

gen = TextDummy("es_ES")


# ══════════════════════════════════════════════════════════════
#  FILL_MODEL
# ══════════════════════════════════════════════════════════════

# ── 1. Simple model ──────────────────────────────────────────
class User(BaseModel):
    name: str
    email: str
    phone: str
    age: int
    active: bool

print("=== 1. Simple Model ===")
user = gen.fill_model(User)
print(f"  name={user.name}, email={user.email}, age={user.age}")


# ── 2. Nested model ──────────────────────────────────────────
class Address(BaseModel):
    street: str
    city: str
    postcode: str
    country: str

class Customer(BaseModel):
    name: str
    email: str
    address: Address

print("\n=== 2. Nested Model ===")
customer = gen.fill_model(Customer)
print(f"  name:    {customer.name}")
print(f"  email:   {customer.email}")
print(f"  address: {customer.address.city}, {customer.address.country}")


# ── 3. Optional and List fields ──────────────────────────────
class Article(BaseModel):
    title: str
    description: Optional[str] = None
    tags: List[str]

print("\n=== 3. Optional + List ===")
article = gen.fill_model(Article)
print(f"  title:       {article.title}")
print(f"  description: {article.description}")
print(f"  tags:        {article.tags}")


# ── 4. Enum fields ───────────────────────────────────────────
class Status(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"

class Account(BaseModel):
    username: str
    email: str
    status: Status

print("\n=== 4. Enum ===")
account = gen.fill_model(Account)
print(f"  username: {account.username}")
print(f"  status:   {account.status}")


# ── 5. Overrides: fixed value, callable, generator name ──────
import random

print("\n=== 5. Overrides (fixed value) ===")
user_fixed = gen.fill_model(User, overrides={"active": True, "age": 30})
print(f"  active={user_fixed.active}, age={user_fixed.age}")

print("\n=== 6. Overrides (callable) ===")
user_fn = gen.fill_model(User, overrides={
    "age": lambda: random.randint(18, 25),
    "active": lambda: True,
})
print(f"  age={user_fn.age} (18-25), active={user_fn.active}")

class Record(BaseModel):
    code: str
    ref: str
    status: str

print("\n=== 7. Overrides (generator name) ===")
rec = gen.fill_model(Record, overrides={
    "code": "uuid4",
    "ref": "iban",
    "status": "order_status",
})
print(f"  code:   {rec.code}")
print(f"  ref:    {rec.ref}")
print(f"  status: {rec.status}")


# ══════════════════════════════════════════════════════════════
#  DUMMYFIELD ANNOTATIONS
# ══════════════════════════════════════════════════════════════

# ── Basic mapping ─────────────────────────────────────────────
class Employee(BaseModel):
    codigo: Annotated[str, DummyField("uuid4")]
    referencia: Annotated[str, DummyField("product_sku")]
    contacto: Annotated[str, DummyField("email")]
    responsable: Annotated[str, DummyField("name")]

print("\n=== 8. DummyField — basic mapping ===")
emp = gen.fill_model(Employee)
print(f"  codigo:      {emp.codigo}")
print(f"  referencia:  {emp.referencia}")
print(f"  contacto:    {emp.contacto}")
print(f"  responsable: {emp.responsable}")


# ── DummyField with kwargs ────────────────────────────────────
class PersonWithAge(BaseModel):
    nombre: Annotated[str, DummyField("name")]
    nacimiento: Annotated[str, DummyField("date_of_birth", min_age=18, max_age=30)]
    clave: Annotated[str, DummyField("password", length=20)]

print("\n=== 9. DummyField — with kwargs ===")
person = gen.fill_model(PersonWithAge)
print(f"  nombre:     {person.nombre}")
print(f"  nacimiento: {person.nacimiento}")
print(f"  clave:      {person.clave}")


# ── Mixed: auto-detect + DummyField ──────────────────────────
class Order(BaseModel):
    name: str          # auto-detected
    email: str         # auto-detected
    city: str          # auto-detected
    referencia_pedido: Annotated[str, DummyField("tracking_number")]
    numero_factura: Annotated[str, DummyField("invoice_number")]
    importe: Annotated[str, DummyField("price", min_val=50, max_val=500)]

print("\n=== 10. Mixed auto-detect + DummyField ===")
order = gen.fill_model(Order)
print(f"  name:              {order.name}")
print(f"  email:             {order.email}")
print(f"  referencia_pedido: {order.referencia_pedido}")
print(f"  numero_factura:    {order.numero_factura}")
print(f"  importe:           {order.importe}")


# ══════════════════════════════════════════════════════════════
#  BATCH, RECORDS & COLUMNS
# ══════════════════════════════════════════════════════════════

# ── fill_model_batch ──────────────────────────────────────────
print("\n=== 11. fill_model_batch ===")
users = gen.fill_model_batch(User, count=5)
for u in users:
    print(f"  {u.name:25s} {u.email:30s} age={u.age}")


# ── to_records (list of dicts) ────────────────────────────────
print("\n=== 12. to_records (5 rows) ===")
records = gen.to_records(User, count=5)
for i, row in enumerate(records):
    print(f"  [{i}] {row}")


# ── to_columns (dict of lists) ───────────────────────────────
print("\n=== 13. to_columns (5 rows) ===")
columns = gen.to_columns(User, count=5)
for field_name, values in columns.items():
    print(f"  {field_name}: {values}")


# ── With overrides ────────────────────────────────────────────
print("\n=== 14. to_records with overrides ===")
records_ov = gen.to_records(User, count=3, overrides={
    "age": lambda: 25,
    "active": True,
})
for row in records_ov:
    print(f"  {row}")


# ── to_columns → pandas DataFrame ────────────────────────────
print("\n=== 15. to_columns → DataFrame ===")
try:
    import pandas as pd
    cols = gen.to_columns(User, count=10)
    df = pd.DataFrame(cols)
    print(df.to_string(index=False))
except ImportError:
    print("  (pandas not installed — skipping)")
    print("  Usage: pd.DataFrame(gen.to_columns(User, count=1000))")
