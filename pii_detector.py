"""PII Detection Engine - Hybrid regex + keyword approach."""
import re
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional


@dataclass
class PIIEntity:
    """Represents a detected PII entity."""
    text: str
    entity_type: str
    start: int
    end: int
    score: float = 1.0
    source: str = "regex"  # or "keyword", "ner"


class PIIDetector:
    """Detects PII in text using regex patterns and keyword matching."""

    def __init__(self):
        self._compile_patterns()
        self._build_known_names()
        self._build_false_positives()

    def _compile_patterns(self):
        """Compile regex patterns for different PII types."""
        self.patterns = {
            'EMAIL_ADDRESS': re.compile(
                r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}'
            ),
            'WEBSITE': re.compile(
                r'(?:https?://)?(?:www\.)?[a-zA-Z0-9][a-zA-Z0-9\-]*(?:\.[a-zA-Z0-9][a-zA-Z0-9\-]*)*\.[a-zA-Z]{2,}(?:/[^\s,;)]*)?'
            ),
            'CIN': re.compile(
                r'\b[UL]\d{5}[A-Z]{2}\d{4}(?:PLC|PTC|GAP|NPL|SGC|OAP)\d{6}\b'
            ),
            'SEBI_REG': re.compile(
                r'\bIN[A-Z]{1,2}\d{8,12}\b'
            ),
            'PAN_NUMBER': re.compile(
                r'\b[A-Z]{5}\d{4}[A-Z]\b'
            ),
            'SSN': re.compile(
                r'\b\d{3}[\s\-]\d{2}[\s\-]\d{4}\b'
            ),
            'CREDIT_CARD': re.compile(
                r'\b(?:4\d{3}|5[1-5]\d{2}|6(?:011|5\d{2})|3[47]\d{2})[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'
            ),
            'IP_ADDRESS': re.compile(
                r'\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b'
            ),
            'DATE_OF_BIRTH': re.compile(
                r'(?:(?:born|birth|date of birth|dob|d\.o\.b|age|birthday)\s*[:;]?\s*)'
                r'(?:'
                r'\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4}'
                r'|(?:January|February|March|April|May|June|July|August|September|October|November|December)'
                r'\s+\d{1,2},?\s+\d{4}'
                r'|\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)'
                r',?\s+\d{4}'
                r')',
                re.IGNORECASE
            ),
        }

    def _build_known_names(self):
        """Build list of known person names from the document."""
        self.known_persons = [
            "Kushal Subbayya Hegde", "Pushpa Kushal Hegde",
            "Rajesh Kushal Hegde", "Rohit Kushal Hegde",
            "Rakhi Girija Shetty", "Sarthak Malvadkar",
            "Sandesh Bhagwat", "Amod Joshi", "Ganesh Prasad",
            "Lokesh Shah", "Soumavo Sarkar",
            "Kishan Rastogi", "Abhijit Diwan",
            "Prakash Boricha", "Sheetal Parab",
            "Eric Bacha", "Sachin Gawade", "Pravin Teli",
            "Siddharth Jadhav", "Tushar Gavankar",
            "Varun Badai", "Parag Pansare", "Hitesh Ramani",
            "Chitra Raste", "Sharmila Joshi", "Cherag Gyara",
            "Manisha Shukla", "Tushar Wakhele",
            "Ashish Mathew Pulloor", "Anand Soni",
            "Shanti Gopalkrishnan", "Lalit Muljibhai Sarvaiya",
            "Suvendu Baranwal", "Rajeev Suresh Bakshi",
            "Kusal Bhandary", "Suresh Hegde", "Pushpa Hegde",
        ]

        self.known_companies = [
            "KSH International Limited",
            "KSH International Private Limited",
            "Bhandary Metal Extrusion Private Limited",
            "Waterloo Industrial Park VI Private Limited",
            "Nuvama Wealth Management Limited",
            "ICICI Securities Limited",
            "MUFG Intime India Private Limited",
            "Link Intime India Private Limited",
            "Kirtane & Pandit, LLP", "Kirtane & Pandit LLP",
            "Trilegal",
            "HDFC Bank Limited", "HDFC Bank",
            "ICICI Bank Limited", "ICICI Bank",
            "Citibank N.A.", "Citibank",
            "IndusInd Bank Limited", "IndusInd Bank",
            "State Bank of India",
            "The Federal Bank Limited", "Federal Bank",
            "Bajaj Finance Limited", "Bajaj Finance",
            "Export-Import Bank of India",
            "CARE Analytics and Advisory Private Limited",
            "CareEdge Research",
            "Kanj & Co. LLP", "Kanj & Co",
            "CARE Ratings Limited",
            "KSH INTERNATIONAL LIMITED",
            "KSH International Chakan Internal Kamgar Sangathna",
        ]

        # Use shorter, robust fragments to catch all address variants
        # regardless of punctuation/spacing differences
        self.known_addresses = [
            # Factory / Registered office
            "Village Birdewadi",
            "Birdewadi",
            "Chakan Taluka",
            "Taluka-Khed",
            "Taluka - Khed",
            "Taluka Khed",
            # Corporate office
            "Montreal Business Centre",
            "Pallod Farms",
            "Off Pallod Farms",
            # BKC office
            "Inspire BKC",
            "801-804, Wing A",
            "801 - 804, Wing A",
            "Bandra Kurla Complex",
            # ICICI Securities office
            "ICICI Venture House",
            "Appasaheb Marathe Marg",
            "Appasaheb Marathe",
            # Registrar office
            "C-101, Embassy 247",
            "Embassy 247",
            "L B S Marg, Vikhroli",
            "Vikhroli (West)",
            # HDFC Bank office
            "Lodha I Think Techno Campus",
            "Kanjurmarg Railway Station",
            "Kanjurmarg (East)",
            # ICICI Bank Pune
            "H.T.Parekh Marg",
            "Backbay Reclamation Churchgate",
            # Auditor office
            "Gopal House",
            "Harshal Hall",
            "Opp Harshal Hall",
            "Opposite Harshal Hall",
            "S. No. 127/1B/1",
            # Registrar Pune
            "PCNTDA Green Building",
            "Akurdi Railway Station",
            # Trilegal office
            "One World Centre",
            "Senapati Bapat Marg",
            "Senapati Bapat Road",
            "Senapati Bapat",
            "Lower Parel (West)",
            "10th Floor, Tower 2A",
            # KP office
            "Onyx Tower",
            "Koregaon Park, Pune",
            "North Main Road, Koregaon",
            # Statutory Auditor
            "Signature Building, Bhandarkar",
            "Bhandarkar road Shivaji Nagar",
            "Bhandarkar road",
            # Army area
            "Gen Thimmayya Road",
            "2401 Gen Thimmayya",
            # ICICI Bank Pune
            "Satguru House",
            "Next to Tanishq Showroom",
            "Bund Garden Road",
            # Marathon office
            "Marathon IT Park",
            # Other
            "Tara Chambers",
            "Wakdewadi",
            "Mumbai-Pune Road, Wakdewadi",
            "Unit no. 1601, B- wing BKC",
            "B- wing BKC",
            "Gat No. 11/3, 11/4, 11/5",
            "Gat No. 11/3",
            # Additional building/office fragments
            "Pratik Bunglow",
            "behind Sahara Hotel",
            "Karve Road, Pune",
        ]

    def _build_false_positives(self):
        """Terms that should NOT be redacted."""
        self.false_positive_terms = {
            "SEBI", "BSE", "NSE", "RBI", "MCA", "ROC", "RoC", "IRDA",
            "Government of India", "India", "Republic of India",
            "Securities and Exchange Board of India",
            "National Stock Exchange of India Limited",
            "BSE Limited", "Bombay Stock Exchange",
            "Reserve Bank of India", "Companies Act",
            "SEBI ICDR Regulations", "Red Herring Prospectus",
            "Initial Public Offering", "IPO", "DRHP",
            "Board of Directors", "Board",
            "Maharashtra", "Karnataka", "Gujarat",
            "Mumbai", "Pune", "Delhi", "Bangalore",
            "United States", "European Union", "Sweden",
        }

    def detect(self, text: str) -> List[PIIEntity]:
        """Detect all PII entities in the given text."""
        entities = []

        # 1. Detect emails
        entities.extend(self._detect_regex(text, 'EMAIL_ADDRESS'))

        # 2. Detect phone numbers
        entities.extend(self._detect_phones(text))

        # 3. Detect known person names
        entities.extend(self._detect_known_entities(text, self.known_persons, 'PERSON'))

        # 4. Detect known companies
        entities.extend(self._detect_known_entities(text, self.known_companies, 'ORGANIZATION'))

        # 5. Detect known addresses
        entities.extend(self._detect_known_entities(text, self.known_addresses, 'ADDRESS'))

        # 6. Detect websites
        entities.extend(self._detect_websites(text))

        # 7. Detect CIN numbers
        entities.extend(self._detect_regex(text, 'CIN'))

        # 8. Detect SEBI Registration numbers
        entities.extend(self._detect_regex(text, 'SEBI_REG'))

        # 9. Detect SSN
        entities.extend(self._detect_regex(text, 'SSN'))

        # 10. Detect Credit cards
        entities.extend(self._detect_regex(text, 'CREDIT_CARD'))

        # 11. Detect IP addresses
        entities.extend(self._detect_regex(text, 'IP_ADDRESS'))

        # 12. Detect DOB
        entities.extend(self._detect_regex(text, 'DATE_OF_BIRTH'))

        # Remove overlapping entities (prefer longer matches)
        entities = self._resolve_overlaps(entities)

        return entities

    def _detect_regex(self, text: str, pattern_name: str) -> List[PIIEntity]:
        """Detect PII using a specific regex pattern."""
        entities = []
        pattern = self.patterns.get(pattern_name)
        if not pattern:
            return entities
        for match in pattern.finditer(text):
            matched_text = match.group(0)
            if not self._is_false_positive(matched_text, pattern_name):
                entities.append(PIIEntity(
                    text=matched_text,
                    entity_type=pattern_name,
                    start=match.start(),
                    end=match.end(),
                    score=0.95,
                    source="regex"
                ))
        return entities

    def _detect_phones(self, text: str) -> List[PIIEntity]:
        """Detect phone numbers with Indian format support."""
        entities = []
        phone_patterns = [
            # +91 XX XXXX XXXX or + 91 XX XXXX XXXX
            r'\+\s*91\s*(?:\([\d\s]+\))?\s*[\-]?\s*\d[\d\s\-]{7,14}\d',
            # 0XX-XXXXXXXX
            r'0\d{2}[\-]\d{7,8}',
        ]
        for pattern_str in phone_patterns:
            pattern = re.compile(pattern_str)
            for match in pattern.finditer(text):
                matched_text = match.group(0).strip()
                digits = re.sub(r'\D', '', matched_text)
                if len(digits) >= 10 and not self._is_false_positive(matched_text, 'PHONE_NUMBER'):
                    entities.append(PIIEntity(
                        text=matched_text,
                        entity_type='PHONE_NUMBER',
                        start=match.start(),
                        end=match.end(),
                        score=0.9,
                        source="regex"
                    ))
        return entities

    def _detect_known_entities(self, text: str, known_list: list, entity_type: str) -> List[PIIEntity]:
        """Detect known entities by exact string matching."""
        entities = []
        for name in sorted(known_list, key=len, reverse=True):
            escaped = re.escape(name)
            pattern = re.compile(escaped, re.IGNORECASE if entity_type in ('PERSON', 'ORGANIZATION') else 0)
            for match in pattern.finditer(text):
                entities.append(PIIEntity(
                    text=match.group(0),
                    entity_type=entity_type,
                    start=match.start(),
                    end=match.end(),
                    score=1.0,
                    source="keyword"
                ))
        return entities

    def _detect_websites(self, text: str) -> List[PIIEntity]:
        """Detect website URLs, filtering out regulatory/government sites."""
        entities = []
        gov_domains = {'sebi.gov.in', 'bseindia.com', 'nseindia.com', 'rbi.org.in',
                       'fbil.org.in', 'oanda.com', 'siportal.sebi.gov.in'}
        pattern = self.patterns['WEBSITE']
        for match in pattern.finditer(text):
            url = match.group(0)
            is_gov = any(gov in url.lower() for gov in gov_domains)
            if not is_gov and len(url) > 5:
                entities.append(PIIEntity(
                    text=url,
                    entity_type='WEBSITE',
                    start=match.start(),
                    end=match.end(),
                    score=0.85,
                    source="regex"
                ))
        return entities

    def _is_false_positive(self, text: str, entity_type: str) -> bool:
        """Check if detected text is a false positive."""
        text_stripped = text.strip()
        if len(text_stripped) < 3:
            return True
        if text_stripped in self.false_positive_terms:
            return True
        if entity_type == 'IP_ADDRESS':
            parts = text_stripped.split('.')
            if all(p == '0' for p in parts):
                return True
        return False

    def _resolve_overlaps(self, entities: List[PIIEntity]) -> List[PIIEntity]:
        """Remove overlapping entities, preferring longer matches."""
        if not entities:
            return entities
        entities.sort(key=lambda e: (e.start, -(e.end - e.start)))
        resolved = []
        last_end = -1
        for entity in entities:
            if entity.start >= last_end:
                resolved.append(entity)
                last_end = entity.end
            elif resolved and (entity.end - entity.start) > (resolved[-1].end - resolved[-1].start):
                resolved[-1] = entity
                last_end = entity.end
        return resolved
