# Voice Intelligence & Decision Support Business Rules

This document details the analytical heuristics, weights, classifications, and business rules governing the Multilingual Voice Intelligence & Decision Intelligence systems in **InsightAI**.

---

## 1. Emotion Classification Rules

Emotion detection analyzes English-translated transcripts to identify the primary emotional driver of the customer. Heuristic classification scans specific lexical vectors:

* **Angry**: Triggered by high-severity complaints and explicit dissatisfaction terms.
  * *Keywords*: "angry", "terrible", "worst", "unacceptable", "furious", "hate", "useless", "rubbish", "horrible", "awful", "stupid", "idiot"
* **Urgent**: Triggered by immediate resolution demands or repeated financial double billing.
  * *Keywords*: "immediately", "quick", "asap", "urgent", "urgently", "twice", "double charge", "refund", "stuck", "block", "emergency"
* **Frustrated**: Triggered by processing delays, software friction, or repetitive crashes.
  * *Keywords*: "frustrated", "frustrating", "slow", "wait", "delay", "delayed", "again", "crashed", "crashes", "freeze", "freezes", "bug", "broken"
* **Satisfied**: Triggered by positive reinforcement, polite drivers, or fast order deliveries.
  * *Keywords*: "good", "great", "excellent", "satisfied", "thank you", "nice", "fast", "love", "perfect", "happy", "awesome", "wonderful", "superb"
* **Calm**: Default state when no strong emotional vectors are detected in the transcript.

---

## 2. Priority Auto-Scoring Rules

Every voice complaint calculates a numeric **Priority Score** (0-100) using sentiment, churn risk, business impact, and emotional parameters:

$$\text{Priority Score} = \text{Severity Weight} + (\text{Business Impact} \times 0.35) + (\text{Churn Risk \%} \times 0.35) + \text{Emotion Modifier}$$

### Inputs and Weights:
1. **Severity Weight**:
   * `Critical`: 40 points
   * `High`: 30 points
   * `Medium`: 20 points
   * `Low`: 10 points
2. **Business Impact Score**: Scaling contribution of 35% of the 0-100 business impact score.
3. **Churn Risk Percent**: Scaling contribution of 35% of the 0-99% churn risk probability.
4. **Emotion Modifier**:
   * `Angry`: +12 points
   * `Urgent`: +10 points
   * `Frustrated`: +6 points
   * `Satisfied`: -15 points
   * `Calm`: +0 points

*Note: The final score is mathematically clamped between 0 and 100.*

### Priority Levels:
* **Low**: 0 - 30
* **Medium**: 31 - 60
* **High**: 61 - 80
* **Critical**: 81 - 100

---

## 3. Voice Risk Level Rules

The **Voice Risk Level** evaluates operational liability by combining retention risk, financial exposure, priority criticality, and sentiment indicators:

$$\text{Risk Score} = (\text{Churn Risk \%} \times 0.30) + (\text{Business Impact} \times 0.30) + (\text{Priority Score} \times 0.20) + \text{Sentiment Bonus} + \text{Emotion Bonus}$$

### Inputs and Offsets:
1. **Sentiment Bonus**:
   * `Negative`: +15 points
   * `Neutral`: +5 points
   * `Positive`: +0 points
2. **Emotion Bonus**:
   * `Angry` / `Urgent`: +10 points
   * `Frustrated`: +5 points
   * `Satisfied`: -10 points
   * `Calm`: +0 points

### Risk Level Ranges:
* **Low Risk**: Risk Score < 35
* **Medium Risk**: 35 &le; Risk Score < 60
* **High Risk**: 60 &le; Risk Score < 80
* **Critical Risk**: Risk Score &ge; 80

---

## 4. Executive Alert Levels

Real-time alert level triggers evaluate critical threshold crossovers to notify management instantly:

* **Critical Alert**: Triggered if **Priority Score > 80** OR **Churn Risk > 75%** OR **Business Impact Score > 80**.
* **Warning Alert**: Triggered if **Priority Score > 60** OR **Churn Risk > 50%** (and not Critical).
* **Normal Alert**: Triggered in all other standard operational states.

---

## 5. Voice Business Health Score

The **Voice Business Health Score** (0-100) measures aggregate customer loyalty and system resilience over all processed voice records:

$$\text{Voice Health Score} = 100 - \left[ (\overline{\text{Churn Risk}} \times 0.3) + (\overline{\text{Business Impact}} \times 0.3) + ((100 - \text{CSI}) \times 0.2) + (\overline{\text{Priority Score}} \times 0.1) \right]$$

### Metrics Explained:
* $\overline{\text{Churn Risk}}$: Mean churn probability (%) of the analyzed voice feedback.
* $\overline{\text{Business Impact}}$: Mean business impact index (0-100).
* $\text{CSI}$: Mapped Customer Satisfaction Index (%) computed from ratings or sentiments.
* $\overline{\text{Priority Score}}$: Mean calculated priority metric.

---

## 6. Business Impact Explainability Rules

Impact explanations are generated using structured templates mapping categories to underlying corporate consequences:

* **Delivery**: *"Repeated delivery delays increase customer dissatisfaction, raise churn probability, and may negatively affect customer retention and brand reputation."*
* **Billing**: *"Payment issues and double charges damage customer trust, trigger high-volume support tickets, and can lead to chargebacks or financial disputes."*
* **App Bug**: *"Application crashes and checkout failures block conversion funnels, directly reducing sales revenue and causing immediate user drop-off."*
* **Staff/Support**: *"Substandard customer support experiences increase support resolution time, lower brand loyalty, and amplify negative word-of-mouth."*
* **Other**: *"Operational friction points degrade overall service experience and reduce user lifetime value."*
