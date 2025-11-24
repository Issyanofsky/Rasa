<div align="center">

# **Functions inside Form Validation class**
</div>

In Rasa, a validation class must inherit:
```python
from rasa_sdk.forms import FormValidationAction
```

Like this:
```python
class ValidateUserInfoForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_user_info_form"
```

Inside this class, you can override several functions.

## Below is a complete list, with explanation and examples.

### 1. required_slots() — OPTIONAL
Allows you to __dynamically decide which slots the form should ask for__.

Use this when different intents require different slots:
```python
def required_slots(self, domain, dispatcher, tracker) -> List[Text]:
    purpose = tracker.get_slot("purpose")

    base = ["user_name", "user_phone", "user_email"]

    if purpose == "meeting":
        return base + ["meeting_time"]
    return base
```

✔ Useful when different flows exist
✔ Not needed if the form has fixed slots

### 2. extract_<slot>() — OPTIONAL
Custom extraction logic for a slot.

Use when Rasa cannot extract the slot automatically.

Example:
```python
def extract_user_name(self, dispatcher, tracker, domain):
    # Try to extract from entity
    entity = next(tracker.get_latest_entity_values("user_name"), None)
    if entity:
        return {"user_name": entity}

    # Fallback: use the whole message text
    text = tracker.latest_message.get("text")
    return {"user_name": text}
```

✔ Great for name, email, phone, etc.
✔ Overrides the default entity extraction

### 3. validate_<slot>() — HIGHLY IMPORTANT
Validates a slot value.

This is where logic like email/phone/name validation lives.

Example:
```python
def validate_user_email(self, value, dispatcher, tracker, domain):
    if "@" in value and "." in value:
        return {"user_email": value}
    dispatcher.utter_message("That doesn't look like a valid email.")
    return {"user_email": None}
```

✔ Most important function in the validation class
✔ Clears invalid slot → form asks again

### 4. validate_slots() — ADVANCED / RARE
This validates the entire set of slots at once.

Use only if multiple slots depend on each other.

Example:
```python
async def validate_slots(self, slots_to_validate, dispatcher, tracker, domain):
    validated = {}
    for slot, value in slots_to_validate.items():
        validated[slot] = value
    return validated
```

Most developers never need to override this.
Use slot-by-slot validation instead.

### 5. extract_slots() — ADVANCED / RARE
Extract multiple slots at once manually.
```python
async def extract_slots(self, dispatcher, tracker, domain):
    return {
        "user_name": "something",
        "user_email": "other"
    }
```

Not commonly needed.

### 6. slot_mappings() — USEFUL
Defines how slots should be filled automatically.
```python
def slot_mappings(self):
    return {
        "user_name": [
            self.from_entity(entity="user_name"),
            self.from_text(intent=["provide_name"]),
        ],
        "user_phone": [
            self.from_entity(entity="user_phone"),
            self.from_text(),
        ]
    }
```

✔ Very powerful
✔ Controls extraction strategy
✔ Works with forms only

### 7. _should_request_slot() — ADVANCED
Tells Rasa whether it should request a slot or skip it.
```python
def _should_request_slot(self, slot_name, dispatcher, tracker, domain):
    if slot_name == "meeting_time" and tracker.get_slot("purpose") != "meeting":
        return False
    return True
```

✔ Useful for conditional slot skipping
✔ Should NOT be used for dynamic slot lists (required_slots is better)

### 8. submit() — OPTIONAL
What happens after all slots are filled and validated?

For forms before Rasa 3.0 this was required.
For Rasa 3.x, the form ends and the next action in your rule executes.

But you can still override:
```python
async def submit(self, dispatcher, tracker, domain):
    dispatcher.utter_message("Thanks! Your details were saved.")
    return []
```

### 9. run() — DO NOT OVERRIDE

Never override run() in a validation class.

Rasa handles the logic internally.
