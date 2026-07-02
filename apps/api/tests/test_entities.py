from app.engine.entities import extract_entities, mask


def types_of(text):
    return {e.entity_type for e in extract_entities(text)}


def test_phone_extraction_and_masking():
    ents = extract_entities("Call me at +91 98123 45670 immediately.")
    phones = [e for e in ents if e.entity_type == "phone"]
    assert phones and phones[0].normalized == "9812345670"
    assert phones[0].masked == "+91-98XXXXXX70"
    assert "9812345670" not in phones[0].masked


def test_upi_not_double_counted_as_email():
    ents = extract_entities("Send money to fraud.helper@ybl right now")
    assert {e.entity_type for e in ents if "@" in e.value} == {"upi_id"}


def test_bank_account_and_ifsc():
    ents = extract_entities("Account no 123456784821 IFSC SBIN0004321")
    accounts = [e for e in ents if e.entity_type == "bank_account"]
    assert accounts and accounts[0].masked.endswith("4821")
    assert accounts[0].masked.startswith("X")
    assert any(e.entity_type == "ifsc" for e in ents)


def test_url_amount_agency():
    text = "CBI notice: pay ₹50,000 via http://fake-rbi.example.in/verify"
    t = types_of(text)
    assert {"url", "amount", "agency"} <= t


def test_hindi_amount():
    assert "amount" in types_of("तुरंत 2 लाख रुपये भेजो")


def test_masking_never_reveals_full_value():
    for etype, value in [
        ("phone", "9812345670"),
        ("bank_account", "123456784821"),
        ("upi_id", "scammer@paytm"),
        ("email", "fraud@evil.com"),
    ]:
        m = mask(etype, value)
        assert value not in m


def test_no_entities_in_clean_text():
    assert types_of("See you at lunch tomorrow!") == set()
