"""
Internet / Technology & Files
==============================
URLs, domains, usernames, logins, passwords, IPs, MAC, UUID,
User-Agent, slugs, and file generators.

README sections: Internet / Technology, Files
"""

from shadetriptxt.text_dummy.text_dummy import TextDummy

gen = TextDummy("es_ES")

# ── Internet / Technology ─────────────────────────────────────
print("=== Internet / Technology ===")
print(f"  URL:         {gen.url()}")
print(f"  Domain:      {gen.domain_name()}")
print(f"  Username:    {gen.username()}")
print(f"  User login:  {gen.userlogin()}")
print(f"  Password:    {gen.password()}")
print(f"  IPv4:        {gen.ipv4()}")
print(f"  IPv6:        {gen.ipv6()}")
print(f"  MAC:         {gen.mac_address()}")
print(f"  User-Agent:  {gen.user_agent()}")
print(f"  Slug:        {gen.slug()}")
print(f"  UUID4:       {gen.uuid4()}")

# ── Files ─────────────────────────────────────────────────────
print("\n=== Files ===")
print(f"  File name:  {gen.file_name()}")
print(f"  Extension:  {gen.file_extension()}")
print(f"  MIME type:  {gen.mime_type()}")
print(f"  File path:  {gen.file_path()}")
