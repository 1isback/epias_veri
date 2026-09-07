import pandas as pd
import json
import uuid
import os
from datetime import datetime
from typing import List, Dict, Any

from app.core.logger import log

EXPORT_DIR = "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

class ExportService:
    @staticmethod
    def _to_dataframe(data: List[Dict[str, Any]]) -> pd.DataFrame:
        return pd.DataFrame(data)

    @staticmethod
    async def export_async(data: List[Dict[str, Any]], format: str, prefix: str = "export") -> str:
        """
        Background export generator that saves the dataset to a file and returns the file path.
        """
        if not data:
            raise ValueError("No data to export")
            
        file_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{prefix}_{timestamp}_{file_id}.{format}"
        filepath = os.path.join(EXPORT_DIR, filename)
        
        df = ExportService._to_dataframe(data)
        
        if format == "csv":
            df.to_csv(filepath, index=False)
        elif format == "excel" or format == "xlsx":
            filepath = filepath.replace(".excel", ".xlsx")
            df.to_excel(filepath, index=False)
        elif format == "json":
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        elif format == "parquet":
            df.to_parquet(filepath, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
            
        log.info(f"Export completed: {filepath}")
        return filepath
