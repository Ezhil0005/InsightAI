import os
import logging
import pandas as pd
from typing import Tuple, Dict, Any

from ingestion import DataIngester
from cleaning import FeedbackCleaner
from ai_engine import FeedbackEnricher
from storage import FeedbackDatabase
from reporting import FeedbackReporter
from reports import ExecutiveReportGenerator

logger = logging.getLogger("QuickCart.Pipeline")

def setup_pipeline_logging(output_dir: str):
    """Sets up pipeline logging to both console and output file."""
    os.makedirs(output_dir, exist_ok=True)
    log_file = os.path.join(output_dir, "pipeline.log")
    
    # Clear existing handlers
    logging.root.handlers = []
    
    log_format = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_format)
    root_logger.addHandler(console_handler)
    
    # File
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(log_format)
    root_logger.addHandler(file_handler)
    
    logger.info(f"Pipeline logging initialized. Writing logs to: {log_file}")


def run_pipeline(
    raw_data_path: str, 
    output_dir: str, 
    db_path: str, 
    excel_path: str,
    use_openai: bool = False,
    use_hf: bool = False,
    use_gemini: bool = False
) -> Tuple[pd.DataFrame, pd.DataFrame, str]:
    """
    Executes the end-to-end Customer Feedback Intelligence Pipeline:
    Ingestion -> Cleaning & Validation -> AI Enrichment -> DB Storage -> Excel & Markdown Reporting
    
    Returns:
        (df_cleaned, df_enriched, excel_report_path)
    """
    logger.info("=== QUICKCART PIPELINE RUN STARTING ===")
    logger.info(f"Source file: {raw_data_path}")
    logger.info(f"Target DB: {db_path}")
    logger.info(f"Target Excel: {excel_path}")

    # Phase 0: Cleanup Old Run Data (Full Isolation)
    logger.info("--- Phase 0: Cleanup Old Run Data Starting ---")
    db = FeedbackDatabase(db_path)
    try:
        db.clear_table()
    except Exception as e:
        logger.error(f"Failed to clear database table: {e}")
    finally:
        db.close()

    # Clear old files from disk
    files_to_delete = [
        os.path.join(output_dir, "cleaned_data.csv"),
        os.path.join(output_dir, "enriched_data.csv"),
        os.path.join(output_dir, "summary_report.md"),
        os.path.join(output_dir, "category_distribution.png"),
        os.path.join(output_dir, "sentiment_distribution.png"),
        excel_path
    ]
    for fp in files_to_delete:
        if os.path.exists(fp):
            try:
                os.remove(fp)
                logger.info(f"Removed old pipeline output: {fp}")
            except Exception as e:
                logger.warning(f"Could not remove old file {fp}: {e}")
    logger.info("--- Phase 0: Cleanup Old Run Data Completed ---")

    # Phase 1: Ingestion
    logger.info("--- Phase 1: Ingestion Starting ---")
    ingester = DataIngester(raw_data_path)
    df_raw = ingester.load_data()
    profiling_stats = ingester.profile_data(df_raw)
    logger.info(f"Ingested raw dataset with shape {df_raw.shape}")
    logger.info("--- Phase 1: Ingestion Completed successfully ---")

    # Phase 2: Cleaning
    logger.info("--- Phase 2: Cleaning & Validation Starting ---")
    cleaner = FeedbackCleaner(df_raw)
    df_cleaned = cleaner.process_cleaning()
    
    if df_cleaned.empty:
        raise ValueError("No valid customer feedback records found after cleaning. Please ensure the file contains a 'feedback_text' column (or variants like 'feedback', 'message', 'text', 'comment') and contains non-empty messages.")
    
    # Save intermediate cleaned CSV
    cleaned_csv_path = os.path.join(output_dir, "cleaned_data.csv")
    df_cleaned.to_csv(cleaned_csv_path, index=False)
    logger.info(f"Cleaned records saved to: {cleaned_csv_path}")
    logger.info("--- Phase 2: Cleaning & Validation Completed successfully ---")

    # Phase 3: AI Enrichment
    logger.info("--- Phase 3: AI Enrichment Starting ---")
    enricher = FeedbackEnricher(use_openai=use_openai, use_hf=use_hf, use_gemini=use_gemini)
    
    enriched_records = []
    total_cleaned = len(df_cleaned)
    
    for idx, row in df_cleaned.iterrows():
        feedback_text = row['feedback_text']
        rating = row.get('rating')
        # Enrich feedback with sentiment, category, and issue summary
        enrichments = enricher.enrich_record(feedback_text, rating=rating)
        
        combined_row = row.to_dict()
        combined_row.update(enrichments)
        enriched_records.append(combined_row)
        
        if len(enriched_records) % 100 == 0 or len(enriched_records) == total_cleaned:
            logger.info(f"Enriched {len(enriched_records)}/{total_cleaned} records...")
            
    df_enriched = pd.DataFrame(enriched_records)
    
    # Standardize columns structure for output
    expected_cols = [
        'id', 'timestamp', 'source', 'rating', 'feedback_text', 'sentiment', 'category', 'issue_summary',
        'severity', 'business_impact_score', 'risk_level', 'churn_risk_percent', 'root_cause', 'language',
        'original_text', 'priority_score', 'business_health_score', 'translated_text', 'executive_action',
        'forecast_category'
    ]
    df_enriched = df_enriched[[col for col in expected_cols if col in df_enriched.columns]]
    
    # Save intermediate enriched CSV
    enriched_csv_path = os.path.join(output_dir, "enriched_data.csv")
    df_enriched.to_csv(enriched_csv_path, index=False)
    logger.info(f"Enriched records saved to: {enriched_csv_path}")
    logger.info("--- Phase 3: AI Enrichment Completed successfully ---")

    # Phase 4: Database Storage
    logger.info("--- Phase 4: Database Storage Starting ---")
    db = FeedbackDatabase(db_path)
    try:
        db.save_dataframe(df_enriched, replace_all=True)
        # Verify readback
        df_stored = db.load_dataframe()
    finally:
        db.close()
    logger.info("--- Phase 4: Database Storage Completed successfully ---")

    # Phase 5: Reporting
    logger.info("--- Phase 5: Reporting & Visuals Starting ---")
    reporter = FeedbackReporter(output_dir)
    chart_paths = reporter.generate_charts(df_stored)
    
    # Generate Excel Report
    reporter.generate_excel_report(df_stored, chart_paths, excel_path)
    
    # Generate Markdown Report
    markdown_path = os.path.join(output_dir, "summary_report.md")
    reporter.generate_markdown_report(df_stored, markdown_path)
    
    # Generate PDF Executive Report
    try:
        pdf_generator = ExecutiveReportGenerator(output_dir)
        pdf_generator.generate_pdf_report(df_stored, "executive_report.pdf")
        logger.info("PDF Executive Report generated successfully.")
    except Exception as e:
        logger.error(f"Failed to generate PDF Report: {e}")
    
    logger.info("--- Phase 5: Reporting & Visuals Completed successfully ---")
    logger.info("=== QUICKCART PIPELINE RUN FINISHED SUCCESSFULLY ===")
    
    return df_cleaned, df_stored, excel_path


if __name__ == "__main__":
    import argparse
    from pathlib import Path
    
    # Set up basic paths
    src_dir = Path(__file__).resolve().parent
    project_dir = src_dir.parent
    
    default_raw = str(project_dir.parent / "data" / "customer_feedback_raw.csv")
    default_out = str(project_dir / "output")
    default_db = str(project_dir / "database" / "feedback_active.db")
    default_excel = str(project_dir / "output" / "report.xlsx")
    
    parser = argparse.ArgumentParser(description="QuickCart Customer Feedback pipeline execution script.")
    parser.add_argument("--raw-data", type=str, default=default_raw, help="Path to raw customer feedback CSV/Excel")
    parser.add_argument("--output-dir", type=str, default=default_out, help="Output folder")
    parser.add_argument("--db-path", type=str, default=default_db, help="Database file path")
    parser.add_argument("--excel-name", type=str, default=default_excel, help="Output Excel report path")
    parser.add_argument("--use-openai", action="store_true", help="Enable Tier 1 OpenAI API GPT completions")
    parser.add_argument("--use-hf", action="store_true", help="Enable Tier 2 local Hugging Face Zero-shot pipelines")
    parser.add_argument("--use-gemini", action="store_true", help="Enable Tier 1 Google Gemini API completions")
    
    args = parser.parse_args()
    
    setup_pipeline_logging(args.output_dir)
    
    try:
        run_pipeline(
            raw_data_path=args.raw_data,
            output_dir=args.output_dir,
            db_path=args.db_path,
            excel_path=args.excel_name,
            use_openai=args.use_openai,
            use_hf=args.use_hf,
            use_gemini=args.use_gemini
        )
    except Exception as e:
        logger.exception(f"Pipeline execution crashed: {e}")
