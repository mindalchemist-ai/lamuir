# Scoring text against word lists

The task description inside <task_instructions> takes priority over this card: where it gives a different formula, input, setting or convention, follow the task description.

When text is scored against word lists, lowercase and split on word characters (for example `re.findall(r"[a-z']+", text.lower())`), so punctuation attached to a word does not stop a match.
