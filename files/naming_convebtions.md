<div align="center">

# **Rasa 3 Naming Conventions (Quick Reference)**
</div>

This section lists all naming patterns that Rasa automatically recognizes for forms, validation, slot asking, deactivation, and form submission.

## 1. Form Validation Class Name

Rasa automatically loads validation classes ONLY if they follow this pattern:
```kotlin
class Validation<FormName>(FormValidationAction):
```
Example"
```python
class ValidationSimplePizzaForm(FormValidationAction):
    ...
```

🔹 Why?
Rasa scans for classes starting with Validation to automatically attach validation to the form.

## 2. Slot Validation Functions

Inside the validation class, each slot must follow this naming pattern:
```php-template
validate_<slot_name>(...)
```
Example:
```python
def validate_pizza_size(self, slot_value, dispatcher, tracker, domain):
    ...
```

🔹 Rasa automatically calls this when a value is mapped to the slot.

## 3. Automatic Slot Asking

Rasa looks for these names when asking for the next slot inside a __Form__:

Default ask action (utterance):
```php-template
utter_ask_<slot_name>
```
Custom action ask handler:
```php-template
action_ask_<slot_name>
```
Example:
```yaml
utter_ask_pizza_type:
  - text: "What pizza type would you like?"
```

🔹 Used every time the form requests a slot value.

__* Note:__
if utter_ask_<slot_name> __exists, Rasa will not trigger__ the action_ask_<slot_name>.
It follow thos priority:
    1. If utter_ask_<slot_name> __exists → use it__
    2. Else if action_ask_<slot_name> __exists → use it__
    3. Else → Rasa uses a fallback, like “What is pizza_type?

## 4. required_slots

Inside the forms section of your domain.yml, you list the slots your form must fill:
```yaml
forms:
  simple_pizza_form:
    required_slots:
      - pizza_size
      - pizza_type
```
What this means:

* The form needs two pieces of information from the user:
    1. pizza_size
    2. pizza_type

* Until both are filled, the form keeps asking questions.

__*Note:__ The order you list them in controls the order of the questions.

## 5. Form Deactivation (stop the form early)

This action name is fixed and must be exactly, Rasa specifically looks for this exact name when stopping a form.:
```nginx
action_deactivate_loop
```
This action __Stop the form. It should no longer ask for slots__ (There is no active form anymore. Turn the form off).

Example:
```python
from rasa_sdk import Action
from rasa_sdk.events import ActiveLoop

class ActionDeactivateLoop(Action):
    def name(self):
        return "action_deactivate_loop"

    def run(self, dispatcher, tracker, domain):
        # This stops the form
        return [ActiveLoop(None)]
```

## 6. Submit Rule Required Names 

When the Form is finishes to submit the form, Rasa expects these __exact keys__ when a form finishes:
```yaml
active_loop: null
slot_was_set:
  - requested_slot: null
```
What they mean:

__1.__ active_loop: null
    * Tells Rasa: “__No form is active anymore__”.
    * Essentially, it __turns off the form__ .
__2.__ slot_was_set:
    * Contains requested_slot: null
    * Tells Rasa: “__We are not asking for any more slots__”
    * It clears the requested_slot that the form was waiting for.
Both are mandatory; if you forget them, the form might keep running or not submit properly.
