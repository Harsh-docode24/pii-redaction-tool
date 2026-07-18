"""PII Replacement Engine - Generates consistent fake alternatives using Faker."""
import re
import random
from typing import Dict
from faker import Faker


class PIIReplacer:
    """Generates consistent fake replacements for PII entities."""

    def __init__(self, seed: int = 42):
        """Initialize with a seed for reproducible results."""
        self.fake = Faker()
        Faker.seed(seed)
        random.seed(seed)
        self._mapping: Dict[str, str] = {}

    def get_replacement(self, original_text: str, entity_type: str) -> str:
        """Get a fake replacement for the given PII text.
        
        Returns the same replacement for the same original text (consistency).
        """
        key = f"{entity_type}::{original_text.strip()}"
        key_lower = f"{entity_type}::{original_text.strip().lower()}"
        
        if key in self._mapping:
            return self._mapping[key]
        if entity_type in ('PERSON', 'ORGANIZATION') and key_lower in self._mapping:
            base = self._mapping[key_lower]
            if original_text.isupper():
                return base.upper()
            return base

        replacement = self._generate_replacement(original_text, entity_type)
        self._mapping[key] = replacement
        if entity_type in ('PERSON', 'ORGANIZATION'):
            self._mapping[key_lower] = replacement
        return replacement

    def _generate_replacement(self, original: str, entity_type: str) -> str:
        """Generate a fake replacement based on entity type."""
        generators = {
            'PERSON': self._generate_person_name,
            'EMAIL_ADDRESS': self._generate_email,
            'PHONE_NUMBER': self._generate_phone,
            'ORGANIZATION': self._generate_company,
            'ADDRESS': self._generate_address,
            'WEBSITE': self._generate_website,
            'CIN': lambda _: self._generate_cin(),
            'SEBI_REG': self._generate_sebi_reg,
            'SSN': lambda _: f"{random.randint(100,999)}-{random.randint(10,99)}-{random.randint(1000,9999)}",
            'CREDIT_CARD': lambda _: self.fake.credit_card_number(),
            'IP_ADDRESS': lambda _: self.fake.ipv4(),
            'DATE_OF_BIRTH': lambda _: self.fake.date_of_birth(minimum_age=25, maximum_age=70).strftime('%B %d, %Y'),
        }
        gen = generators.get(entity_type, lambda _: "[REDACTED]")
        return gen(original)

    def _generate_person_name(self, original: str) -> str:
        """Generate a fake person name matching the structure of the original."""
        parts = original.strip().split()
        if len(parts) >= 3:
            name = f"{self.fake.first_name()} {self.fake.first_name()} {self.fake.last_name()}"
        elif len(parts) == 2:
            name = f"{self.fake.first_name()} {self.fake.last_name()}"
        else:
            name = self.fake.first_name()
        if original.isupper():
            return name.upper()
        return name

    def _generate_email(self, original: str) -> str:
        """Generate a fake email matching domain structure."""
        local = self.fake.user_name()
        if '@' in original:
            domain = original.split('@')[1]
            if 'bank' in domain.lower():
                return f"{local}@examplebank.com"
            elif 'nuvama' in domain.lower():
                return f"{local}@investcorp.com"
            elif 'securities' in domain.lower():
                return f"{local}@securitiesfirm.com"
            elif 'ksh' in domain.lower():
                return f"{local}@redactedcorp.com"
        return f"{local}@example.com"

    def _generate_phone(self, original: str) -> str:
        """Generate a fake phone number matching the format."""
        if '+91' in original or '+ 91' in original:
            digits = f"{random.randint(70,99)}{random.randint(10000000, 99999999)}"
            if '(' in original:
                return f"+ 91 ({digits[:2]}) {digits[2:6]} {digits[6:]}"
            parts_count = len(re.findall(r'\d+', original))
            if parts_count >= 4:
                return f"+91 {digits[:2]} {digits[2:6]} {digits[6:]}"
            else:
                return f"+91 {digits}"
        elif original.startswith('0'):
            return f"0{random.randint(20,99)}-{random.randint(10000000, 99999999)}"
        return f"+91 {random.randint(70,99)}{random.randint(10000000, 99999999)}"

    def _generate_company(self, original: str) -> str:
        """Generate a fake company name matching structure."""
        base = self.fake.company()
        if 'Private Limited' in original:
            return f"{base} Private Limited"
        elif 'Limited' in original:
            return f"{base} Limited"
        elif 'LLP' in original:
            return f"{base} LLP"
        elif 'N.A.' in original:
            return f"{base} N.A."
        return base

    def _generate_address(self, original: str) -> str:
        """Generate a fake address."""
        return self.fake.address().replace('\n', ', ')

    def _generate_website(self, original: str) -> str:
        """Generate a fake website URL."""
        domain = self.fake.domain_name()
        if original.startswith('https://'):
            return f"https://www.{domain}"
        elif original.startswith('http://'):
            return f"http://www.{domain}"
        elif original.startswith('www.'):
            return f"www.{domain}"
        return f"www.{domain}"

    def _generate_cin(self) -> str:
        """Generate a fake CIN number."""
        prefix = random.choice(['U', 'L'])
        digits1 = f"{random.randint(10000, 99999)}"
        state = random.choice(['MH', 'DL', 'KA', 'TN', 'GJ', 'RJ', 'UP', 'PN'])
        year = f"{random.randint(1980, 2024)}"
        comp_type = random.choice(['PLC', 'PTC'])
        digits2 = f"{random.randint(100000, 999999)}"
        return f"{prefix}{digits1}{state}{year}{comp_type}{digits2}"

    def _generate_sebi_reg(self, original: str) -> str:
        """Generate a fake SEBI registration number."""
        prefix = original[:3] if len(original) >= 3 else 'INX'
        digits = ''.join(random.choices('0123456789', k=9))
        return f"{prefix}{digits}"

    def get_mapping(self) -> Dict[str, str]:
        """Return the complete PII mapping dictionary."""
        return dict(self._mapping)
