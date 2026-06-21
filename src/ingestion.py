import os
import logging
from typing import Optional

import pandas as pd
import xml.etree.ElementTree as ET

logger = logging.getLogger("QuickCart.Ingestion")


class DataIngester:
    """
    Loads a raw CSV file containing customer feedback and produces
    a pandas DataFrame plus simple profiling output.
    """

    def __init__(self, raw_path: str):
        self.raw_path = raw_path
        self.logger = logging.getLogger("QuickCart.Ingestion")

    def load_data(self) -> pd.DataFrame:
        """
        Attempt to load a CSV or Excel file using robust options.
        Returns a DataFrame. Raises FileNotFoundError if file doesn't exist.
        """
        if not os.path.exists(self.raw_path):
            raise FileNotFoundError(f"Raw data file not found: {self.raw_path}")
        # If the input is an Excel file, use pd.read_excel
        lower = self.raw_path.lower()
        if lower.endswith(('.xls', '.xlsx', '.xlsm', '.xlsb')):
            try:
                self.logger.info(f"Detected Excel file. Attempting to load: {self.raw_path}")
                # read first sheet by default
                df = pd.read_excel(self.raw_path, sheet_name=0)
                df.columns = [c.strip() for c in df.columns]
                if "id" in df.columns:
                    df["id"] = df["id"].astype(str)
                self.logger.info(f"Successfully loaded Excel file. Initial shape: {df.shape}")
                return df
            except Exception as e:
                self.logger.error(f"Failed to read Excel file: {e}")
                raise

        # If the input is XML, try to parse it into a table
        if lower.endswith('.xml'):
            try:
                self.logger.info(f"Detected XML file. Attempting to load: {self.raw_path}")
                # Prefer pandas.read_xml when available (handles many common XML shapes)
                try:
                    df_xml = pd.read_xml(self.raw_path)
                    df_xml.columns = [c.strip() for c in df_xml.columns]
                    if "id" in df_xml.columns:
                        df_xml["id"] = df_xml["id"].astype(str)
                    self.logger.info(f"Successfully loaded XML via pandas.read_xml. Shape: {df_xml.shape}")
                    return df_xml
                except Exception:
                    # Fallback: generic ElementTree parsing
                    tree = ET.parse(self.raw_path)
                    root = tree.getroot()

                    # Find candidate record elements (the most common tag among direct descendants)
                    tags = [child.tag for child in root.findall('.//*')]
                    if not tags:
                        raise ValueError("No elements found in XML file to tabularize")

                    # choose the tag that appears most frequently and has multiple occurrences
                    from collections import Counter
                    tag_counts = Counter(tags)
                    # pick candidate tag with count > 1
                    candidate_tag, count = tag_counts.most_common(1)[0]
                    if count <= 1:
                        # fallback to direct children of root
                        records = list(root)
                    else:
                        records = root.findall('.//'+candidate_tag)

                    rows = []
                    for rec in records:
                        row = {}
                        # include attributes
                        row.update(rec.attrib)
                        # include child elements text
                        for c in rec:
                            row[c.tag] = c.text
                        rows.append(row)

                    df_xml = pd.DataFrame(rows)
                    if not df_xml.empty:
                        df_xml.columns = [c.strip() for c in df_xml.columns]
                        if "id" in df_xml.columns:
                            df_xml["id"] = df_xml["id"].astype(str)
                    self.logger.info(f"Loaded XML via ElementTree fallback. Shape: {df_xml.shape}")
                    return df_xml
            except Exception as e:
                self.logger.error(f"Failed to read XML file: {e}")
                raise

        # Otherwise, attempt CSV using multiple encodings
        encodings = ["utf-8", "latin1", "cp1252"]
        last_error: Optional[Exception] = None

        for enc in encodings:
            try:
                self.logger.info(f"Attempting to load CSV with encoding: {enc}")
                # on_bad_lines='skip' avoids crashing on malformed rows
                df = pd.read_csv(self.raw_path, encoding=enc, on_bad_lines='skip')

                # Normalize column names
                df.columns = [c.strip() for c in df.columns]

                # Ensure expected columns exist (not strict — we'll log missing)
                expected = {"id", "timestamp", "source", "rating", "feedback_text"}
                missing = expected - set(df.columns)
                if missing:
                    self.logger.warning(f"Input CSV is missing expected columns: {missing}")

                # Convert id to string to avoid numeric truncation
                if "id" in df.columns:
                    df["id"] = df["id"].astype(str)

                self.logger.info(f"Successfully loaded CSV with encoding: {enc}. Initial shape: {df.shape}")
                return df
            except Exception as e:
                last_error = e
                self.logger.debug(f"Failed to read with encoding {enc}: {e}")
                continue

        # If we reach here, all encodings failed
        self.logger.error(f"Failed to read CSV with tried encodings. Last error: {last_error}")
        raise last_error if last_error is not None else RuntimeError("Unknown CSV read error")

    def profile_data(self, df: Optional[pd.DataFrame] = None) -> dict:
        """
        Prints/logs simple profiling information about the DataFrame.
        """
        if df is None:
            df = self.load_data()

        self.logger.info("=== Dataset Profiling Report ===")
        total_rows = len(df)
        self.logger.info(f"Total Rows: {total_rows}")

        # Column types
        columns = list(df.columns)
        dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
        self.logger.info(f"Columns: {columns}")
        self.logger.info("Data Types:")
        for col, dtype in df.dtypes.items():
            self.logger.info(f"  - {col}: {dtype}")

        # Missing value counts
        missing_counts = {}
        self.logger.info("Missing Value Counts:")
        for col in df.columns:
            missing = int(df[col].isna().sum())
            missing_counts[col] = missing
            pct = missing / total_rows if total_rows else 0
            self.logger.info(f"  - {col}: {missing} ({pct:.1%})")

        # Exact duplicate rows
        exact_dups = int(df.duplicated(keep='first').sum())
        self.logger.info(f"Exact Duplicate Rows: {exact_dups}")

        # Duplicate messages with different IDs (use feedback_text)
        dup_texts = 0
        if "feedback_text" in df.columns and "id" in df.columns:
            text_counts = df.groupby('feedback_text')['id'].nunique()
            dup_texts = int((text_counts[text_counts > 1]).shape[0])
            self.logger.info(f"Duplicate messages with different IDs: {dup_texts}")

        self.logger.info("=================================")

        return {
            "total_rows": total_rows,
            "columns": columns,
            "data_types": dtypes,
            "missing_value_counts": missing_counts,
            "exact_duplicate_rows": exact_dups,
            "duplicate_text_with_diff_ids": dup_texts
        }


if __name__ == "__main__":
    import argparse
    import logging as _logging
    from pathlib import Path

    _logging.basicConfig(level=_logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    parser = argparse.ArgumentParser(description="Data ingester + profiler for QuickCart feedback CSV")
    parser.add_argument("--raw-data", type=str, default=str(Path(__file__).resolve().parents[1] / "data" / "customer_feedback_raw.csv"), help="Path to raw CSV file")
    args = parser.parse_args()

    ingester = DataIngester(args.raw_data)
    df = ingester.load_data()
    ingester.profile_data(df)
