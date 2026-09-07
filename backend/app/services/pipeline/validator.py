import logging
from typing import List, Dict, Any, Tuple

logger = logging.getLogger(__name__)

class Validator:
    @staticmethod
    def validate_ptf(records: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Validates PTF records.
        Returns (valid_records, invalid_records)
        """
        valid = []
        invalid = []
        
        for record in records:
            if not record.get("date") or record.get("price") is None:
                logger.warning(f"Invalid PTF record missing date or price: {record}")
                invalid.append(record)
                continue
            
            try:
                # ensure numeric types
                float(record["price"])
                float(record.get("priceUsd", 0))
                float(record.get("priceEur", 0))
                valid.append(record)
            except ValueError:
                logger.warning(f"Invalid PTF record price type: {record}")
                invalid.append(record)
                
        return valid, invalid
