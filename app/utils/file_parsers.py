"""
File parsing utilities for lexicon import/export functionality.

Provides functions to parse and validate JSON and CSV files containing
lexicon term data.
"""

import csv
import json
import io
from typing import List, Dict, Tuple
from fastapi import UploadFile, HTTPException, status


# File size limit: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes


async def validate_file_size(file: UploadFile) -> None:
    """
    Validate that the uploaded file does not exceed the maximum size limit.
    
    Args:
        file: The uploaded file to validate
        
    Raises:
        HTTPException: If file size exceeds MAX_FILE_SIZE
    """
    # Read file to check size
    contents = await file.read()
    file_size = len(contents)
    
    # Reset file pointer for subsequent reads
    await file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({file_size} bytes) exceeds maximum allowed size ({MAX_FILE_SIZE} bytes)"
        )


async def parse_json_file(file: UploadFile) -> List[Dict[str, str]]:
    """
    Parse a JSON file containing lexicon terms.
    
    Expected format: [{"term": "...", "replacement": "..."}, ...]
    
    Args:
        file: The uploaded JSON file
        
    Returns:
        List of dictionaries with 'term' and 'replacement' keys
        
    Raises:
        HTTPException: If JSON is invalid or has incorrect structure
    """
    try:
        # Read file contents
        contents = await file.read()
        await file.seek(0)
        
        # Parse JSON
        data = json.loads(contents.decode('utf-8'))
        
        # Validate that data is a list
        if not isinstance(data, list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="JSON file must contain an array of term objects"
            )
        
        # Validate each item has required fields
        parsed_terms = []
        for idx, item in enumerate(data):
            if not isinstance(item, dict):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item at index {idx} is not a valid object"
                )
            
            if 'term' not in item or 'replacement' not in item:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item at index {idx} is missing 'term' or 'replacement' field"
                )
            
            term = str(item['term']).strip()
            replacement = str(item['replacement']).strip()
            
            if not term or not replacement:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Item at index {idx} has empty 'term' or 'replacement' field"
                )
            
            parsed_terms.append({
                'term': term,
                'replacement': replacement
            })
        
        return parsed_terms
        
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON format: {str(e)}"
        )
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File encoding error. Expected UTF-8 encoded JSON file."
        )


async def parse_csv_file(file: UploadFile) -> List[Dict[str, str]]:
    """
    Parse a CSV file containing lexicon terms.
    
    Expected format: Two columns (term, replacement) with header row
    
    Args:
        file: The uploaded CSV file
        
    Returns:
        List of dictionaries with 'term' and 'replacement' keys
        
    Raises:
        HTTPException: If CSV is invalid or has incorrect structure
    """
    try:
        # Read file contents
        contents = await file.read()
        await file.seek(0)
        
        # Decode and parse CSV
        text_content = contents.decode('utf-8')
        csv_file = io.StringIO(text_content)
        
        # Use DictReader to parse CSV with header
        reader = csv.DictReader(csv_file)
        
        # Validate header
        if not reader.fieldnames or len(reader.fieldnames) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file must have at least 2 columns with header row (term, replacement)"
            )
        
        # Check if required columns exist (case-insensitive)
        fieldnames_lower = [f.lower() for f in reader.fieldnames]
        if 'term' not in fieldnames_lower or 'replacement' not in fieldnames_lower:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file must have 'term' and 'replacement' columns in header"
            )
        
        # Find actual column names (preserving original case)
        term_col = None
        replacement_col = None
        for col in reader.fieldnames:
            if col.lower() == 'term':
                term_col = col
            if col.lower() == 'replacement':
                replacement_col = col
        
        # Parse rows
        parsed_terms = []
        for idx, row in enumerate(reader, start=2):  # Start at 2 (header is row 1)
            term = row.get(term_col, '').strip()
            replacement = row.get(replacement_col, '').strip()
            
            if not term or not replacement:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Row {idx} has empty 'term' or 'replacement' field"
                )
            
            parsed_terms.append({
                'term': term,
                'replacement': replacement
            })
        
        if not parsed_terms:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="CSV file contains no data rows"
            )
        
        return parsed_terms
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File encoding error. Expected UTF-8 encoded CSV file."
        )
    except csv.Error as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid CSV format: {str(e)}"
        )


def generate_json_export(terms: List[Dict[str, str]]) -> str:
    """
    Generate JSON string from list of lexicon terms.
    
    Args:
        terms: List of dictionaries with 'term' and 'replacement' keys
        
    Returns:
        JSON formatted string
    """
    return json.dumps(terms, indent=2, ensure_ascii=False)


def generate_csv_export(terms: List[Dict[str, str]]) -> str:
    """
    Generate CSV string from list of lexicon terms.
    
    Args:
        terms: List of dictionaries with 'term' and 'replacement' keys
        
    Returns:
        CSV formatted string with header
    """
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=['term', 'replacement'])
    writer.writeheader()
    writer.writerows(terms)
    return output.getvalue()
