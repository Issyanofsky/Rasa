<div align="center">

# **Rasa 3 Naming Conventions (Quick Reference)**
</div>

This section lists all naming patterns that Rasa automatically recognizes for forms, validation, slot asking, deactivation, and form submission.

## 1. Slot Validation Function

Rasa automatically calls:
```php-template
validate_<slot_name>()
```
Example:
```python
def validate_pizza_size(self, value, dispatcher, tracker, domain):
    ...
```

__What it does__

Validates slot values after they are extracted.

## 2. Form Validation Class

The class __must start with__ "Validate" and end with "FormValidationAction".

Pattern
```python
class Validate<FormName>Form(FormValidationAction):
```
Example:
```python
class ValidateSimplePizzaForm(FormValidationAction):
    ...
```
__What it does__

Holds all validation methods for a form.

✅ 3. Custom Ask-Next-Slot Action

Rasa looks automatically for:

utter_ask_<slot_name>


or a custom action:

action_ask_<slot_name>

Example
utter_ask_pizza_type:
  - text: "What kind of pizza would you like?"

What it does

Controls how the bot asks for a slot.

✅ 4. Form Deactivation Action

Rasa automatically detects ONLY this exact name:

action_deactivate_loop

Example (Python)
class ActionDeactivateLoop(Action):
    def name(self): return "action_deactivate_loop"

    def run(self, dispatcher, tracker, domain):
        return [ActiveLoop(None)]

What it does

Stops the form immediately.

✅ 5. Form Submission Action (Optional)

If you want a custom submit step:

action_submit_<form_name>

Example
action_submit_simple_pizza_form

What it does

Runs after all required slots are filled (if defined in a rule).

✅ 6. Submit Rule Required Names

Rasa expects these exact event names inside a submit rule:

active_loop: null
slot_was_set:
  - requested_slot: null

What it does

Tells Rasa the form is finished.

✅ 7. Slot Mapping Naming

This is fixed and must be written exactly like this:

slot_mappings:
  <slot_name>:
    - type: from_entity
      entity: <entity_name>

Example
slot_mappings:
  pizza_size:
    - type: from_entity
      entity: pizza_size

✅ 8. Required Slots List

Inside forms:

forms:
  simple_pizza_form:
    required_slots:
      - pizza_size
      - pizza_type

What it does

Defines which questions the form must ask.

✅ 9. Event Names Used in Python

These must NOT be renamed:

Event	Purpose
ActiveLoop()	Start/stop a form
SlotSet()	Set any slot
FollowupAction()	Force next action
Form()	Internal form state
Example
return [SlotSet("pizza_size", "large")]

✅ 10. Stories & Rules Conditions

Use these EXACT keyword names:

active_loop: <form_name>
slot_was_set:
  - requested_slot: <slot_name>

Example
- rule: Submit Pizza Form
  condition:
    - active_loop: simple_pizza_form
