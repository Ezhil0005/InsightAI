import os
import re
import json
import time
import logging
from typing import Dict, Any, Optional
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from providers import ProviderManager

logger = logging.getLogger("QuickCart.AIEngine")

class RulesFallbackEngine:
    """
    Deterministic rule-based NLP engine for sentiment, category, and advanced decision metrics.
    Used as Tier 3 fallback when no API key or local model is active.
    """
    def __init__(self):
        # Lexicons for sentiment classification
        self.positive_keywords = {
            'excellent', 'great', 'good', 'polite', 'fresh', 'prompt', 'fast', 'love', 
            'happy', 'friendly', 'best', 'quick', 'easy', 'perfect', 'satisfied', 'delicious',
            'awesome', 'wonderful', 'superb', 'smooth', 'helpful', 'super', 'neat', 
            'impressed', 'clean', 'tasty', 'joy', 'glad', 'pleased'
        }
        self.negative_keywords = {
            'crash', 'crashed', 'crashes', 'frustrating', 'frustrated', 'charge', 'charged',
            'refund', 'slow', 'spill', 'spilled', 'spills', 'late', 'bad', 'terrible', 'broken',
            'outdated', 'worst', 'error', 'fail', 'failed', 'issue', 'wait', 'rude',
            'cold', 'unacceptable', 'disappointed', 'spillage', 'delay', 'delayed', 'missing',
            'deducted', 'cancelled', 'canceled', 'wrong', 'never received', 'ridiculous',
            'freezes', 'failing', 'stuck', 'drains', 'greyed', 'disconnected', 'on hold', 'impolite',
            'useless', 'horrible', 'rubbish', 'awful', 'hate', 'careless', 'not responding', 
            'cancel', 'cannot', 'unable', 'aggressively', 'furious', 'angry'
        }
        
        # Priority mapping for category keywords
        self.category_patterns = {
            'Billing': [
                'charge', 'charged', 'refund', 'money', 'cost', 'price', 'pay', 'payment',
                'credit card', 'bill', 'fee', 'overcharged', 'reimburse', 'invoice', 'coupon',
                'deducted', 'service fee', 'double charge', 'paid', 'transaction'
            ],
            'App Bug': [
                'crash', 'crashed', 'crashes', 'checkout', 'ui', 'outdated', 'button', 'broken',
                'app', 'slow', 'search', 'error', 'freeze', 'freezes', 'load', 'bug', 'log in',
                'login', 'screen', 'click', 'loading', 'greyed', 'notification', 'battery', 'map',
                'update', 'save button', 'hangs', 'version'
            ],
            'Delivery': [
                'delivery', 'spill', 'spilled', 'late', 'driver', 'rider', 'speed', 'arrive',
                'time', 'hour', 'food', 'cold', 'spillage', 'delayed', 'delay', 'packaged',
                'marked delivered', 'door', 'building', 'cancelled order', 'delivered to wrong'
            ],
            'Staff/Support': [
                'support', 'person', 'staff', 'rude', 'polite', 'respond', 'agent',
                'help desk', 'customer service', 'representative', 'attitude', 'emails',
                'replied', 'customer care', 'on hold', 'hold for', 'disconnected', 'nobody'
            ]
        }

    def analyze(self, text: str, rating: Optional[int] = None) -> Dict[str, Any]:
        """
        Runs deterministic rule-based analysis on the feedback text.
        Includes advanced language detection, phrase/word translation, and safety verification.
        """
        if not text:
            text = ""
            
        text_lower = text.lower().strip()
        original_text = text

        # 1. Advanced Language Detection (Script & Vocabulary-based)
        has_tamil_char = bool(re.search(r'[\u0B80-\u0BFF]', text))
        has_hindi_char = bool(re.search(r'[\u0900-\u097F]', text))
        
        tanglish_indicators = ["varala", "pannunga", "pannuka", "sapadu", "kuduthanga", "aachu", "romba", "late-ah", "driver-ah", "illai", "irukku", "panni", "pannura", "vandhuchu", "vandhachu", "late ah", "irundhuchu", "worst ah", "innum", "mudiyala", "careless ah", "aagiduchu", "super aa", "irukanga", "pannala", "super ah"]
        hinglish_indicators = ["ho gaya", "karo", "nahi", "aayega", "milega", "kab", "hai", "tha", "se", "aur", "pe", "mein", "gaya", "karna", "bhi", "bola", "tak"]
        
        words = set(re.findall(r'\b\w+\b', text_lower))
        def match_indicator(indicator: str) -> bool:
            if " " in indicator or "-" in indicator:
                return bool(re.search(r'\b' + re.escape(indicator) + r'\b', text_lower))
            return indicator in words

        if has_tamil_char and has_hindi_char:
            language = "Mixed"
        elif has_tamil_char:
            has_eng = any(c.isalpha() for c in text if ord(c) < 128)
            language = "Tanglish" if has_eng else "Tamil"
        elif has_hindi_char:
            has_eng = any(c.isalpha() for c in text if ord(c) < 128)
            language = "Hinglish" if has_eng else "Hindi"
        elif any(match_indicator(w) for w in tanglish_indicators) and any(match_indicator(w) for w in hinglish_indicators):
            language = "Mixed"
        elif any(match_indicator(w) for w in tanglish_indicators):
            language = "Tanglish"
        elif any(match_indicator(w) for w in hinglish_indicators):
            language = "Hinglish"
        else:
            language = "English"

        # 2. Advanced Heuristic Translation (Phrase-level first, then word-level)
        translated_text = text
        translation_confidence = 1.0
        
        if language != "English":
            translation_confidence = 0.90
            try:
                translated_lower = text_lower
                # Phrase replacements
                phrase_mappings = {
                    "டெலிவரி தாமதம்": "delivery was delayed",
                    "பணியாளர்கள் மிகவும் ஆக்ரோஷமாக நடந்துகொள்கிறார்கள்": "staff are behaving very aggressively",
                    "டெலிவரி மிகவும் தாமதமாக வந்தது மற்றும் உணவு குளிர்ந்திருந்தது": "delivery was very delayed and food was cold",
                    "मेरा ऑर्डर बहुत देर से आया और खाना ठंडा था": "my order was very late and food was cold",
                    "पैसे दो बार कट गए लेकिन ऑर्डर कन्फर्म नहीं हुआ": "payment was deducted twice but order was not confirmed",
                    "பணம் இரண்டு முறை கழிக்கப்பட்டது ஆனால் ஆர்டர் உறுதிப்படுத்தப்படவில்லை": "payment was deducted twice but order was not confirmed",
                    "டெலிவரி மிகவும் வேகமாக வந்தது மிகவும் மகிழ்ச்சி": "delivery was very fast and I am very happy",
                    "मेरा ऑर्डर समय से पहले पहुंच गया बहुत अच्छा अनुभव": "my order arrived before expected time and very good experience",
                    "delivery romba late ah vandhuchu": "delivery was very late",
                    "food um cold ah irundhuchu": "food was also cold",
                    "delivery romba worst ah irundhuchu": "delivery was very worst",
                    "customer support bhi help nahi kiya": "customer support did not help",
                    "food super aa irundhuchu": "food was super",
                    "delivery bahut late tha": "delivery was very late",
                    "refund innum varala": "refund was not received yet",
                    "support ne bola kal tak aa jayega": "support said it will come by tomorrow",
                    "app crash aagiduchu": "app crashed",
                    "order cancel panna mudiyala": "unable to cancel order",
                    "customer care not responding": "customer care not responding",
                    "service super ah irundhuchu": "service was excellent",
                    "definitely will order again": "definitely will order again",
                    "romba careless ah": "very careless",
                    "problem solve pannala": "problem not solved",
                    "careless ah irukanga": "are careless",
                    "super ah irundhuchu": "was excellent",
                    "romba late": "very late",
                    "bahut late": "very late",
                    "refund nahi mila": "refund not received",
                    "samay se pehle": "before expected time",
                    "se pehle": "before expected time",
                    "pahunch gaya": "arrived",
                    "pahuch gaya": "arrived",
                    "பணியாளர்கள் மிகவும்": "staff are very",
                    "ஆக்ரோஷமாக நடந்துகொள்கிறார்கள்": "behaving aggressively",
                    "மிகவும் தாமதமாக": "very late",
                    "மற்றும் உணவு": "and food",
                    "இரண்டு முறை": "twice",
                    "கழிக்கப்பட்டது": "deducted",
                    "வேகமாக வந்தது": "came fast",
                    "மிகவும் மகிழ்ச்சி": "very happy",
                }
                
                for phrase, rep in phrase_mappings.items():
                    has_non_ascii = any(ord(c) > 127 for c in phrase)
                    if has_non_ascii:
                        pattern = r'(?<![a-zA-Z0-9])' + re.escape(phrase) + r'(?![a-zA-Z0-9])'
                    else:
                        pattern = r'\b' + re.escape(phrase) + r'\b'
                    translated_lower = re.sub(pattern, rep, translated_lower)
                    
                # Word replacements
                word_mappings = {
                    "டெலிவரி": "delivery",
                    "தாமதம்": "delayed",
                    "தாமதமாக": "delayed",
                    "வந்தது": "arrived",
                    "உணவு": "food",
                    "பணம்": "money",
                    "கழிக்கப்பட்டது": "deducted",
                    "ஆர்டர்": "order",
                    "மகிழ்ச்சி": "happy",
                    "பணியாளர்கள்": "staff",
                    "மிகவும்": "very",
                    "மோசமாக": "worst",
                    "ஆதரவு": "support",
                    "உதவி": "help",
                    "பிரச்சனை": "problem",
                    "வாடிக்கையாளர்": "customer",
                    "மற்றும்": "and",
                    "ஆனால்": "but",
                    "ஆக்ரோஷமாக": "aggressively",
                    "ஆப்": "app",
                    "செயலி": "app",
                    "பக்": "bug",
                    "கட்டணம்": "billing",
                    
                    "ऑर्डर": "order",
                    "देर": "late",
                    "आया": "arrived",
                    "खाना": "food",
                    "ठंडा": "cold",
                    "था": "was",
                    "थी": "was",
                    "पैसे": "money",
                    "दो": "two",
                    "बार": "times",
                    "कट": "deducted",
                    "कन्फर्म": "confirmed",
                    "समय": "time",
                    "अच्छा": "good",
                    "अनुभव": "experience",
                    "कर्मचारी": "staff",
                    "सपोर्ट": "support",
                    
                    "romba": "very",
                    "rombo": "very",
                    "vandhuchu": "arrived",
                    "vanthuchu": "arrived",
                    "vandhachu": "arrived",
                    "irundhuchu": "was",
                    "irunthuchu": "was",
                    "irukanga": "are",
                    "pannala": "did not do",
                    "innum": "yet",
                    "varala": "did not come",
                    "mudiyala": "unable",
                    "aachu": "happened",
                    "panna": "to do",
                    "nalla": "good",
                    
                    "mera": "my",
                    "meri": "my",
                    "mere": "my",
                    "aur": "and",
                    "bhi": "also",
                    "bahut": "very",
                    "bohot": "very",
                    "achha": "good",
                    "acha": "good",
                    "nahi": "not",
                    "nahin": "not",
                    "kiya": "did",
                    "bola": "said",
                    "kal": "tomorrow",
                    "tak": "until",
                    "hua": "happened",
                    "karo": "do",
                    "pe": "on",
                    "mein": "in",
                    "hai": "is"
                }
                
                for word, rep in word_mappings.items():
                    has_non_ascii = any(ord(c) > 127 for c in word)
                    if has_non_ascii:
                        pattern = r'(?<![a-zA-Z0-9])' + re.escape(word) + r'(?![a-zA-Z0-9])'
                    else:
                        pattern = r'\b' + re.escape(word) + r'\b'
                    translated_lower = re.sub(pattern, rep, translated_lower)
                    
                # Clean up spacing
                translated_text = re.sub(r'\s+', ' ', translated_lower).strip()
                # Capitalize
                if translated_text:
                    translated_text = translated_text[0].upper() + translated_text[1:]
                else:
                    translated_text = original_text
            except Exception as e:
                logger.warning(f"Heuristics translation failed: {e}. Falling back to original text.")
                translated_text = original_text
                translation_confidence = 0.50

        # Phase 4 - Translation Safety Layer: Verify translation exists
        if not translated_text or len(translated_text.strip()) == 0:
            translated_text = original_text
            translation_confidence = 0.50
            
        work_text_lower = translated_text.lower()

        # 3. Classify Sentiment
        pos_count = sum(1 for w in self.positive_keywords if w in work_text_lower)
        neg_count = sum(1 for w in self.negative_keywords if w in work_text_lower)
        
        # Adjust count weights for context
        if "worst" in work_text_lower or "careless" in work_text_lower or "aggressively" in work_text_lower or "never received" in work_text_lower:
            neg_count += 3
            
        if pos_count > neg_count:
            sentiment = "Positive"
            analysis_confidence = round(0.70 + (min(pos_count - neg_count, 3) * 0.10), 2)
        elif neg_count > pos_count:
            sentiment = "Negative"
            analysis_confidence = round(0.70 + (min(neg_count - pos_count, 3) * 0.10), 2)
        else:
            sentiment = "Neutral"
            analysis_confidence = 0.70

        # Context overrides
        if "crashed" in work_text_lower or "charged twice" in work_text_lower or "never received" in work_text_lower or "crash" in work_text_lower:
            sentiment = "Negative"
            analysis_confidence = 0.95

        # 4. Classify Category (Weighted Scoring)
        cat_scores = {cat: 0 for cat in self.category_patterns.keys()}
        for cat, keywords in self.category_patterns.items():
            for kw in keywords:
                if kw in work_text_lower:
                    if re.search(r'\b' + re.escape(kw) + r'\b', work_text_lower):
                        cat_scores[cat] += 2
                    else:
                        cat_scores[cat] += 1

        max_score = max(cat_scores.values())
        if max_score > 0:
            priority = ['Billing', 'App Bug', 'Delivery', 'Staff/Support']
            top_cats = [c for c, s in cat_scores.items() if s == max_score]
            category = next((c for c in priority if c in top_cats), top_cats[0])
        else:
            category = "Other"
            
        # Refinement for categories based on translation keywords
        if "staff" in work_text_lower or "careless" in work_text_lower or "support" in work_text_lower or "customer care" in work_text_lower:
            category = "Staff/Support"

        # 5. Generate Issue Summary (First sentence up to 12 words)
        sentences = [s.strip() for s in re.split(r'[.!?]', translated_text) if s.strip()]
        first_sentence = sentences[0] if sentences else translated_text
        first_sentence = re.sub(r'[^\w\s\-\']', '', first_sentence).strip()
        
        words_list = first_sentence.split()
        if len(words_list) > 12:
            summary = " ".join(words_list[:12]) + "..."
        else:
            summary = " ".join(words_list)
            
        if not summary:
            summary = "General customer feedback review."
        else:
            summary = summary[0].upper() + summary[1:]

        # 6. Severity Prediction
        if sentiment == "Negative":
            if any(w in work_text_lower for w in ["double charge", "crashed", "legal", "court", "fraud", "never received", "stole", "crashes", "crash"]):
                severity = "Critical"
            elif any(w in work_text_lower for w in ["late", "delay", "rude", "error", "spill", "broken", "worst", "careless", "aggressively"]):
                severity = "High"
            else:
                severity = "Medium"
        elif sentiment == "Neutral":
            severity = "Medium"
        else:
            severity = "Low"

        # 7. Business Impact Score & Risk Level
        impact_score = 15
        if sentiment == "Negative":
            impact_score += 35
        elif sentiment == "Neutral":
            impact_score += 15
            
        if rating is not None:
            if rating == 1:
                impact_score += 35
            elif rating == 2:
                impact_score += 25
            elif rating == 3:
                impact_score += 10
        else:
            if sentiment == "Negative":
                impact_score += 20
                
        if category in ["Billing", "App Bug"]:
            impact_score += 10
        elif category in ["Delivery", "Staff/Support"]:
            impact_score += 5
            
        if any(w in work_text_lower for w in ["charge", "refund", "crash", "never received", "legal", "fraud", "double charge"]):
            impact_score += 10

        impact_score = min(max(impact_score, 0), 100)

        if impact_score >= 80:
            risk_level = "Critical"
        elif impact_score >= 60:
            risk_level = "High"
        elif impact_score >= 35:
            risk_level = "Medium"
        else:
            risk_level = "Low"

        # 8. Customer Churn Prediction
        churn_risk = 5
        if rating is not None:
            if rating == 1:
                churn_risk += 60
            elif rating == 2:
                churn_risk += 45
            elif rating == 3:
                churn_risk += 20
            elif rating == 4:
                churn_risk += 5
        else:
            if sentiment == "Negative":
                churn_risk += 35
            elif sentiment == "Neutral":
                churn_risk += 10
                
        if category in ["App Bug", "Billing"]:
            churn_risk += 15
        elif category == "Staff/Support":
            churn_risk += 8
            
        if sentiment == "Negative":
            churn_risk += 15

        churn_risk = min(max(churn_risk, 0), 99)

        # 9. Root Cause Intelligence
        root_cause = "General Operations"
        if category == "Delivery":
            if any(w in work_text_lower for w in ["spill", "leak", "packaging"]):
                root_cause = "Packaging Issue"
            elif any(w in work_text_lower for w in ["late", "delay", "hour", "time", "delayed"]):
                root_cause = "Route Planning Failure"
            elif any(w in work_text_lower for w in ["driver", "rider", "rude", "conduct"]):
                root_cause = "Courier Shortage"
            else:
                root_cause = "Warehouse Delay"
        elif category == "App Bug":
            if any(w in work_text_lower for w in ["crash", "crashed", "freeze", "freezes"]):
                root_cause = "Checkout crash"
            elif any(w in work_text_lower for w in ["map", "location", "gps"]):
                root_cause = "GPS/Tracking failure"
            else:
                root_cause = "UI lag"
        elif category == "Billing":
            if any(w in work_text_lower for w in ["charge", "double", "charged twice"]):
                root_cause = "Gateway Timeout"
            elif any(w in work_text_lower for w in ["refund"]):
                root_cause = "Refund Delay"
            else:
                root_cause = "API Failure"
        elif category == "Staff/Support":
            if any(w in work_text_lower for w in ["wait", "time", "hold"]):
                root_cause = "Response Time Delay"
            else:
                root_cause = "Agent Conduct"
        else:
            root_cause = "General Inquiry"

        # 10. Priority Score Formulation
        severity_w = {"Critical": 40, "High": 30, "Medium": 20, "Low": 10}
        sev_val = severity_w.get(severity, 10)
        priority_score = int(sev_val + (impact_score * 0.35) + (churn_risk * 0.35))
        
        # 11. Business Health Score (0-100)
        health_deduct = 0
        if sentiment == "Negative":
            health_deduct += 25
        elif sentiment == "Neutral":
            health_deduct += 8
        health_deduct += (impact_score * 0.25) + (churn_risk * 0.25)
        business_health_score = int(max(100 - health_deduct, 5))

        # 12. Executive Action Plan Mapping
        exec_actions = {
            "Packaging Issue": "Audit delivery bag structural specifications and implement sealed spill-guards.",
            "Route Planning Failure": "Recalibrate dispatch buffer limits and update active route mapping API variables.",
            "Courier Shortage": "Launch weekend incentives to resolve localized delivery courier shortages.",
            "Warehouse Delay": "Optimize picking queue patterns and allocate temporary warehouse packing workers.",
            "Checkout crash": "Roll back recent frontend web payment release and debug checkout session locks.",
            "GPS/Tracking failure": "Rebind core device tracking API client and correct location drift handling.",
            "UI lag": "Optimize dashboard static assets and clean up redundant image layers.",
            "Gateway Timeout": "Set up dual gateway processing fallback routes with our secondary payment broker.",
            "Refund Delay": "Deploy automatic credit settlement rules for dispute values below $15.",
            "API Failure": "Increase connection retry parameters and configure automated transaction daemon restarts.",
            "Response Time Delay": "Launch AI automated response agent to clear repetitive support queues.",
            "Agent Conduct": "Deploy customer service quality training curriculum for support representatives.",
            "General Inquiry": "Improve search categorization in consumer self-service FAQ portal."
        }
        executive_action = exec_actions.get(root_cause, "Implement structural metrics tracking for ongoing reviews.")

        return {
            "sentiment": sentiment,
            "category": category,
            "issue_summary": summary,
            "severity": severity,
            "business_impact_score": impact_score,
            "risk_level": risk_level,
            "churn_risk_percent": churn_risk,
            "root_cause": root_cause,
            "language": language,
            "original_text": original_text,
            "translated_text": translated_text,
            "priority_score": priority_score,
            "business_health_score": business_health_score,
            "executive_action": executive_action,
            "forecast_category": category,
            
            # Confidence fields (Phase 9 requirements)
            "translation_confidence": translation_confidence,
            "analysis_confidence": analysis_confidence
        }


class FeedbackEnricher:
    """
    Enriches feedback text by routing queries to the Universal ProviderManager.
    Supports backwards-compatible inputs while discarding local HuggingFace dependencies.
    """
    def __init__(self, use_openai: bool = False, use_hf: bool = False, use_gemini: bool = False):
        self.provider_manager = ProviderManager()
        
        # Determine default routing mode based on flags
        if use_gemini:
            self.default_mode = "Gemini"
        elif use_openai:
            self.default_mode = "OpenAI"
        else:
            # HuggingFace is removed; falls back to Auto-Select/Heuristics
            self.default_mode = "Auto-Select"
            
        logger.info(f"FeedbackEnricher configured. Standard routing mode: {self.default_mode}")

    def enrich_record(self, text: str, rating: Optional[int] = None) -> Dict[str, Any]:
        """
        Enriches a feedback record by invoking the Universal ProviderManager.
        Guarantees safety against crashes.
        """
        try:
            return self.provider_manager.analyze_feedback(text, rating=rating, mode=self.default_mode)
        except Exception as e:
            logger.error(f"Enrichment runtime failure: {e}. Falling back to rules heuristics.")
            # Absolute fallback
            return self.provider_manager.heuristics_engine.analyze(text, rating=rating)
