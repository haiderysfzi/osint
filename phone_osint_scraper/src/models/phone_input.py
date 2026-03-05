from pydantic import BaseModel, Field, field_validator
import phonenumbers

class PhoneInput(BaseModel):
    phone: str = Field(..., description="Phone number to process")
    
    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v: str) -> str:
        try:
            parsed = phonenumbers.parse(v)
            if not phonenumbers.is_valid_number(parsed):
                # Fallback to loose validation if it doesn't have a '+' prefix but might be valid for a specific region
                # For now, let's stick to strict E.164
                if not v.startswith('+'):
                    raise ValueError("Phone number must start with '+' for E.164 format")
                raise ValueError("Invalid phone number")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise ValueError("Could not parse phone number")
