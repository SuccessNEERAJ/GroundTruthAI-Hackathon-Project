"""
PII (Personally Identifiable Information) masking module.
Detects and masks sensitive information before sending to LLM,
then unmasks it in the response.
"""

import re
from typing import Dict, Tuple


def mask_text(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Mask PII in text by replacing with placeholders.
    
    Detects and masks:
    - Phone numbers (various formats)
    - Email addresses
    
    Args:
        text: The original text containing potential PII.
    
    Returns:
        Tuple[str, Dict[str, str]]: 
            - Masked text with placeholders
            - Mapping dictionary from placeholders to original values
    """
    masked_text = text
    mapping = {}
    
    # Phone number patterns - multiple patterns to catch different formats
    phone_patterns = [
        r'\+\d{1,3}[-.\s]?\d{3}[-.\s]?\d{4}',  # +1-555-0101, +1 555 0101 (international short)
        r'\+\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # +1-555-123-4567, +1 (555) 123-4567
        r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}',  # (555) 123-4567
        r'\d{3}[-.\s]\d{3}[-.\s]\d{4}',  # 555-123-4567, 555.123.4567
        r'\b\d{10}\b'  # 5551234567
    ]
    
    phone_counter = 1
    for pattern in phone_patterns:
        phones = re.findall(pattern, masked_text)
        for phone in phones:
            # Skip if already masked or if it's just whitespace
            if phone.strip() and phone not in mapping.values():
                placeholder = f"[PHONE_{phone_counter}]"
                mapping[placeholder] = phone
                masked_text = masked_text.replace(phone, placeholder, 1)
                phone_counter += 1
    
    # Email pattern
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, masked_text)
    
    for i, email in enumerate(emails, 1):
        placeholder = f"[EMAIL_{i}]"
        mapping[placeholder] = email
        masked_text = masked_text.replace(email, placeholder, 1)
    
    return masked_text, mapping


def unmask_text(text: str, mapping: Dict[str, str]) -> str:
    """
    Unmask PII in text by replacing placeholders with original values.
    
    Args:
        text: The masked text with placeholders.
        mapping: Dictionary mapping placeholders to original values.
    
    Returns:
        str: Text with original PII values restored.
    """
    unmasked_text = text
    
    for placeholder, original_value in mapping.items():
        unmasked_text = unmasked_text.replace(placeholder, original_value)
    
    return unmasked_text


def mask_customer_context(context: Dict) -> Tuple[Dict, Dict[str, str]]:
    """
    Mask PII in customer context dictionary.
    
    Args:
        context: Customer context dictionary.
    
    Returns:
        Tuple[Dict, Dict[str, str]]:
            - Masked context dictionary
            - Mapping dictionary for unmasking
    """
    masked_context = context.copy()
    all_mappings = {}
    
    # Mask phone
    if "phone" in masked_context:
        masked_phone, phone_mapping = mask_text(masked_context["phone"])
        masked_context["phone"] = masked_phone
        all_mappings.update(phone_mapping)
    
    # Mask email
    if "email" in masked_context:
        masked_email, email_mapping = mask_text(masked_context["email"])
        masked_context["email"] = masked_email
        all_mappings.update(email_mapping)
    
    return masked_context, all_mappings


if __name__ == "__main__":
    # Demo and testing
    print("=== PII Masking Demo ===\n")
    
    # Test phone masking
    test_texts = [
        "Call me at +1-555-0101 or email john@example.com",
        "My number is (555) 123-4567 and backup is 555.987.6543",
        "Contact: alice@company.com or phone 5551234567"
    ]
    
    for original in test_texts:
        print(f"Original: {original}")
        masked, mapping = mask_text(original)
        print(f"Masked:   {masked}")
        print(f"Mapping:  {mapping}")
        unmasked = unmask_text(masked, mapping)
        print(f"Unmasked: {unmasked}")
        print(f"Match: {original == unmasked}\n")
    
    # Test with LLM-style response
    print("=== LLM Response Masking Test ===\n")
    llm_response = "Sure! You can reach us at [PHONE_1] or email [EMAIL_1] for support."
    mapping = {
        "[PHONE_1]": "+1-555-0101",
        "[EMAIL_1]": "support@coffee.com"
    }
    print(f"Masked response: {llm_response}")
    unmasked_response = unmask_text(llm_response, mapping)
    print(f"Unmasked response: {unmasked_response}")
