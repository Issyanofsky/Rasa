<div align="center">

# **Creating New Assistant**
</div>

# Topics:

  1. Upgrading Rasa.
  2. Quick code walkthrough of a basic Rasa assistant.
  3. Most-used CLI commands.

# 1. Installing/Upgarding Rasa

__Installing Rasa__ - install via the rasa site ([Rasa Instalation](https://rasa.com/docs/pro/installation/overview/))

__*note:__ if it's been a while, Update Rasa before you begin.

    pip install --upgrade rasa

check if rasa installed (on terminal):

    rasa -h

Create a new project

    rasa init

# 2. Quick code walkthrough of a basic Rasa assistant

Must files in Rasa. the minimum files needed to run Rasa, are:

  * __domain.yml__ - shows all the things the assistans knows about (the ALL things the assistans can say).
  * __config.yml__ - sets the NLU pipeline.
  * __At least one data file__ (nlu.yml, rules.yml, stories.yml)
    - nlu.yml - differant ways people may express.
    - stories.yml - show potential conversation flows
      - __intent:__ things that user may say to the assistant that be detected by the NLU.
      - __action:__ things the assistant does (if it start with utter (ex. utter_greet) its something the assistant said (reply).
    - __rules.yml:__ define rules. things that are condition (ex. if user say "goodbye", the assistant reply "goodbye" as well).

# 3. Most-used CLI commands

help - display help. list of all commands

    rasa -h 

train - traines a new model and stores it model directory (named the time it was trained)

    rasa train

shell - allow to talk to the assistant in a shell (terminal)

    rasa shell

    
