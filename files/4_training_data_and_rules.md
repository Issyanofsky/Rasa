<div align="center">

# **Training Data & Rules**
</div>

# Topics:

  1. What is training data for a Rasa assistant?
  2. Stories.
  3. Rules.
  4. Intens (examples)
     - Where to start if you already have data.
     - Where to start if you don't already have data.

# 1. What is training data for a Rasa assistant?

What is "__data__" for Rasa project?
  * The text data used to pretrain any models or features you're using (e.g. language models, wrod embaddings, etc,)
  * User-generated text - what the user usualy type (ex. what are the differante ways your customers say "hello").
  * Pattens of conversations - pattern that happen in a conversation (e.g.if a user say "hello" to the assistanse, what the assistant will replay).

Examples where we can get data:
  - Customer support logs (assuming data collection & rules is covered in the privacy policy).
  - User conversation with our assistant (__NOTE__ this is the __best__ place to find data - from users interacting with  our asistsnt).

#  2. Stories

Stories - training data to teach the asistant what it should do next.

If you have a storie discribing the same pattern the conversation went. the pattern that used in the storie will be triggered.
It, however, you have a pattern of conversation the assistant did'nt seen before, it will look at all stories and guess what it most likely fit (which storie). if it not sure which storie fit (under a trash level we set) it will start a pallback.

__how to set patterns (stories):__
  - __If you have conversation data__:
    - if you have conversations that you trying to model, start with those patterns.
  - __If you dont have conversation data.__ generate your own conversational patterns:
    - It's easiest to use __interactive learning__ to create stories - command line interface tool to do interactive learning where you pretend to be both the assistant and the user having conversations.
    - Start with common flows, "happy paths" - conversation you want your user have every time.
    - Then add common errors/digressions.
  - __Once your model is trained__:
    - Add more data from user conversations.
   
__how a Stories look like__

![Stories](../images/stories401.gif)

    stories:
      - story: happy path # Define the story name (any desctiption name)
        steps:
          - intent: greet
          - action: utter_greet
          - intent: mood_great
          - action: utter_happy
In the pattern of the conversation (under steps)

  __intent__ - things that user say that the mechine model has detected.
  
  __action__ - things that the assistant do.

__OR statements__

![Or statements](../images/stories402.gif)
