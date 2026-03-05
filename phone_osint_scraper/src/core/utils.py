import phonenumbers

class PhoneNormalizer:
    @staticmethod
    def normalize(phone: str) -> str:
        try:
            parsed = phonenumbers.parse(phone)
            if not phonenumbers.is_valid_number(parsed):
                return phone
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except Exception:
            return phone

class CountryDetector:
    @staticmethod
    def detect(phone: str) -> str:
        try:
            parsed = phonenumbers.parse(phone)
            # return ISO country code (e.g., 'PK', 'US')
            # phonenumbers doesn't directly return the ISO code for the country of the number.
            # but we can get it via the region code for the country calling code.
            region_code = phonenumbers.region_code_for_number(parsed)
            return region_code if region_code else "UNKNOWN"
        except Exception:
            return "UNKNOWN"
