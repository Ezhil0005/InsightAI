import re
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Tuple, Optional, Any
import unicodedata

logger = logging.getLogger("QuickCart.Cleaning")

last_validation_summary = {
    "total_rows": 0,
    "valid_rows": 0,
    "invalid_rows": 0,
    "skipped_rows": 0
}

class FeedbackCleaner:
    """
    Cleans, validates, and normalizes raw customer feedback data.
    """
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        # Precedence for resolving duplicate IDs (higher number = higher trust)
        self.source_precedence = {
            'support_ticket': 3,
            'app_store_review': 2,
            'survey_comment': 1
        }

    def clean_timestamp(self, ts_str: Any) -> Optional[str]:
        """
        Standardizes raw timestamps into 'YYYY-MM-DD HH:MM:SS'.
        If a timestamp is invalid or missing, returns None and logs the issue.
        """
        if pd.isna(ts_str) or not isinstance(ts_str, (str, datetime)) or str(ts_str).strip() == "":
            return None

        if isinstance(ts_str, datetime):
            return ts_str.strftime("%Y-%m-%d %H:%M:%S")

        clean_str = str(ts_str).strip()
        
        # List of potential date formats to parse
        date_formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y %H:%M",
            "%m/%d/%Y",
            "%m/%d/%y %H:%M:%S",
            "%m/%d/%y %H:%M",
            "%m/%d/%y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%B %d %Y",
            "%b %d %Y",
            "%d-%b-%y",
            "%d-%b-%Y",
            "%d-%m-%y",
            "%d-%m-%Y",
            "%d/%m/%Y",
            "%d/%m/%y",
            "%m-%d-%Y",
            "%m-%d-%y",
            "%d %b %Y",
            "%d %B %Y",
        ]

        for fmt in date_formats:
            try:
                dt = datetime.strptime(clean_str, fmt)
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                continue

        # If standard parsing fails, try pandas to_datetime as a fallback (handles some fuzzy formatting)
        try:
            dt = pd.to_datetime(clean_str, errors='raise')
            if not pd.isna(dt):
                return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            pass

        logger.warning(f"Unparseable or invalid timestamp encountered: '{ts_str}'. Coerced to NULL.")
        return None

    def validate_rating(self, rating: Any) -> Optional[int]:
        """
        Validates that rating is an integer between 1 and 5.
        Coerces invalid ratings to None (NULL) and logs it.
        """
        if pd.isna(rating) or str(rating).strip() == "":
            return None

        val = str(rating).strip()
        try:
            # Check if it represents a float or int
            num = float(val)
            if num.is_integer():
                num_int = int(num)
                if 1 <= num_int <= 5:
                    return num_int
                else:
                    logger.warning(f"Rating '{rating}' is out of bounds (must be 1-5). Coerced to NULL.")
            else:
                logger.warning(f"Rating '{rating}' is a non-integer float. Coerced to NULL.")
        except ValueError:
            logger.warning(f"Rating '{rating}' is non-numeric. Coerced to NULL.")
        
        return None

    def is_meaningful_feedback(self, text: Any) -> Tuple[bool, str]:
        """
        Determines if feedback text is meaningful or spam/test data.
        Returns (is_meaningful, log_reason).
        """
        if pd.isna(text) or not isinstance(text, str):
            return False, "Null or non-string feedback"

        # Remove extra whitespace and strip
        cleaned = re.sub(r'\s+', ' ', text).strip()
        
        if len(cleaned) == 0:
            return False, "Empty message"

        # Check if the text is just punctuation/symbols
        if re.match(r'^[^\w\s]+$', cleaned):
            return False, f"Punctuation/symbol only: '{cleaned}'"

        # Check if numeric only
        if cleaned.isdigit():
            return False, f"Numeric only: '{cleaned}'"

        # List of explicit meaningless terms (case-insensitive)
        meaningless_words = {'ok', 'test', 'none', 'n/a', 'null', 'nan', 'hello', 'good', 'fine', 'hi', 'no', 'yes', 'dot', 'spam', 'meh'}
        if cleaned.lower() in meaningless_words:
            return False, f"Meaningless blocklisted word: '{cleaned}'"

        # If it's a very short comment (<= 3 words or <= 15 chars), check if it contains domain keywords
        words = cleaned.lower().split()
        if len(words) <= 3 or len(cleaned) <= 15:
            domain_keywords = {
                'late', 'delay', 'delivery', 'spill', 'cold', 'bad', 'refund', 'charge', 'pay', 
                'app', 'bug', 'crash', 'slow', 'support', 'wait', 'rude', 'wrong', 'missing', 
                'item', 'food', 'driver', 'rider', 'checkout', 'ui', 'spillage', 'crashed',
                'fee', 'money', 'crashes', 'error', 'freeze', 'freezes', 'broken'
            }
            has_keyword = any(w in domain_keywords for w in words) or any(keyword in cleaned.lower() for keyword in domain_keywords)
            if not has_keyword:
                return False, f"Short message without domain relevance: '{cleaned}'"

        return True, "Valid feedback"

    def clean_source(self, source: Any) -> str:
        """
        Normalizes and validates the feedback source name.
        Defaults to 'survey_comment' if invalid.
        """
        if pd.isna(source) or not isinstance(source, str):
            return 'survey_comment'
        
        norm_source = str(source).strip().lower().replace('-', '_').replace(' ', '_')
        valid_sources = {'support_ticket', 'app_store_review', 'survey_comment'}
        
        if norm_source in valid_sources:
            return norm_source
        elif norm_source == 'app_store':
            return 'app_store_review'
        else:
            logger.warning(f"Inconsistent source '{source}' normalized to 'survey_comment'.")
            return 'survey_comment'

    def normalize_feedback_for_duplicate_check(self, text: Any) -> str:
        """
        Builds a duplicate-check key while preserving non-Latin scripts.
        Pandas regex character classes can drop Indic scripts here, which
        incorrectly removed valid Tamil/Hindi feedback as "empty" text.
        """
        if pd.isna(text):
            return ""

        normalized = unicodedata.normalize("NFKC", str(text)).casefold()
        chars = []
        for ch in normalized:
            if ch.isalnum() or ch.isspace():
                chars.append(ch)
        return re.sub(r"\s+", " ", "".join(chars)).strip()

    def process_cleaning(self) -> pd.DataFrame:
        """
        Executes the full cleaning pipeline step-by-step.
        Ensures strict row validation (skips rows with missing rating, timestamp, or feedback_text).
        """
        logger.info(f"Starting cleaning pipeline. Input rows: {len(self.df)}")
        df_work = self.df.copy()
        
        # Normalize column names to handle variant inputs
        cols_lower = {col: col.strip().lower() for col in df_work.columns}
        rename_map = {}
        for orig, low in cols_lower.items():
            if low in ('id', 'identifier', 'rowid'):
                rename_map[orig] = 'id'
            elif low in ('timestamp', 'time', 'created_at', 'date'):
                rename_map[orig] = 'timestamp'
            elif low in ('source', 'origin'):
                rename_map[orig] = 'source'
            elif low in ('rating', 'stars'):
                rename_map[orig] = 'rating'
            elif low in ('feedback_text', 'feedback', 'message', 'text', 'comment', 'body'):
                rename_map[orig] = 'feedback_text'

        if rename_map:
            df_work = df_work.rename(columns=rename_map)

        total_rows = len(df_work)
        valid_rows = 0
        invalid_rows = 0
        skipped_rows = 0

        if 'feedback_text' not in df_work.columns:
            logger.error("Input data does not contain a feedback text column. Aborting cleaning.")
            self.validation_summary = {
                "total_rows": total_rows,
                "valid_rows": 0,
                "invalid_rows": total_rows,
                "skipped_rows": total_rows
            }
            return pd.DataFrame()

        # Step 1: Pre-normalize fields & apply text/timestamp/rating validation
        cleaned_records = []
        for idx, row in df_work.iterrows():
            fb_id = None
            if 'id' in row.index:
                try:
                    fb_id = str(row.get('id')) if not pd.isna(row.get('id')) else None
                    if fb_id is not None:
                        fb_id = fb_id.strip()
                except Exception:
                    fb_id = None

            # Clean and validate source
            source = self.clean_source(row.get('source'))
            
            # Strict validation for rating
            raw_rating = row.get('rating')
            rating = self.validate_rating(raw_rating)
            if rating is None:
                logger.warning(f"Row {idx}: Missing or invalid rating '{raw_rating}'. Skipping row.")
                skipped_rows += 1
                invalid_rows += 1
                continue
                
            # Strict validation for timestamp
            raw_ts = row.get('timestamp')
            timestamp = self.clean_timestamp(raw_ts)
            if timestamp is None:
                logger.warning(f"Row {idx}: Missing or invalid timestamp '{raw_ts}'. Skipping row.")
                skipped_rows += 1
                invalid_rows += 1
                continue

            # Strict validation for feedback_text
            raw_text = row.get('feedback_text', '')
            is_valid_text, reason = self.is_meaningful_feedback(raw_text)
            if not is_valid_text:
                logger.warning(f"Row {idx}: Meaningless or missing feedback_text. Reason: {reason}. Skipping row.")
                skipped_rows += 1
                invalid_rows += 1
                continue

            # Clean extra spaces in text
            clean_text = re.sub(r'\s+', ' ', str(raw_text)).strip()

            cleaned_records.append({
                'id': fb_id,
                'timestamp': timestamp,
                'source': source,
                'rating': rating,
                'feedback_text': clean_text
            })
            valid_rows += 1

        df_cleaned = pd.DataFrame(cleaned_records)
        logger.info(f"After text, timestamp, and rating validation: {len(df_cleaned)} rows remain.")

        # Save validation summary statistics (Phase 5 requirements)
        self.validation_summary = {
            "total_rows": total_rows,
            "valid_rows": len(df_cleaned),
            "invalid_rows": invalid_rows,
            "skipped_rows": skipped_rows
        }

        global last_validation_summary
        last_validation_summary.update(self.validation_summary)

        if df_cleaned.empty:
            return df_cleaned

        # Step 2: Remove near-duplicate messages (messages differing only by punctuation/casing/whitespace)
        df_cleaned['text_norm'] = df_cleaned['feedback_text'].apply(
            self.normalize_feedback_for_duplicate_check
        )

        df_cleaned = df_cleaned[df_cleaned['text_norm'].str.len() > 0]

        dup_text_groups = df_cleaned.groupby('text_norm')
        resolved_text_rows = []
        for text, group in dup_text_groups:
            if len(group) == 1:
                resolved_text_rows.append(group.iloc[0])
                continue

            tmp = group.copy()
            tmp['precedence'] = tmp['source'].map(lambda s: self.source_precedence.get(s, 0))
            tmp['ts_sort'] = pd.to_datetime(tmp['timestamp'], errors='coerce')
            tmp = tmp.sort_values(by=['precedence', 'ts_sort'], ascending=[False, False], na_position='last')
            chosen = tmp.iloc[0].drop(['precedence', 'ts_sort'])
            resolved_text_rows.append(chosen)

        df_cleaned = pd.DataFrame(resolved_text_rows).reset_index(drop=True)
        logger.info(f"After near-duplicate normalization: {len(df_cleaned)} rows remain.")

        # Step 3: Remove exact duplicates (if any remain)
        df_cleaned = df_cleaned.drop_duplicates(keep='first')

        # Step 4: Resolve duplicate IDs (same ID with conflicting data)
        id_groups = df_cleaned.groupby('id')
        resolved_rows = []
        
        for name, group in id_groups:
            if name is None or pd.isna(name):
                for _, r in group.iterrows():
                    resolved_rows.append(r)
                continue
                
            if len(group) == 1:
                resolved_rows.append(group.iloc[0])
            else:
                logger.warning(f"ID Conflict detected for ID '{name}' ({len(group)} records). Resolving...")
                sorted_group = group.copy()
                sorted_group['precedence'] = sorted_group['source'].map(lambda s: self.source_precedence.get(s, 0))
                sorted_group['ts_sort'] = pd.to_datetime(sorted_group['timestamp'], errors='coerce')
                sorted_group = sorted_group.sort_values(
                    by=['precedence', 'ts_sort'], 
                    ascending=[False, False], 
                    na_position='last'
                )
                chosen_record = sorted_group.iloc[0].drop(['precedence', 'ts_sort'])
                resolved_rows.append(chosen_record)

        df_final = pd.DataFrame(resolved_rows)

        if 'text_norm' in df_final.columns:
            df_final = df_final.drop(columns=['text_norm'])

        if 'rating' in df_final.columns:
            df_final['rating'] = df_final['rating'].apply(
                lambda r: int(r) if pd.notnull(r) else None
            )

        logger.info(f"Final cleaned dataset row count: {len(df_final)}")
        return df_final
