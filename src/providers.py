import os
import json
import time
import logging
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, List, Tuple
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from audit import log_ai_call, get_audit_stats

logger = logging.getLogger("QuickCart.Providers")

class ProviderScoringEngine:
    """
    Ranks active AI providers based on success rate, latency, and cost records.
    """
    @staticmethod
    def get_provider_scores() -> Dict[str, float]:
        """
        Retrieves recent audit logs stats and computes a combined performance score.
        Score = SuccessRate% * (1000 / (AvgLatencyMs + 10)) * (1 / (EstimatedCostPer1KTokens + 0.001))
        """
        stats = get_audit_stats()
        scores = {}
        
        # Default fallback configurations
        default_latencies = {"openai": 1200.0, "gemini": 800.0, "groq": 300.0, "heuristics": 5.0}
        
        for p in ["openai", "gemini", "groq", "heuristics"]:
            # Retrieve values or use defaults
            p_stats = stats.get(p.upper(), {})
            if p == "heuristics":
                p_stats = stats.get("RULES FALLBACK", stats.get("HEURISTICS", {}))
                
            latency = p_stats.get("avg_latency_ms", default_latencies[p])
            success_rate = p_stats.get("success_rate_pct", 100.0)
            
            # Estimated cost per 1k tokens in USD
            cost_config = config.PROVIDER_COSTS.get(p, {"input": 0.0, "output": 0.0})
            cost_per_1k = (cost_config["input"] * 750) + (cost_config["output"] * 250)
            
            # Avoid divide-by-zero
            latency = max(latency, 1.0)
            success_rate = max(success_rate, 1.0)
            
            # Score formula: higher is better
            latency_factor = 1000.0 / (latency + 10.0)
            cost_factor = 1.0 / (cost_per_1k + 0.0001)
            success_factor = success_rate / 100.0
            
            score = success_factor * latency_factor * cost_factor
            scores[p] = round(score, 4)
            
        return scores

    @staticmethod
    def get_best_provider(available_providers: List[str]) -> str:
        """
        Selects the best provider among those available (keys configured).
        """
        if not available_providers:
            return "heuristics"
            
        scores = ProviderScoringEngine.get_provider_scores()
        # Sort available providers by score descending
        sorted_providers = sorted(
            available_providers, 
            key=lambda p: scores.get(p.lower(), 0.0), 
            reverse=True
        )
        return sorted_providers[0]


class ProviderManager:
    """
    Unified manager executing AI completions, translation, and speech transcription.
    Cascades gracefully from the selected provider down the performance list.
    """
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.gemini_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        from ai_engine import RulesFallbackEngine
        self.heuristics_engine = RulesFallbackEngine()
        self.last_provider_used = "heuristics"
        self.last_fallback_count = 0

    def get_active_providers(self) -> List[str]:
        """
        Returns list of providers that have valid API keys.
        """
        active = []
        if self.openai_key and len(self.openai_key.strip()) > 10:
            active.append("openai")
        if self.gemini_key and len(self.gemini_key.strip()) > 10:
            active.append("gemini")
        if self.groq_key and len(self.groq_key.strip()) > 10:
            active.append("groq")
        return active

    def analyze_feedback(self, text: str, rating: Optional[int] = None, mode: str = "Auto-Select") -> Dict[str, Any]:
        """
        Routes the text enrichment request to the best provider.
        mode can be: 'Auto-Select', 'OpenAI', 'Gemini', 'Groq', 'Heuristics'
        Cascades on failure.
        """
        self.last_provider_used = "heuristics"
        self.last_fallback_count = 0
        active_providers = self.get_active_providers()
        
        # Build priority queue
        queue = []
        selected_mode = mode.lower()
        
        if selected_mode == "openai" and "openai" in active_providers:
            queue = ["openai", "gemini", "groq", "heuristics"]
        elif selected_mode == "gemini" and "gemini" in active_providers:
            queue = ["gemini", "openai", "groq", "heuristics"]
        elif selected_mode == "groq" and "groq" in active_providers:
            queue = ["groq", "gemini", "openai", "heuristics"]
        elif selected_mode == "heuristics" or not active_providers:
            queue = ["heuristics"]
        else:
            # Auto-Select
            best = ProviderScoringEngine.get_best_provider(active_providers)
            queue = [best]
            for p in ["groq", "gemini", "openai", "heuristics"]:
                if p not in queue and (p in active_providers or p == "heuristics"):
                    queue.append(p)
                    
        # Process queue
        fallback_count = 0
        for provider in queue:
            t0 = time.time()
            try:
                if provider == "openai":
                    result, tokens = self._call_openai(text, rating)
                    latency = (time.time() - t0) * 1000.0
                    log_ai_call("OPENAI", latency, "Success", tokens, "analyze_feedback")
                    self.last_provider_used = "openai"
                    self.last_fallback_count = fallback_count
                    return result
                elif provider == "gemini":
                    result, tokens = self._call_gemini(text, rating)
                    latency = (time.time() - t0) * 1000.0
                    log_ai_call("GEMINI", latency, "Success", tokens, "analyze_feedback")
                    self.last_provider_used = "gemini"
                    self.last_fallback_count = fallback_count
                    return result
                elif provider == "groq":
                    result, tokens = self._call_groq(text, rating)
                    latency = (time.time() - t0) * 1000.0
                    log_ai_call("GROQ", latency, "Success", tokens, "analyze_feedback")
                    self.last_provider_used = "groq"
                    self.last_fallback_count = fallback_count
                    return result
                elif provider == "heuristics":
                    result = self.heuristics_engine.analyze(text, rating)
                    latency = (time.time() - t0) * 1000.0
                    log_ai_call("HEURISTICS", latency, "Success", 0, "analyze_feedback")
                    self.last_provider_used = "heuristics"
                    self.last_fallback_count = fallback_count
                    return result
            except Exception as e:
                latency = (time.time() - t0) * 1000.0
                log_ai_call(provider.upper(), latency, f"Error: {str(e)}", 0, "analyze_feedback")
                logger.warning(f"Provider '{provider}' failed: {e}. Cascading to next.")
                fallback_count += 1
                
        # If all fail (should not happen as heuristics is bulletproof)
        self.last_provider_used = "heuristics"
        self.last_fallback_count = fallback_count
        return self.heuristics_engine.analyze(text, rating)

    def transcribe_audio(self, file_name: str, file_bytes: bytes, mode: str = "Auto-Select") -> str:
        """
        Routes Speech-to-Text transcription.
        mode can be: 'Auto-Select', 'OpenAI', 'Gemini', 'Groq', 'Mock'
        """
        self.last_provider_used = "mock"
        self.last_fallback_count = 0
        active_providers = self.get_active_providers()
        queue = []
        selected_mode = mode.lower()
        
        if "openai" in selected_mode and "openai" in active_providers:
            queue = ["openai", "gemini", "groq", "mock"]
        elif "gemini" in selected_mode and "gemini" in active_providers:
            queue = ["gemini", "openai", "groq", "mock"]
        elif "groq" in selected_mode and "groq" in active_providers:
            queue = ["groq", "openai", "gemini", "mock"]
        elif "mock" in selected_mode:
            queue = ["mock"]
        else:
            # Auto-Select
            best = ProviderScoringEngine.get_best_provider([p for p in active_providers if p in ["openai", "gemini", "groq"]])
            queue = [best] if best in ["openai", "gemini", "groq"] else []
            for p in ["openai", "gemini", "groq", "mock"]:
                if p not in queue and (p in active_providers or p == "mock"):
                    queue.append(p)
                    
        fallback_count = 0
        for provider in queue:
            t0 = time.time()
            try:
                if provider == "openai":
                    transcript = self._transcribe_openai(file_name, file_bytes)
                    latency = (time.time() - t0) * 1000.0
                    log_ai_call("OPENAI_WHISPER", latency, "Success", 100, "transcribe_audio") # Est 100 tokens
                    self.last_provider_used = "openai"
                    self.last_fallback_count = fallback_count
                    return transcript
                elif provider == "gemini":
                    transcript = self._transcribe_gemini(file_name, file_bytes)
                    latency = (time.time() - t0) * 1000.0
                    log_ai_call("GEMINI_AUDIO", latency, "Success", 150, "transcribe_audio") # Est 150 tokens
                    self.last_provider_used = "gemini"
                    self.last_fallback_count = fallback_count
                    return transcript
                elif provider == "groq":
                    transcript = self._transcribe_groq(file_name, file_bytes)
                    latency = (time.time() - t0) * 1000.0
                    log_ai_call("GROQ_WHISPER", latency, "Success", 120, "transcribe_audio") # Est 120 tokens
                    self.last_provider_used = "groq"
                    self.last_fallback_count = fallback_count
                    return transcript
                elif provider == "mock":
                    transcript = self._transcribe_mock(file_name, file_bytes)
                    latency = (time.time() - t0) * 1000.0
                    log_ai_call("MOCK_VOICE", latency, "Success", 0, "transcribe_audio")
                    self.last_provider_used = "mock"
                    self.last_fallback_count = fallback_count
                    return transcript
            except Exception as e:
                latency = (time.time() - t0) * 1000.0
                log_ai_call(provider.upper() + "_VOICE", latency, f"Error: {str(e)}", 0, "transcribe_audio")
                logger.warning(f"Voice provider '{provider}' failed: {e}. Cascading.")
                fallback_count += 1
                
        self.last_provider_used = "mock"
        self.last_fallback_count = fallback_count
        return self._transcribe_mock(file_name, file_bytes)

    # API Implementation Methods
    def _call_openai(self, text: str, rating: Optional[int]) -> Tuple[Dict[str, Any], int]:
        import openai
        client = openai.OpenAI(api_key=self.openai_key)
        prompt = self._build_prompt(text, rating)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": "You are a customer feedback intelligence parser. You must strictly output JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0
        )
        res_content = response.choices[0].message.content
        tokens = response.usage.total_tokens if response.usage else 250
        return self._post_process_json(json.loads(res_content), text), tokens

    def _call_gemini(self, text: str, rating: Optional[int]) -> Tuple[Dict[str, Any], int]:
        prompt = self._build_prompt(text, rating)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json"}
        }
        
        data_bytes = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
        
        with urllib.request.urlopen(req, timeout=12) as response:
            res_content = response.read().decode('utf-8')
            res_json = json.loads(res_content)
            text_out = res_json['candidates'][0]['content']['parts'][0]['text']
            
        # Est tokens: 250
        return self._post_process_json(json.loads(text_out.strip()), text), 250

    def _call_groq(self, text: str, rating: Optional[int]) -> Tuple[Dict[str, Any], int]:
        prompt = self._build_prompt(text, rating)
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.groq_key}"
        }
        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": "You are a customer feedback intelligence parser. You must strictly output JSON format."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.0
        }
        
        data_bytes = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
        
        with urllib.request.urlopen(req, timeout=10) as response:
            res_content = response.read().decode('utf-8')
            res_json = json.loads(res_content)
            text_out = res_json['choices'][0]['message']['content']
            tokens = res_json.get('usage', {}).get('total_tokens', 250)
            
        return self._post_process_json(json.loads(text_out.strip()), text), tokens

    def _build_prompt(self, text: str, rating: Optional[int]) -> str:
        return f"""
        Analyze this customer feedback:
        Text: "{text}"
        Rating: {rating if rating is not None else "None"}
        
        You must return a valid JSON object matching this structure:
        {{
          "sentiment": "Positive" | "Negative" | "Neutral",
          "category": "Billing" | "App Bug" | "Delivery" | "Staff/Support" | "Other",
          "issue_summary": "One short sentence summary in English.",
          "severity": "Low" | "Medium" | "High" | "Critical",
          "business_impact_score": <integer from 0 to 100>,
          "risk_level": "Low" | "Medium" | "High" | "Critical",
          "churn_risk_percent": <integer from 0 to 100>,
          "root_cause": "Select specific operational root cause: Packaging Issue, Route Planning Failure, Courier Shortage, Warehouse Delay, Checkout crash, GPS/Tracking failure, UI lag, Gateway Timeout, Refund Delay, API Failure, Response Time Delay, Agent Conduct, General Inquiry",
          "language": "English" | "Hindi" | "Tamil",
          "translated_text": "English translation if input is Tamil/Hindi, else same as original",
          "executive_action": "Operational quick-fix recommendation.",
          "forecast_category": "Billing" | "App Bug" | "Delivery" | "Staff/Support" | "Other"
        }}
        """

    def _post_process_json(self, data: Dict[str, Any], text: str) -> Dict[str, Any]:
        """Ensures priority and business health calculations are added to output."""
        sentiment = data.get("sentiment", "Neutral")
        category = data.get("category", "Other")
        
        severity_w = {"Critical": 40, "High": 30, "Medium": 20, "Low": 10}
        sev_val = severity_w.get(data.get("severity", "Low"), 10)
        
        impact = int(data.get("business_impact_score", 15))
        churn = int(data.get("churn_risk_percent", 5))
        
        priority_score = int(sev_val + (impact * 0.35) + (churn * 0.35))
        
        health_deduct = 0
        if sentiment == "Negative":
            health_deduct += 25
        elif sentiment == "Neutral":
            health_deduct += 8
        health_deduct += (impact * 0.25) + (churn * 0.25)
        business_health_score = int(max(100 - health_deduct, 5))
        
        return {
            "sentiment": sentiment,
            "category": category,
            "issue_summary": data.get("issue_summary", "Feedback analyzed by AI."),
            "severity": data.get("severity", "Low"),
            "business_impact_score": impact,
            "risk_level": data.get("risk_level", "Low"),
            "churn_risk_percent": churn,
            "root_cause": data.get("root_cause", "General Inquiry"),
            "language": data.get("language", "English"),
            "original_text": text,
            "translated_text": data.get("translated_text", text),
            "priority_score": priority_score,
            "business_health_score": business_health_score,
            "executive_action": data.get("executive_action", "Monitor operational logs."),
            "forecast_category": category
        }

    # Transcribe implementation methods
    def _transcribe_openai(self, file_name: str, file_bytes: bytes) -> str:
        import openai
        client = openai.OpenAI(api_key=self.openai_key)
        temp_filename = f"temp_voice_{file_name}"
        with open(temp_filename, "wb") as f:
            f.write(file_bytes)
        try:
            with open(temp_filename, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            return str(transcript).strip()
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    def _transcribe_gemini(self, file_name: str, file_bytes: bytes) -> str:
        import base64
        normalized_name = file_name.lower()
        mime_type = "audio/mp3"
        if normalized_name.endswith(".wav"):
            mime_type = "audio/wav"
        elif normalized_name.endswith(".m4a"):
            mime_type = "audio/m4a"
        elif normalized_name.endswith(".ogg"):
            mime_type = "audio/ogg"

        audio_b64 = base64.b64encode(file_bytes).decode("utf-8")
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        headers = {"Content-Type": "application/json"}
        prompt = "Please accurately transcribe this audio recording into English text. Only return the transcription, nothing else."
        payload = {
            "contents": [{
                "parts": [
                    {"inlineData": {"mimeType": mime_type, "data": audio_b64}},
                    {"text": prompt}
                ]
            }]
        }
        
        data_bytes = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=18) as response:
            res_content = response.read().decode('utf-8')
            res_json = json.loads(res_content)
            transcript = res_json['candidates'][0]['content']['parts'][0]['text']
        return transcript.strip()

    def _transcribe_groq(self, file_name: str, file_bytes: bytes) -> str:
        import uuid
        boundary = f"----WebKitFormBoundary{uuid.uuid4().hex}"
        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        }
        
        body_parts = []
        body_parts.append(f"--{boundary}".encode('utf-8'))
        body_parts.append(b'Content-Disposition: form-data; name="model"')
        body_parts.append(b'')
        body_parts.append(b'whisper-large-v3')
        
        mime_type = "audio/wav"
        if file_name.lower().endswith(".mp3"):
            mime_type = "audio/mp3"
        elif file_name.lower().endswith(".m4a"):
            mime_type = "audio/m4a"
        elif file_name.lower().endswith(".ogg"):
            mime_type = "audio/ogg"
            
        body_parts.append(f"--{boundary}".encode('utf-8'))
        body_parts.append(f'Content-Disposition: form-data; name="file"; filename="{file_name}"'.encode('utf-8'))
        body_parts.append(f'Content-Type: {mime_type}'.encode('utf-8'))
        body_parts.append(b'')
        body_parts.append(file_bytes)
        body_parts.append(f"--{boundary}--".encode('utf-8'))
        body_parts.append(b'')
        
        body_bytes = b'\r\n'.join(body_parts)
        
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        req = urllib.request.Request(url, data=body_bytes, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=12) as response:
            res_content = response.read().decode('utf-8')
            res_json = json.loads(res_content)
            return res_json.get("text", "").strip()

    def _transcribe_mock(self, file_name: str, file_bytes: bytes) -> str:
        normalized_name = file_name.lower()
        if "tamil" in normalized_name:
            return "டெலிவரி மிகவும் தாமதம்."
        elif "hindi" in normalized_name:
            return "डिलीवरी बहुत लेट हो गई है."
        elif "tanglish" in normalized_name:
            return "Hello, delivery romba late-ah vandhuchu."
        elif "hinglish" in normalized_name:
            return "delivery bahut late ho gaya hai."
        elif "spill" in normalized_name or "packaging" in normalized_name or "leak" in normalized_name:
            return "Yes, the driver brought the food but the packaging was broken and the soup was spilled all over the bag. It is very frustrating."
        elif "charge" in normalized_name or "double" in normalized_name or "billing" in normalized_name:
            return "I checked my billing history and you charged me twice for my grocery order. I need a refund immediately."
        elif "crash" in normalized_name or "freeze" in normalized_name or "bug" in normalized_name:
            return "Every time I click checkout on the checkout screen, the app freezes and crashes. Please fix this bug."
        elif any(w in normalized_name for w in ["late", "delay", "time", "order", "delivery", "status"]):
            return "My grocery delivery is delayed by three days. Nobody is telling me when it will arrive."
        elif "rude" in normalized_name or "rider" in normalized_name or "agent" in normalized_name:
            return "Hello, I wanted to report an issue with my delivery driver. He was very rude when handing over the groceries."
        else:
            return "My delivery is late and I have been waiting for hours. Please resolve this."
