# Hints · Done means done

## Follow one conversation
In `run_agent`, print `messages` when the loop ends, for one failing scenario. Read it as the model would. After each tool call, what was it told?

## A failure that reads as success
`except Exception: result = None` turns every tool failure into the text `null`. To the model that means nothing went wrong, so it carries on and reports success. Hand it the reason instead (`str(exc)`). It can fix a call when it knows what was wrong with it.

## No reply at all
When the model names a tool that does not exist, the loop hits `continue` without adding a message. The model sees the same conversation again and sends the same call again, forever. Tell it the tool does not exist and which ones do. Then make the loop finite anyway: `max_steps` is accepted and never used.

## Trusting the narrator
`refund_issued` is decided by looking for the word "issued" in the model's last sentence. That sentence is a claim. The tool results are the record: keep the `issue_refund` calls that succeeded, set `refund_issued` from those, and do not pass a success message on to the customer when nothing backs it up.

## A rule in a prompt is a request
The system prompt says refunds above 200 need approval, and the model refunds 2,300 anyway. A rule that has to hold goes in code, at the point where the tool is called. Check the boundary too: the policy says "above".
