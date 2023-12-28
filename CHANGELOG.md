
# **Skribify v0.1.9 Release Notes**

# Changelog for Skribify Script

## Version 0.1.9

### Modifications

- **System Prompt:**
  - The system prompt text is now loaded from 'Skribify\prompt.txt' file to ensure it's dynamically changeable and not hardcoded into the script.
  - Ensured the system prompt is passed correctly to the OpenAI API call within the `Summarizer` class's `summarize` method.
  - System prompt format adjusted for clarity and readability in the bot's instructions.

- **User Instructions:**
  - Appended "\nUser Instructions: " to the end of the transcript in the `Summarizer` class to clearly delineate where user-provided instructions are expected.
  - Adjusted the handling of user instructions within the `Summarizer` class to ensure they are correctly recognized and processed following the transcript summary.

### Other Changes

- Updated version to 0.1.9 to reflect the changes made to the script.
- Minor code optimizations and refactoring for better readability and maintenance.

