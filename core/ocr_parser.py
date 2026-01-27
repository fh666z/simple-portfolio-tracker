"""OCR-based image parser for Portfolio Tracker."""
import re
from pathlib import Path
from typing import Optional

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from .models import Holding
from .data_parser import parse_number, parse_percentage, clean_instrument_name


def check_tesseract() -> bool:
    """Check if Tesseract is available."""
    if not OCR_AVAILABLE:
        return False
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def parse_image_file(file_path: str | Path) -> list[Holding]:
    """
    Parse an image file using OCR and return list of Holdings.
    
    Expected table format (from input-image.png):
    INSTRUMENT | POSITION | LAST | CHANGE % | COST BASIS | MARKET VALUE | AVG PRICE | DAILY P&L | UNREALIZED P&L
    """
    if not OCR_AVAILABLE:
        raise ImportError("pytesseract and Pillow are required for OCR. Install with: pip install pytesseract Pillow")
    
    if not check_tesseract():
        raise RuntimeError(
            "Tesseract OCR is not installed or not found in PATH.\n"
            "Please install Tesseract:\n"
            "- Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki\n"
            "- Add Tesseract to PATH or set pytesseract.pytesseract.tesseract_cmd"
        )
    
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Load image
    image = Image.open(file_path)
    
    # Use Tesseract with table-friendly settings
    # PSM 6 = Assume a single uniform block of text
    custom_config = r'--oem 3 --psm 6'
    
    # Extract text
    text = pytesseract.image_to_string(image, config=custom_config)
    
    return parse_ocr_text(text)


def parse_ocr_text(text: str) -> list[Holding]:
    """Parse OCR-extracted text into Holdings."""
    lines = text.strip().split('\n')
    holdings = []
    
    # Find header line to understand column structure
    header_idx = -1
    for i, line in enumerate(lines):
        line_upper = line.upper()
        if 'INSTRUMENT' in line_upper or 'POSITION' in line_upper:
            header_idx = i
            break
    
    # Parse data lines (skip header)
    start_idx = header_idx + 1 if header_idx >= 0 else 0
    
    for line in lines[start_idx:]:
        line = line.strip()
        if not line:
            continue
        
        # Try to parse as a data row
        holding = parse_ocr_line(line)
        if holding:
            holdings.append(holding)
    
    return holdings


def parse_ocr_line(line: str) -> Optional[Holding]:
    """
    Parse a single OCR line into a Holding.
    
    The line format is typically space/tab separated:
    INSTRUMENT POSITION LAST CHANGE% COST_BASIS MARKET_VALUE AVG_PRICE DAILY_P&L UNREALIZED_P&L
    """
    # Split by multiple spaces or tabs
    parts = re.split(r'\s{2,}|\t+', line.strip())
    
    # Also try single space split if we don't get enough parts
    if len(parts) < 5:
        parts = line.strip().split()
    
    if len(parts) < 5:
        return None
    
    # First part should be instrument (may contain letters/numbers)
    instrument = clean_instrument_name(parts[0])
    
    # Skip if instrument looks like a number or is empty
    if not instrument or instrument.replace('.', '').replace('-', '').isdigit():
        return None
    
    # Skip header rows and summary rows
    skip_keywords = ['instrument', 'position', 'total', 'sum', 'pending', 'last', 'change']
    if any(kw in instrument.lower() for kw in skip_keywords):
        return None
    
    try:
        # Extract numeric values from remaining parts
        numbers = []
        for part in parts[1:]:
            # Clean the part
            cleaned = part.strip()
            
            # Handle percentage values
            if '%' in cleaned:
                cleaned = cleaned.replace('%', '')
                val = parse_percentage(cleaned)
            else:
                val = parse_number(cleaned)
            
            numbers.append(val)
        
        # Pad with zeros if not enough values
        while len(numbers) < 8:
            numbers.append(0.0)
        
        # Map to Holding fields
        # Expected order: position, last, change%, cost_basis, market_value, avg_price, daily_pnl, unrealized_pnl
        holding = Holding(
            instrument=instrument,
            position=numbers[0],
            last_price=numbers[1],
            change_pct=numbers[2],
            cost_basis=numbers[3],
            market_value=numbers[4],
            avg_price=numbers[5],
            daily_pnl=numbers[6],
            unrealized_pnl=numbers[7] if len(numbers) > 7 else 0.0,
        )
        
        return holding
        
    except (ValueError, IndexError) as e:
        print(f"Warning: Could not parse line '{line}': {e}")
        return None


def parse_image_with_data(file_path: str | Path) -> tuple[list[Holding], str]:
    """
    Parse an image file and return both Holdings and raw OCR text.
    Useful for debugging and showing raw text in review dialog.
    """
    if not OCR_AVAILABLE:
        raise ImportError("pytesseract and Pillow are required for OCR")
    
    if not check_tesseract():
        raise RuntimeError("Tesseract OCR is not installed")
    
    file_path = Path(file_path)
    image = Image.open(file_path)
    
    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(image, config=custom_config)
    
    holdings = parse_ocr_text(text)
    
    return holdings, text
