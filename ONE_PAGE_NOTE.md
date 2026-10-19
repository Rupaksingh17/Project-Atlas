# What I Would Do With One More Week

If I had one more week to work on Project Atlas, I would focus on making its answers more dependable and its limits clearer. The current project demonstrates report search, client access checks, and safeguards, but its assessment data is fictional. It is not a substitute for licensed research or a production client portal.

## 1. Understand the evaluation failures

I would start by rerunning the 25-question evaluation and reviewing every failure. The earlier run passed 19 questions. Several factual questions and a library-count question failed, so I would check whether the information exists in the test reports, whether retrieval found the right passage, and whether the answer was judged against the right evidence. I would improve the evaluation checks so they verify the expected facts and source references, then publish the new results—including any failures—rather than presenting only the score.

## 2. Make answers easier to verify

For each factual answer, I would require a report title and page reference that support the claim. When the available reports do not contain enough evidence, the copilot should say so instead of filling the gap with a guess. I would add focused checks for conflicting figures, derived estimates, and questions about reports outside a client’s subscription.

## 3. Test the safeguards after changes

I would keep the prompt-injection and read-only SQL checks in the evaluation and rerun them whenever the chat or database code changes. I would also verify that one client cannot see another client’s reports or feedback. These checks matter because a useful answer is not acceptable if it crosses an access boundary.

## 4. Make setup reproducible

I would follow the README from a clean checkout on a second machine, then fix any missing steps. That run should cover starting the services, loading the fictional assessment data, opening the portal, and sending a question through the copilot. A fresh setup is a better check of the instructions than relying on my existing environment.

## 5. Be explicit about what production still needs

Before calling this production-ready, I would replace the demo client selector with the organization’s trusted sign-in and identity mapping, and load only reports the organization is licensed to use. I would also confirm deployment settings, secret handling, backups, and operational monitoring with the organization. Until those inputs are available, I would describe Atlas as an assessment implementation and present its fictional-data warning clearly.

That is where I would spend the extra week: on evidence, repeatable checks, and honest boundaries before adding more features.
