# Security model

ForgeAI treats repository code as untrusted input.

Controls:

- edits are restricted to the temporary repository root
- `.git` and `.env*` paths are blocked
- oversized files and binary files are excluded from LLM context
- sandbox execution disables networking
- container memory, CPU and PID limits are enforced
- all Linux capabilities are dropped
- `no-new-privileges` is enabled
- execution has a timeout
- empty PRs are rejected
- detected secrets cause review failure

Production deployment should run the sandbox worker on a dedicated VM/node and never mount a privileged host Docker socket into an internet-facing application. For higher isolation, replace Docker with a VM or microVM runtime.
