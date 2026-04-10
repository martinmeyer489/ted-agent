"""
TED Expert Query Builder

Translates natural language and structured parameters into TED expert search queries.
"""

from datetime import datetime
from typing import List, Optional
import re
from loguru import logger


class TEDQueryBuilder:
    """Build TED Expert Search queries from parameters."""
    
    # Country code mappings (lowercase to uppercase)
    COUNTRY_CODES = {
        "germany": "deu", "france": "fra", "spain": "esp", "italy": "ita",
        "poland": "pol", "netherlands": "nld", "belgium": "bel", "austria": "aut",
        "portugal": "prt", "greece": "grc", "czech republic": "cze", "czechia": "cze",
        "hungary": "hun", "sweden": "swe", "denmark": "dnk", "finland": "fin",
        "slovakia": "svk", "ireland": "irl", "croatia": "hrv", "lithuania": "ltu",
        "slovenia": "svn", "latvia": "lva", "estonia": "est", "cyprus": "cyp",
        "luxembourg": "lux", "malta": "mlt", "bulgaria": "bgr", "romania": "rou",
    }
    
    # CPV category mappings (first 2 digits)
    CPV_CATEGORIES = {
        "it": "72*", "software": "48*", "construction": "45*",
        "services": "71*", "consulting": "79*", "health": "33*",
        "education": "80*", "transport": "60*", "food": "15*",
    }
    
    def __init__(self):
        self.query_parts = []
    
    def country(self, country: str) -> 'TEDQueryBuilder':
        """Add country filter using place of performance (RC field)."""
        country_code = self._normalize_country_code(country)
        if country_code:
            self.query_parts.append(f"RC={country_code}")
        else:
            logger.warning(f"Unknown country: '{country}'")
        return self
    
    def countries(self, countries: List[str]) -> 'TEDQueryBuilder':
        """Add multiple country filter using RC (place of performance) with IN operator."""
        if not countries:
            return self
            
        # Normalize country names to codes
        country_codes = []
        for country in countries:
            code = self._normalize_country_code(country)
            if code:
                country_codes.append(code.upper())
            else:
                logger.warning(f"Unknown country: '{country}'")
        
        if country_codes:
            if len(country_codes) == 1:
                self.query_parts.append(f"RC={country_codes[0]}")
            else:
                codes_str = ", ".join(country_codes)
                self.query_parts.append(f"RC IN ({codes_str})")
        
        return self
    
    def notice_types(self, notice_types: List[str]) -> 'TEDQueryBuilder':
        """Add notice type filter using notice-type field with IN operator.
        
        Args:
            notice_types: List of notice type codes (e.g., ['cn-standard', 'can-standard'])
        
        Common notice types:
            - cn-standard: Contract notice – standard regime
            - can-standard: Contract award notice – standard regime
            - cn-social: Contract notice – light regime
            - can-social: Contract award notice – light regime
            - can-modif: Contract modification notice
            - corr: Change notice
            - compl: Contract completion notice
            - cn-desg: Design contest notice
        """
        if not notice_types:
            return self
        
        # Clean and validate notice types
        clean_types = [nt.strip().lower() for nt in notice_types if nt and nt.strip()]
        
        if clean_types:
            if len(clean_types) == 1:
                self.query_parts.append(f"notice-type={clean_types[0]}")
            else:
                types_str = " ".join(clean_types)
                self.query_parts.append(f"notice-type IN ({types_str})")
        
        return self
    
    def published_after(self, date: str) -> 'TEDQueryBuilder':
        """Add publication date filter (>= date)."""
        clean_date = self._normalize_date(date)
        self.query_parts.append(f"PD>={clean_date}")
        return self
    
    def published_before(self, date: str) -> 'TEDQueryBuilder':
        """Add publication date filter (<= date)."""
        clean_date = self._normalize_date(date)
        self.query_parts.append(f"PD<={clean_date}")
        return self
    
    def cpv_code(self, cpv: str) -> 'TEDQueryBuilder':
        """Add CPV code filter."""
        # Check if it's a category keyword
        if cpv.lower() in self.CPV_CATEGORIES:
            cpv = self.CPV_CATEGORIES[cpv.lower()]
        
        self.query_parts.append(f"classification-cpv={cpv}")
        return self
    
    def title_contains(self, text: str) -> 'TEDQueryBuilder':
        """Add full-text search (searches across all content, not just titles)."""
        text = self._escape_query_text(text)
        self.query_parts.append(f"FT={text}")
        return self
    
    def build(self, sort_by: str = "publication-date DESC") -> str:
        """Build final query string with SORT BY clause."""
        if not self.query_parts:
            query = "ND=*"
        else:
            query = " AND ".join(self.query_parts)
        
        # Add SORT BY clause
        if sort_by:
            query = f"{query} SORT BY {sort_by}"
        
        return query
    
    def reset(self) -> 'TEDQueryBuilder':
        """Reset builder."""
        self.query_parts = []
        return self
    
    def _normalize_country_code(self, country: str) -> Optional[str]:
        """Convert country name to ISO3 code."""
        country_lower = country.lower().strip()
        
        # Check if it's already a 3-letter code
        if len(country_lower) == 3 and country_lower.isalpha():
            return country_lower.upper()
        
        # Look up in mapping
        return self.COUNTRY_CODES.get(country_lower, "").upper() if country_lower in self.COUNTRY_CODES else None
    
    @staticmethod
    def _normalize_date(date_str: str) -> str:
        """Convert date to YYYYMMDD format."""
        formats = [
            "%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", 
            "%d/%m/%Y", "%Y%m%d",
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y%m%d")
            except ValueError:
                continue
        
        if re.match(r'^\d{8}$', date_str):
            return date_str
        
        raise ValueError(f"Invalid date format: {date_str}")
    
    @staticmethod
    def _escape_query_text(text: str) -> str:
        """Escape special characters in query text."""
        # If contains spaces, quote it
        if ' ' in text:
            return f'"{text}"'
        return text


# Recommended fields for comprehensive tender data (based on working example)
DEFAULT_NOTICE_FIELDS = [
    "notice-title",
    "notice-type",
    "publication-date",
    "place-of-performance-city-part",
    "place-of-performance-post-code-part",
    "place-of-performance-country-part",
    "contract-nature-main-proc",
    "contract-nature-add-proc",
    "contract-nature-subtype",
    "description-glo",
    "description-lot",
    "description-part",
    "contract-title",
    "estimated-value-cur-lot",
    "organisation-name-buyer",
    "buyer-category",
    "classification-cpv",
    "ND",
]
