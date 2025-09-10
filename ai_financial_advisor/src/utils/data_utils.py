"""
Utility functions for data handling.
"""
import os
import pandas as pd
import time
from typing import Optional


def read_prices(csv_path: str, max_retries: int = 3, wait_time: float = 0.1) -> pd.DataFrame:
    """
    Read price data from CSV file with retry logic for file access issues.
    
    Args:
        csv_path: Path to CSV file
        max_retries: Maximum number of retries if file access fails
        wait_time: Time to wait between retries (seconds)
        
    Returns:
        DataFrame with OHLCV data indexed by date
        
    Raises:
        FileNotFoundError: If CSV file doesn't exist after retries
        ValueError: If CSV file is empty or malformed after retries
    """
    if not os.path.isabs(csv_path):
        csv_path = os.path.abspath(csv_path)
    
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            # Check if file exists and has size > 0
            if not os.path.isfile(csv_path):
                if attempt < max_retries:
                    print(f"⚠️  CSV file not found (attempt {attempt + 1}/{max_retries + 1}): {csv_path}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise FileNotFoundError(f"CSV not found after {max_retries + 1} attempts: {csv_path}")
            
            # Check file size
            file_size = os.path.getsize(csv_path)
            if file_size == 0:
                if attempt < max_retries:
                    print(f"⚠️  CSV file is empty (attempt {attempt + 1}/{max_retries + 1}): {csv_path}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise ValueError(f"CSV file is empty after {max_retries + 1} attempts: {csv_path}")
            
            # Try to read the CSV
            try:
                df = pd.read_csv(csv_path, low_memory=False)
            except (pd.errors.EmptyDataError, pd.errors.ParserError) as e:
                if attempt < max_retries:
                    print(f"⚠️  Failed to parse CSV (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise ValueError(f"Failed to parse CSV after {max_retries + 1} attempts: {e}")
            
            # Validate basic structure
            if df.empty:
                if attempt < max_retries:
                    print(f"⚠️  CSV parsed but empty (attempt {attempt + 1}/{max_retries + 1}): {csv_path}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise ValueError(f"CSV file contains no data after {max_retries + 1} attempts: {csv_path}")
            
            # Process date column
            try:
                date_col = 'Date' if 'Date' in df.columns else df.columns[0]
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce', utc=False)
                df = df.dropna(subset=[date_col]).set_index(date_col).sort_index()
                
                # Validate we still have data after date processing
                if df.empty:
                    if attempt < max_retries:
                        print(f"⚠️  No valid dates found in CSV (attempt {attempt + 1}/{max_retries + 1})")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise ValueError(f"No valid dates found in CSV after {max_retries + 1} attempts")
                
                # Success - return validated DataFrame
                return ensure_df(df)
                
            except Exception as e:
                if attempt < max_retries:
                    print(f"⚠️  Date processing failed (attempt {attempt + 1}/{max_retries + 1}): {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    raise ValueError(f"Date processing failed after {max_retries + 1} attempts: {e}")
                    
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                print(f"⚠️  File access error (attempt {attempt + 1}/{max_retries + 1}): {e}")
                time.sleep(wait_time)
                continue
            else:
                break
    
    # If we get here, all attempts failed
    raise last_error or Exception(f"Failed to read CSV after {max_retries + 1} attempts")


def ensure_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate DataFrame has required OHLCV columns.
    
    Args:
        df: DataFrame to validate
        
    Returns:
        Validated DataFrame
        
    Raises:
        ValueError: If DataFrame is invalid or missing required columns
    """
    if not isinstance(df, pd.DataFrame) or df.empty:
        raise ValueError('Price DataFrame is empty. Check ticker/period/interval.')
    
    required_cols = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    for needed in required_cols:
        if needed not in df.columns:
            raise ValueError(f'Missing column: {needed}')
    
    return df