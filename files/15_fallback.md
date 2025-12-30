<div align="center">

# **FallBack**
</div>

A __fallback__ is what your assistant does when it’s not confident about what the user wants.

Example:
```makefile
User: blablabla
Bot: Sorry, I didn’t understand that. Can you rephrase?
```

This happens when:
* Intent confidence is too low
* The user message is confusing
* The message doesn’t match any intent
* The conversation goes off-script
* The user keeps giving invalid answers

## Types of fallbacks in Rasa 3+
There are 3 main fallback mechanisms you should know:
1. NLU Fallback (low intent confidence) - “I don’t understand what you said”
2. Rule-based fallback (conversation-level) - “I don’t know what to do next”
3. Custom fallback actions (advanced/extreme cases) - “Special business logic for edge cases”

__*Note:__ You usually use __all of them together__.

### How They Work Together (Important)
```pgsql
A typical Rasa 3+ setup looks like this:

User input
   ↓
NLU confidence check
   ↓
nlu_fallback (if low confidence)
   ↓
Dialogue policies
   ↓
core fallback (if no action fits)
   ↓
custom fallback logic (if needed)
```

__Best practice stack__
|-------------------|-------------------------------------------------------------|
|        Layer	    |                        Purpose                              |
|-------------------|-------------------------------------------------------------|
| NLU fallback	    | Catch unclear messages                                      |
| Rule fallback	    | Catch broken conversation flow                              |
| Custom fallback	  | Handle business logic & recovery                            |
|-------------------|-------------------------------------------------------------|

⚠️ __Common Mistakes__
❌ Relying only on NLU fallback
❌ No core fallback → bot crashes conversationally
❌ One generic fallback message everywhere
❌ No tracking of fallback frequency

### 1. NLU Fallback (low intent confidence)

This fallback happens during intent classification, before dialogue management.
If Rasa’s NLU model is not confident enough about the user’s intent, it triggers a fallback intent.

__How it works (internals)__
* The intent classifier outputs confidence scores:
```json
{
  "intent": "greet",
  "confidence": 0.38
}
```
* If confidence < threshold, Rasa predicts:
```makefile
intent: nlu_fallback
```

__How to configure it (Rasa 3+)__
In config.yml
```yaml
pipeline:
  - name: WhitespaceTokenizer
  - name: DIETClassifier
    confidence_threshold: 0.4
```
or explicitly:
```yaml
pipeline:
  - name: FallbackClassifier
    threshold: 0.4
```
__What happens when it triggers?__
* Intent becomes nlu_fallback
* No entities are trusted
* Dialogue continues like any other intent

__Typical rule for NLU fallback__
```yaml
rules:
- rule: Handle NLU fallback
  steps:
  - intent: nlu_fallback
  - action: utter_nlu_fallback
```
__Example response__
```yaml
responses:
  utter_nlu_fallback:
    - text: "Sorry, I didn’t quite understand that. Can you rephrase?"
```
__When to use it__

✅ User types unclear text
✅ Typos, slang, random input
✅ First line of defense

❌ Doesn’t help if the intent is correct but the __conversation flow is broken__

### 2. Rule-Based Fallback (Conversation-Level Fallback)

This fallback happens when:
```makefile
Rasa understands the intent, but no policy can decide what action to take next
```
This is handled by __FallbackPolicy__.

__How it works (internals)__
* Rasa policies predict the next action
* Each action has a confidence
* If __highest confidence < threshold__, fallback triggers

__Configuration (Rasa 3+)__
In config.yml
```yaml
policies:
  - name: RulePolicy
    core_fallback_threshold: 0.3
    core_fallback_action_name: "action_default_fallback"
```
__Default behavior__

By default:
* Action: action_default_fallback
* It sends a generic message
* Conversation may reset or wait

__Custom rule-based fallback__
```yaml
rules:
- rule: Core fallback
  steps:
  - action: action_default_fallback
```

__Example custom response__
```yaml
responses:
  utter_default:
    - text: "I’m not sure how to help with that yet."
```
__When it triggers__

✅ Intent is recognized
✅ Entities extracted
❌ Dialogue state doesn’t match any rule or story

Example:
```vbnet
User: book a flight
Bot: sure, where from?
User: pizza
```

NLU works, but dialogue logic breaks → __core fallback__

__When to use it__
✅ Safety net for broken conversation paths
✅ Missing stories or rules
❌ Not good for handling very specific logic

### 3. Custom Fallback Actions (Advanced / Extreme Cases)

A custom Python action that decides dynamically what to do when fallback happens.
This is not automatic — you explicitly call it.

__Why use custom fallback actions?__
Because sometimes:
* You want to log fallback data
* You want different responses depending on context
* You want to escalate to human
* You want to retry intent prediction
* You want domain-specific recovery logic

__Example custom fallback action__
```python
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

class ActionCustomFallback(Action):
    def name(self):
        return "action_custom_fallback"

    def run(self, dispatcher, tracker, domain):
        last_intent = tracker.latest_message["intent"].get("name")

        if last_intent == "nlu_fallback":
            dispatcher.utter_message(
                text="Could you say that in a different way?"
            )
        else:
            dispatcher.utter_message(
                text="I’m not sure what to do next. Let’s start over."
            )

        return []
```

__Hook it into rules__
```yaml
rules:
- rule: Custom fallback
  steps:
  - action: action_custom_fallback
```
__Advanced use cases__
✅ Multi-step clarification
✅ Context-aware retry
✅ Language detection failures
✅ Escalation after N failures
✅ Analytics and monitoring

