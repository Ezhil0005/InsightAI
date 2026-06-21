import os
import sys
import logging
import pandas as pd
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger("QuickCart.Reports")

# Path setups
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from business_metrics import (
    calculate_csi, 
    calculate_revenue_risk, 
    calculate_business_health, 
    calculate_operational_risk
)
from executive_advisor import ExecutiveAdvisor
from scenario_engine import StrategicScenarioEngine
from action_tracker import ActionImpactTracker

# ReportLab Imports
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

class ExecutiveReportGenerator:
    """
    Generates downloadable enterprise-grade PDF summaries for executives.
    """
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def generate_pdf_report(self, df: pd.DataFrame, pdf_filename: str = "executive_report.pdf") -> str:
        """
        Compiles and generates the PDF executive digest report.
        Returns the absolute filepath to the generated PDF.
        """
        pdf_path = os.path.join(self.output_dir, pdf_filename)
        
        if not REPORTLAB_AVAILABLE:
            # Create a simple txt fallback if reportlab is missing
            fallback_txt = pdf_path.replace(".pdf", ".txt")
            with open(fallback_txt, "w", encoding="utf-8") as f:
                f.write("=== EXECUTIVE DIGEST REPORT (FALLBACK) ===\n")
                f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                if not df.empty:
                    f.write(f"Total Feedbacks: {len(df)}\n")
                    f.write(f"Business Health Score: {calculate_business_health(df)}%\n")
                    f.write(f"CSI: {calculate_csi(df)}%\n")
                    f.write(f"Average Churn Risk: {df['churn_risk_percent'].mean():.1f}%\n")
            return fallback_txt

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54
        )
        
        # Styles
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=24,
            leading=28,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=15
        )
        
        subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=colors.HexColor('#475569'),
            spaceAfter=25
        )
        
        h1_style = ParagraphStyle(
            'SectionHeader',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            textColor=colors.HexColor('#1e3a8a'),
            spaceBefore=15,
            spaceAfter=10,
            keepWithNext=True
        )
        
        body_style = ParagraphStyle(
            'BodyTextCustom',
            parent=styles['BodyText'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#334155'),
            spaceAfter=10
        )
        
        callout_style = ParagraphStyle(
            'CalloutText',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=10.5,
            leading=15,
            textColor=colors.HexColor('#1e40af'),
        )
        
        story = []
        
        # Calculate metrics
        csi = calculate_csi(df)
        rev_risk = calculate_revenue_risk(df)
        health = calculate_business_health(df)
        op_risk = calculate_operational_risk(df)
        avg_churn = df['churn_risk_percent'].mean() if 'churn_risk_percent' in df.columns else 20.0
        
        advisor_res = ExecutiveAdvisor.generate_advice(df, {"business_health_score": health})
        
        # 1. Title Block
        story.append(Paragraph("InsightAI Decision Intelligence", title_style))
        story.append(Paragraph(f"<b>EXECUTIVE REPORT DIGEST</b> &bull; Generated: {datetime.now().strftime('%B %d, %Y')} &bull; Baseline Assessment", subtitle_style))
        
        # 2. Executive Scorecard Grid
        story.append(Paragraph("1. Executive Scorecard", h1_style))
        scorecard_data = [
            [
                Paragraph("<b>KPI Metric</b>", body_style), 
                Paragraph("<b>Current State</b>", body_style), 
                Paragraph("<b>Target Range</b>", body_style), 
                Paragraph("<b>Status</b>", body_style)
            ],
            [
                Paragraph("Business Health Score", body_style), 
                Paragraph(f"<b>{health}%</b>", body_style), 
                Paragraph("&gt; 85%", body_style),
                Paragraph("Critical" if health < 60 else ("Warning" if health < 85 else "Optimal"), body_style)
            ],
            [
                Paragraph("Customer Satisfaction Index (CSI)", body_style), 
                Paragraph(f"<b>{csi}%</b>", body_style), 
                Paragraph("&gt; 80%", body_style),
                Paragraph("Needs Uplift" if csi < 75 else "Healthy", body_style)
            ],
            [
                Paragraph("Average Churn Risk", body_style), 
                Paragraph(f"<b>{avg_churn:.1f}%</b>", body_style), 
                Paragraph("&lt; 30%", body_style),
                Paragraph("Elevated" if avg_churn > 40 else "Stable", body_style)
            ],
            [
                Paragraph("Operational Risk Index", body_style), 
                Paragraph(f"<b>{op_risk}%</b>", body_style), 
                Paragraph("&lt; 30%", body_style),
                Paragraph("Elevated" if op_risk > 40 else "Stable", body_style)
            ]
        ]
        
        t_scorecard = Table(scorecard_data, colWidths=[2.2*inch, 1.5*inch, 1.3*inch, 1.5*inch])
        t_scorecard.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('TOPPADDING', (0,0), (-1,0), 8),
            ('LINEBELOW', (0,0), (-1,0), 1.5, colors.HexColor('#cbd5e1')),
            ('LINEBELOW', (0,1), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('BOTTOMPADDING', (0,1), (-1,-1), 6),
            ('TOPPADDING', (0,1), (-1,-1), 6),
        ]))
        story.append(t_scorecard)
        story.append(Spacer(1, 15))
        
        # 3. Advisor Summary & Top Risk
        story.append(Paragraph("2. Strategic Findings & Top Risk areas", h1_style))
        story.append(Paragraph(f"Our operations intelligence algorithms report that the <b>{advisor_res['top_business_risk']}</b> represents the single highest risk sector. This area currently impacts approximately <b>{advisor_res['affected_customers']} users</b>.", body_style))
        
        # Callout block for Recommended Action
        callout_data = [[
            Paragraph(f"<b>Critical Executive Action:</b> {advisor_res['recommended_action']}<br/><i>Expected Outcome:</i> {advisor_res['expected_outcome']}", callout_style)
        ]]
        t_callout = Table(callout_data, colWidths=[6.5*inch])
        t_callout.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#eff6ff')),
            ('BORDER', (0,0), (-1,-1), 1, colors.HexColor('#bfdbfe')),
            ('LINELEFT', (0,0), (-1,-1), 4, colors.HexColor('#3b82f6')),
            ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('LEFTPADDING', (0,0), (-1,-1), 15),
            ('RIGHTPADDING', (0,0), (-1,-1), 15),
        ]))
        story.append(t_callout)
        story.append(Spacer(1, 20))
        
        # Page Break to keep it organized
        story.append(PageBreak())
        
        # 4. Scenario Simulations Comparison Table
        story.append(Paragraph("3. What-If Strategic Scenario Simulations", h1_style))
        story.append(Paragraph("Using historical correlations and category regression models, we have simulated the outcomes of specific operational upgrades to compare their return-on-value metrics.", body_style))
        
        scenario_headers = [
            Paragraph("<b>Scenario Preset</b>", body_style),
            Paragraph("<b>Projected CSI</b>", body_style),
            Paragraph("<b>Churn Drop</b>", body_style),
            Paragraph("<b>Revenue Recovered</b>", body_style),
            Paragraph("<b>Health Index</b>", body_style)
        ]
        
        scenario_rows = [scenario_headers]
        for key in ["Increase Support Team", "Improve Delivery Performance", "Reduce Payment Failures", "Improve App Stability"]:
            res = StrategicScenarioEngine.simulate_scenario(df, key)
            scenario_rows.append([
                Paragraph(f"<b>{res['name']}</b>", body_style),
                Paragraph(f"{res['simulated_csi']}% (+{res['csi_delta']:.1f}%)", body_style),
                Paragraph(f"{res['churn_delta']:.1f}%", body_style),
                Paragraph(f"₹{res['revenue_saved']:,.2f}", body_style),
                Paragraph(f"{res['simulated_health']}%", body_style)
            ])
            
        t_scenarios = Table(scenario_rows, colWidths=[2.2*inch, 1.1*inch, 0.9*inch, 1.3*inch, 1.0*inch])
        t_scenarios.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
            ('LINEBELOW', (0,0), (-1,0), 1.5, colors.HexColor('#cbd5e1')),
            ('LINEBELOW', (0,1), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ]))
        story.append(t_scenarios)
        story.append(Spacer(1, 20))
        
        # 5. Implementation Roadmap
        story.append(Paragraph("4. Tactical Action Roadmap & ROI Metrics", h1_style))
        roadmap = ActionImpactTracker.get_action_roadmap(df)
        
        roadmap_headers = [
            Paragraph("<b>Priority Action</b>", body_style),
            Paragraph("<b>Timeline</b>", body_style),
            Paragraph("<b>Difficulty</b>", body_style),
            Paragraph("<b>Revenue Gain</b>", body_style),
            Paragraph("<b>CSI Lift</b>", body_style)
        ]
        
        roadmap_rows = [roadmap_headers]
        for item in roadmap[:4]: # Top 4
            roadmap_rows.append([
                Paragraph(f"<b>{item['action']}</b><br/><font color='#64748b' size='8'>{item['description'][:50]}...</font>", body_style),
                Paragraph(item["timeline"], body_style),
                Paragraph(item["difficulty"], body_style),
                Paragraph(f"₹{item['revenue_benefit']:,.2f}", body_style),
                Paragraph(f"+{item['csi_benefit']:.1f}%", body_style)
            ])
            
        t_roadmap = Table(roadmap_rows, colWidths=[2.5*inch, 0.9*inch, 0.9*inch, 1.2*inch, 1.0*inch])
        t_roadmap.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f8fafc')),
            ('LINEBELOW', (0,0), (-1,0), 1.5, colors.HexColor('#cbd5e1')),
            ('LINEBELOW', (0,1), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(t_roadmap)
        story.append(Spacer(1, 20))
        
        # Check if there are voice complaints
        voice_df = df[df['source'] == 'voice_uploader'] if ('source' in df.columns and not df.empty) else pd.DataFrame()
        if not voice_df.empty:
            import json
            story.append(PageBreak())
            story.append(Paragraph("5. Multilingual Executive Voice Intelligence", h1_style))
            story.append(Paragraph("This section presents structured analytics, emotions, risks, and recommendations generated from processed voice complaint audio logs.", body_style))
            
            for idx, (_, row) in enumerate(voice_df.iterrows(), 1):
                vid = row.get("id", f"VOICE_REC_{idx}")
                ts = row.get("timestamp", "N/A")
                orig = row.get("original_text", row.get("feedback_text", ""))
                trans = row.get("translated_text", "")
                summary = row.get("voice_summary", "Customer voice recording.")
                emotion = row.get("voice_emotion", "Calm")
                emotion_conf = row.get("emotion_confidence", 1.0)
                pri_score = row.get("voice_priority_score", row.get("priority_score", 50))
                pri_level = row.get("voice_priority_level", "Medium")
                risk_lvl = row.get("voice_risk_level", row.get("risk_level", "Medium"))
                alert_lvl = row.get("executive_alert_level", "Normal")
                impact = row.get("business_impact_score", 50)
                impact_explanation = row.get("impact_explanation", "")
                churn = row.get("churn_risk_percent", 20)
                rec_imm = row.get("immediate_action", row.get("executive_action", ""))
                rec_st = row.get("short_term_action", "")
                rec_lt = row.get("long_term_action", "")
                provider = row.get("provider_used", "heuristics")
                dur = row.get("total_processing_time", 0.0)
                timeline_str = row.get("stage_duration", "{}")
                
                story.append(Paragraph(f"<b>Complaint ID: {vid}</b> (Recorded: {ts})", ParagraphStyle('VoiceID', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, spaceBefore=8, spaceAfter=4)))
                
                metrics_table_data = [
                    [
                        Paragraph("<b>Acoustics & Language</b>", body_style),
                        Paragraph(f"Language: {row.get('language', 'English')}<br/>Duration: {row.get('audio_duration_seconds', 0.0)}s<br/>Quality Score: {row.get('audio_quality_score', 0.0)}%", body_style),
                        Paragraph("<b>Emotion & Sentiment</b>", body_style),
                        Paragraph(f"Emotion: {emotion} ({int(emotion_conf*100)}% conf)<br/>Sentiment: {row.get('sentiment', 'Neutral')}", body_style)
                    ],
                    [
                        Paragraph("<b>Alert & Risk Index</b>", body_style),
                        Paragraph(f"Alert Level: <b><font color='{'red' if alert_lvl=='Critical' else ('orange' if alert_lvl=='Warning' else 'green')}'>{alert_lvl}</font></b><br/>Risk Level: {risk_lvl}<br/>Priority Score: {pri_score} ({pri_level})", body_style),
                        Paragraph("<b>Business Diagnostics</b>", body_style),
                        Paragraph(f"Business Impact: {impact}/100<br/>Churn Risk: {churn}%<br/>Provider Used: {provider}", body_style)
                    ]
                ]
                t_v_metrics = Table(metrics_table_data, colWidths=[1.5*inch, 1.8*inch, 1.4*inch, 1.8*inch])
                t_v_metrics.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#f8fafc')),
                    ('BACKGROUND', (2,0), (2,-1), colors.HexColor('#f8fafc')),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('TOPPADDING', (0,0), (-1,-1), 5),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 5),
                ]))
                story.append(t_v_metrics)
                story.append(Spacer(1, 6))
                
                story.append(Paragraph(f"<b>Original Transcript:</b> <i>\"{orig}\"</i>", body_style))
                if trans and trans != orig:
                    story.append(Paragraph(f"<b>English Translation:</b> <i>\"{trans}\"</i>", body_style))
                story.append(Paragraph(f"<b>Voice Summary:</b> {summary}", body_style))
                story.append(Paragraph(f"<b>Impact Explanation:</b> {impact_explanation}", body_style))
                
                story.append(Paragraph("<b>Action Roadmap Recommendations:</b>", ParagraphStyle('RecHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=9, spaceBefore=4, spaceAfter=2)))
                rec_data = [
                    [Paragraph("<b>Immediate Action:</b>", body_style), Paragraph(rec_imm, body_style)],
                    [Paragraph("<b>Short-Term Action:</b>", body_style), Paragraph(rec_st, body_style)],
                    [Paragraph("<b>Long-Term Action:</b>", body_style), Paragraph(rec_lt, body_style)]
                ]
                t_v_recs = Table(rec_data, colWidths=[1.5*inch, 5.0*inch])
                t_v_recs.setStyle(TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#eff6ff')),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
                    ('TOPPADDING', (0,0), (-1,-1), 4),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ]))
                story.append(t_v_recs)
                
                try:
                    timeline_dict = json.loads(timeline_str)
                    stages_list = [f"{k}: {v}s" for k, v in timeline_dict.items()]
                    timeline_viz = " &rarr; ".join(stages_list) + f" (Total: {dur}s)"
                    story.append(Paragraph(f"<b>Processing Timeline:</b> <font color='#475569' size='8'>{timeline_viz}</font>", ParagraphStyle('TimelineStyle', parent=styles['Normal'], spaceBefore=5, spaceAfter=15)))
                except:
                    story.append(Paragraph(f"<b>Processing Duration:</b> {dur} seconds total", ParagraphStyle('DurationStyle', parent=styles['Normal'], spaceBefore=5, spaceAfter=15)))
                    
                if idx < len(voice_df):
                    story.append(Spacer(1, 10))
            story.append(Spacer(1, 10))
            
        # Sign-off
        story.append(Paragraph("Report generated dynamically by InsightAI platform. All projections are derived from statistical classification distributions and regression models.", subtitle_style))
        
        # Build Document
        doc.build(story)
        logger.info(f"PDF report successfully created at: {pdf_path}")
        return pdf_path
