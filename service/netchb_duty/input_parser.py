"""Input parser for flexible MAWB input formats."""

from __future__ import annotations

import re
from typing import Dict, List


def normalize_mawb(mawb: str) -> str:
    """
    Extract and normalize MAWB to 11 digits.
    
    Args:
        mawb: MAWB string in any format (e.g., "235-94731221", "23594731221")
        
    Returns:
        Normalized MAWB (11 digits, no separators)
        
    Raises:
        ValueError: If MAWB doesn't contain exactly 11 digits
    """
    digits = "".join(ch for ch in mawb if ch.isdigit())
    if len(digits) != 11:
        raise ValueError(f"MAWB '{mawb}' must contain exactly 11 digits, found {len(digits)}")
    return digits


def parse_mawb_input(text: str) -> List[Dict[str, str]]:
    """
    Parse input in multiple formats:
    1. Tab-separated: "ORD\tMZZ\t235-94731221" (3 columns - backward compatible)
    2. Tab-separated: "ORD\tMZZ\tBroker\t4250\t235-94731221" (5 columns - Port, Customer, Broker, HAWBs, Master)
    3. Comma-separated: "ORD,MZZ,235-94731221" (3 columns - backward compatible)
    4. Comma-separated: "ORD,MZZ,Broker,4250,235-94731221" (5 columns)
    5. Space-separated: "235-94731221 ORD MZZ"
    6. Just MAWB: "235-94731221" or "23594731221"
    
    Args:
        text: Raw input text from user
        
    Returns:
        List of dictionaries with keys: mawb, airport_code (optional), customer (optional), checkbook_hawbs (optional)
    """
    if not text or not text.strip():
        return []
    
    results = []
    lines = text.strip().split('\n')
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        
        # Try to detect format by separator
        # Check for tab-separated
        if '\t' in line:
            parts = [p.strip() for p in line.split('\t')]
            checkbook_hawbs = None
            # Handle 5-column format: Port, Customer, Broker, HAWBs, Master
            if len(parts) >= 5:
                # Find the MAWB (11 digits) - it should be the last column
                mawb_raw = parts[4]
                if re.search(r'\d{11}', mawb_raw):
                    airport_code = parts[0] or None
                    customer = parts[1] or None
                    # Broker (parts[2]) is ignored - selected from dropdown
                    checkbook_hawbs = parts[3] or None  # HAWBs at index 3
                else:
                    # Not a valid 5-column format, fall through to 3-column
                    mawb_raw = None
            elif len(parts) >= 3:
                # Format: Airport Code, Customer, MAWB (backward compatible)
                airport_code = parts[0] or None
                customer = parts[1] or None
                mawb_raw = parts[2]
            elif len(parts) == 2:
                # Could be MAWB + something else, or Airport + MAWB
                # Try to identify which is MAWB (contains 11 digits)
                if re.search(r'\d{11}', parts[0]):
                    mawb_raw = parts[0]
                    airport_code = parts[1] if parts[1] and not re.search(r'\d{11}', parts[1]) else None
                    customer = None
                    checkbook_hawbs = None
                elif re.search(r'\d{11}', parts[1]):
                    airport_code = parts[0] if parts[0] and not re.search(r'\d{11}', parts[0]) else None
                    mawb_raw = parts[1]
                    customer = None
                    checkbook_hawbs = None
                else:
                    # Both parts look like non-MAWB, skip
                    continue
            else:
                # Single column - assume it's MAWB
                mawb_raw = parts[0]
                airport_code = None
                customer = None
                checkbook_hawbs = None
        # Check for comma-separated
        elif ',' in line:
            parts = [p.strip() for p in line.split(',')]
            checkbook_hawbs = None
            # Handle 5-column format: Port, Customer, Broker, HAWBs, Master
            if len(parts) >= 5:
                # Find the MAWB (11 digits) - it should be the last column
                mawb_raw = parts[4]
                if re.search(r'\d{11}', mawb_raw):
                    airport_code = parts[0] or None
                    customer = parts[1] or None
                    # Broker (parts[2]) is ignored - selected from dropdown
                    checkbook_hawbs = parts[3] or None  # HAWBs at index 3
                else:
                    # Not a valid 5-column format, fall through to 3-column
                    mawb_raw = None
            elif len(parts) >= 3:
                airport_code = parts[0] or None
                customer = parts[1] or None
                mawb_raw = parts[2]
            elif len(parts) == 2:
                # Try to identify which is MAWB
                if re.search(r'\d{11}', parts[0]):
                    mawb_raw = parts[0]
                    airport_code = parts[1] if parts[1] and not re.search(r'\d{11}', parts[1]) else None
                    customer = None
                    checkbook_hawbs = None
                elif re.search(r'\d{11}', parts[1]):
                    airport_code = parts[0] if parts[0] and not re.search(r'\d{11}', parts[0]) else None
                    mawb_raw = parts[1]
                    customer = None
                    checkbook_hawbs = None
                else:
                    continue
            else:
                mawb_raw = parts[0]
                airport_code = None
                customer = None
                checkbook_hawbs = None
        # Check for space-separated (multiple spaces or single space)
        elif re.search(r'\s{2,}', line) or (line.count(' ') >= 2):
            parts = [p.strip() for p in re.split(r'\s+', line)]
            # Try to find the MAWB (contains 11 digits)
            mawb_part = None
            mawb_idx = None
            for idx, part in enumerate(parts):
                if re.search(r'\d{11}', part):
                    mawb_part = part
                    mawb_idx = idx
                    break
            
            checkbook_hawbs = None
            if mawb_part:
                mawb_raw = mawb_part
                # Handle 5-column format: Port, Customer, Broker, HAWBs, Master
                if len(parts) >= 5 and mawb_idx == 4:
                    airport_code = parts[0] or None
                    customer = parts[1] or None
                    # Broker (parts[2]) is ignored - selected from dropdown
                    checkbook_hawbs = parts[3] or None  # HAWBs at index 3
                else:
                    # Everything before MAWB could be airport/customer
                    before_mawb = parts[:mawb_idx]
                    if len(before_mawb) >= 2:
                        airport_code = before_mawb[0] or None
                        customer = before_mawb[1] or None
                    elif len(before_mawb) == 1:
                        airport_code = before_mawb[0] or None
                        customer = None
                    else:
                        airport_code = None
                        customer = None
            else:
                # No MAWB found, assume first part is MAWB
                mawb_raw = parts[0]
                airport_code = parts[1] if len(parts) > 1 else None
                customer = parts[2] if len(parts) > 2 else None
                checkbook_hawbs = None
        else:
            # Single value - assume it's just MAWB
            mawb_raw = line
            airport_code = None
            customer = None
            checkbook_hawbs = None
        
        # Normalize MAWB
        try:
            normalized_mawb = normalize_mawb(mawb_raw)
            result_dict = {
                "mawb": normalized_mawb,
                "airport_code": airport_code if airport_code else None,
                "customer": customer if customer else None,
            }
            if checkbook_hawbs is not None:
                result_dict["checkbook_hawbs"] = checkbook_hawbs
            results.append(result_dict)
        except ValueError as exc:
            # Skip invalid MAWBs but don't fail entire parse
            continue
    
    return results


