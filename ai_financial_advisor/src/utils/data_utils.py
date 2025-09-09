"""
Utility functions for data handling.
"""
import os
import pandas as pd


def read_prices(csv_path: str) -> pd.DataFrame:
    """
    Read price data from CSV file.
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        DataFrame with OHLCV data indexed by date
    """
    if not os.path.isabs(csv_path):
        csv_path = os.path.abspath(csv_path)
    
    if not os.path.isfile(csv_path):
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    
    df = pd.read_csv(csv_path, low_memory=False)
    date_col = 'Date' if 'Date' in df.columns else df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col], errors='coerce', utc=False)
    df = df.dropna(subset=[date_col]).set_index(date_col).sort_index()
    
    return ensure_df(df)


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