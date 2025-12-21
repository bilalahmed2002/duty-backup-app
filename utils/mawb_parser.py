"""MAWB input parser for bulk processing."""

import re
import json
from typing import List, Dict, Optional
from pathlib import Path

# Debug logging
DEBUG_LOG_PATH = Path(__file__).parent.parent.parent / ".cursor" / "debug.log"


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


def parse_mawb_input(text: str) -> List[Dict[str, Optional[str]]]:
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
    # #region agent log
    try:
        with open(DEBUG_LOG_PATH, 'a') as f:
            f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A",
                "location": "mawb_parser.py:parse_mawb_input:entry",
                "message": "Parser entry",
                "data": {"text_length": len(text) if text else 0, "text_preview": text[:100] if text else None},
                "timestamp": __import__('time').time() * 1000
            }) + "\n")
    except: pass
    # #endregion
    
    if not text or not text.strip():
        return []
    
    # Pre-process: Detect Excel paste format (newline-separated instead of tab-separated)
    # Excel pastes each cell on a new line: JFK\nYDH\nM3\n1325\n999-38649026\nJFK\nBFE\n...
    # We need to reconstruct as: JFK\tYDH\tM3\t1325\t999-38649026\nJFK\tBFE\t...
    text_stripped = text.strip()
    has_tabs = '\t' in text_stripped
    all_lines = [line.strip() for line in text_stripped.split('\n') if line.strip()]
    
    # #region agent log
    try:
        with open(DEBUG_LOG_PATH, 'a') as f:
            f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "B",
                "location": "mawb_parser.py:parse_mawb_input:preprocess",
                "message": "Pre-processing check",
                "data": {
                    "has_tabs": has_tabs,
                    "total_lines": len(all_lines),
                    "first_5_lines": all_lines[:5]
                },
                "timestamp": __import__('time').time() * 1000
            }) + "\n")
    except: pass
    # #endregion
    
    # If no tabs and we have multiple lines, try to reconstruct as tab-separated
    if not has_tabs and len(all_lines) > 1:
        # Try grouping into chunks of 5 (5-column format: Port, Customer, Broker, HAWBs, Master)
        # Or chunks of 3 (3-column format: Airport, Customer, MAWB)
        reconstructed_lines = []
        i = 0
        while i < len(all_lines):
            # Try 5-column format first
            if i + 4 < len(all_lines):
                # Check if the 5th element (index i+4) contains 11 digits (MAWB)
                potential_mawb = all_lines[i + 4]
                digits = ''.join(ch for ch in potential_mawb if ch.isdigit())
                if len(digits) == 11:
                    # This looks like a 5-column row
                    reconstructed_lines.append('\t'.join(all_lines[i:i+5]))
                    i += 5
                    continue
            
            # Try 3-column format
            if i + 2 < len(all_lines):
                # Check if the 3rd element (index i+2) contains 11 digits (MAWB)
                potential_mawb = all_lines[i + 2]
                digits = ''.join(ch for ch in potential_mawb if ch.isdigit())
                if len(digits) == 11:
                    # This looks like a 3-column row
                    reconstructed_lines.append('\t'.join(all_lines[i:i+3]))
                    i += 3
                    continue
            
            # If we can't match a pattern, try to find MAWB in remaining lines
            # Look ahead to find the next 11-digit MAWB
            found_mawb = False
            for j in range(i, min(i + 10, len(all_lines))):
                potential_mawb = all_lines[j]
                digits = ''.join(ch for ch in potential_mawb if ch.isdigit())
                if len(digits) == 11:
                    # Found MAWB at index j
                    # If j - i >= 4, assume 5-column format
                    if j - i >= 4:
                        reconstructed_lines.append('\t'.join(all_lines[i:j+1]))
                        i = j + 1
                        found_mawb = True
                        break
                    # If j - i >= 2, assume 3-column format
                    elif j - i >= 2:
                        reconstructed_lines.append('\t'.join(all_lines[i:j+1]))
                        i = j + 1
                        found_mawb = True
                        break
            
            if not found_mawb:
                # Can't reconstruct, skip this line
                i += 1
        
        if reconstructed_lines:
            # #region agent log
            try:
                with open(DEBUG_LOG_PATH, 'a') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "B",
                        "location": "mawb_parser.py:parse_mawb_input:reconstructed",
                        "message": "Reconstructed from Excel format",
                        "data": {
                            "original_lines": len(all_lines),
                            "reconstructed_lines": len(reconstructed_lines),
                            "first_reconstructed": reconstructed_lines[0] if reconstructed_lines else None
                        },
                        "timestamp": __import__('time').time() * 1000
                    }) + "\n")
            except: pass
            # #endregion
            text_stripped = '\n'.join(reconstructed_lines)
    
    results: List[Dict[str, Optional[str]]] = []
    lines = text_stripped.split('\n')
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line:
            continue
        
        # #region agent log
        try:
            with open(DEBUG_LOG_PATH, 'a') as f:
                f.write(json.dumps({
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "A",
                    "location": f"mawb_parser.py:parse_mawb_input:line_{line_num}",
                    "message": "Processing line",
                    "data": {"line_num": line_num, "line": line, "line_repr": repr(line), "has_tab": '\t' in line, "has_comma": ',' in line},
                    "timestamp": __import__('time').time() * 1000
                }) + "\n")
        except: pass
        # #endregion
        
        # Try to detect format by separator
        # Check for tab-separated
        if '\t' in line:
            parts = [p.strip() for p in line.split('\t')]
            
            # #region agent log
            try:
                with open(DEBUG_LOG_PATH, 'a') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "A",
                        "location": f"mawb_parser.py:parse_mawb_input:tab_split",
                        "message": "Tab-separated detected",
                        "data": {"line_num": line_num, "parts_count": len(parts), "parts": parts, "parts_repr": [repr(p) for p in parts]},
                        "timestamp": __import__('time').time() * 1000
                    }) + "\n")
            except: pass
            # #endregion
            
            checkbook_hawbs = None
            # Handle 5-column format: Port, Customer, Broker, HAWBs, Master
            if len(parts) >= 5:
                # Find the MAWB (11 digits total, may have dashes) - it should be the last column
                mawb_raw = parts[4]
                # Extract all digits and check if we have 11
                digits = ''.join(ch for ch in mawb_raw if ch.isdigit())
                
                # #region agent log
                try:
                    with open(DEBUG_LOG_PATH, 'a') as f:
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "A",
                            "location": f"mawb_parser.py:parse_mawb_input:5col_check",
                            "message": "5-column format check",
                            "data": {"line_num": line_num, "mawb_raw": mawb_raw, "digits": digits, "digits_count": len(digits), "parts_0": parts[0], "parts_1": parts[1], "parts_3": parts[3]},
                            "timestamp": __import__('time').time() * 1000
                        }) + "\n")
                except: pass
                # #endregion
                
                if len(digits) == 11:
                    airport_code = parts[0] if parts[0] else None
                    customer = parts[1] if parts[1] else None
                    # Broker (parts[2]) is ignored - selected from dropdown
                    checkbook_hawbs = parts[3] if parts[3] else None  # HAWBs at index 3
                    
                    # #region agent log
                    try:
                        with open(DEBUG_LOG_PATH, 'a') as f:
                            f.write(json.dumps({
                                "sessionId": "debug-session",
                                "runId": "run1",
                                "hypothesisId": "A",
                                "location": f"mawb_parser.py:parse_mawb_input:5col_extracted",
                                "message": "5-column values extracted",
                                "data": {"line_num": line_num, "airport_code": airport_code, "customer": customer, "checkbook_hawbs": checkbook_hawbs, "mawb_raw": mawb_raw},
                                "timestamp": __import__('time').time() * 1000
                            }) + "\n")
                    except: pass
                    # #endregion
                else:
                    # Not a valid 5-column format, fall through to 3-column
                    mawb_raw = None
                    airport_code = None
                    customer = None
                    
                    # #region agent log
                    try:
                        with open(DEBUG_LOG_PATH, 'a') as f:
                            f.write(json.dumps({
                                "sessionId": "debug-session",
                                "runId": "run1",
                                "hypothesisId": "A",
                                "location": f"mawb_parser.py:parse_mawb_input:5col_failed",
                                "message": "5-column format failed - not 11 digits",
                                "data": {"line_num": line_num, "digits_count": len(digits)},
                                "timestamp": __import__('time').time() * 1000
                            }) + "\n")
                    except: pass
                    # #endregion
            elif len(parts) >= 3:
                # Format: Airport Code, Customer, MAWB (backward compatible)
                airport_code = parts[0] if parts[0] else None
                customer = parts[1] if parts[1] else None
                mawb_raw = parts[2]
            elif len(parts) == 2:
                # Could be MAWB + something else, or Airport + MAWB
                # Try to identify which is MAWB (contains 11 digits total)
                digits0 = ''.join(ch for ch in parts[0] if ch.isdigit())
                digits1 = ''.join(ch for ch in parts[1] if ch.isdigit())
                if len(digits0) == 11:
                    mawb_raw = parts[0]
                    airport_code = parts[1] if parts[1] and len(digits1) != 11 else None
                    customer = None
                    checkbook_hawbs = None
                elif len(digits1) == 11:
                    airport_code = parts[0] if parts[0] and len(digits0) != 11 else None
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
                # Find the MAWB (11 digits total, may have dashes) - it should be the last column
                mawb_raw = parts[4]
                # Extract all digits and check if we have 11
                digits = ''.join(ch for ch in mawb_raw if ch.isdigit())
                if len(digits) == 11:
                    airport_code = parts[0] if parts[0] else None
                    customer = parts[1] if parts[1] else None
                    # Broker (parts[2]) is ignored - selected from dropdown
                    checkbook_hawbs = parts[3] if parts[3] else None  # HAWBs at index 3
                else:
                    # Not a valid 5-column format, fall through to 3-column
                    mawb_raw = None
                    airport_code = None
                    customer = None
            elif len(parts) >= 3:
                airport_code = parts[0] if parts[0] else None
                customer = parts[1] if parts[1] else None
                mawb_raw = parts[2]
            elif len(parts) == 2:
                # Try to identify which is MAWB (contains 11 digits total)
                digits0 = ''.join(ch for ch in parts[0] if ch.isdigit())
                digits1 = ''.join(ch for ch in parts[1] if ch.isdigit())
                if len(digits0) == 11:
                    mawb_raw = parts[0]
                    airport_code = parts[1] if parts[1] and len(digits1) != 11 else None
                    customer = None
                    checkbook_hawbs = None
                elif len(digits1) == 11:
                    airport_code = parts[0] if parts[0] and len(digits0) != 11 else None
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
            # Try to find the MAWB (contains 11 digits total, may have dashes)
            mawb_part = None
            mawb_idx = None
            for idx, part in enumerate(parts):
                # Extract all digits and check if we have 11
                digits = ''.join(ch for ch in part if ch.isdigit())
                if len(digits) == 11:
                    mawb_part = part
                    mawb_idx = idx
                    break
            
            checkbook_hawbs = None
            if mawb_part:
                mawb_raw = mawb_part
                # Handle 5-column format: Port, Customer, Broker, HAWBs, Master
                if len(parts) >= 5 and mawb_idx == 4:
                    airport_code = parts[0] if parts[0] else None
                    customer = parts[1] if parts[1] else None
                    # Broker (parts[2]) is ignored - selected from dropdown
                    checkbook_hawbs = parts[3] if parts[3] else None  # HAWBs at index 3
                else:
                    # Everything before MAWB could be airport/customer
                    before_mawb = parts[:mawb_idx]
                    if len(before_mawb) >= 2:
                        airport_code = before_mawb[0] if before_mawb[0] else None
                        customer = before_mawb[1] if before_mawb[1] else None
                    elif len(before_mawb) == 1:
                        airport_code = before_mawb[0] if before_mawb[0] else None
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
        
        # Normalize MAWB - skip if mawb_raw is None
        if mawb_raw is None:
            continue
            
        try:
            normalized_mawb = normalize_mawb(mawb_raw)
            result_dict: Dict[str, Optional[str]] = {
                "mawb": normalized_mawb,
                "airport_code": airport_code if airport_code else None,
                "customer": customer if customer else None,
            }
            if checkbook_hawbs is not None:
                result_dict["checkbook_hawbs"] = checkbook_hawbs
            results.append(result_dict)
        except ValueError as exc:
            # Skip invalid MAWBs but don't fail entire parse
            # #region agent log
            try:
                with open(DEBUG_LOG_PATH, 'a') as f:
                    f.write(json.dumps({
                        "sessionId": "debug-session",
                        "runId": "run1",
                        "hypothesisId": "A",
                        "location": f"mawb_parser.py:parse_mawb_input:normalize_error",
                        "message": "Normalize MAWB failed",
                        "data": {"line_num": line_num, "error": str(exc), "mawb_raw": mawb_raw},
                        "timestamp": __import__('time').time() * 1000
                    }) + "\n")
            except: pass
            # #endregion
            continue
    
    # #region agent log
    try:
        with open(DEBUG_LOG_PATH, 'a') as f:
            f.write(json.dumps({
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "A",
                "location": "mawb_parser.py:parse_mawb_input:exit",
                "message": "Parser exit",
                "data": {"results_count": len(results), "results": results},
                "timestamp": __import__('time').time() * 1000
            }) + "\n")
    except: pass
    # #endregion
    
    return results


