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



![Integration with a Website](../images/integration_website1300.gif)
