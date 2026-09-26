# AI Assist: optional and session-controlled

## What is real in this source

The app is complete as a bounded preliminary generator with AI off. The UI offers three plain choices: engines only; add a local model; or use a cloud model with a user-owned key. Provider configuration stays in the Python process, not in a project, environment file, log or browser localStorage. A one-click clear switches AI off. References expire after 30 minutes. Python cannot guarantee that an old immutable key string is securely zeroed from physical memory; no such promise is made.

The user reviews the destination and a cost estimate before a request. Unknown prices stay unknown; they are not displayed as free. Estimates use a character heuristic rather than billing-token truth. Cloud key creation/revocation must be performed on the provider's site; use a scoped project key and spending limit where available. Revoke the key there after a session. There is no OS-keychain integration in this release.

Only the fused structured brief and instruction are sent to the selected provider. Reference images are not sent. The app does not silently route to another vendor, follow redirects with a key, run returned code or let a model directly mutate a scene. AI output must be a small JSON patch, rationale and critique; permitted fields are allowlisted. The patch is regenerated and screened before being offered for user approval. Soil and cost-rate guesses are prohibited.

**The available gate is geometric, not statutory or structural.** No response earns construction approval. Model critique remains unverified commentary. There is no measured evidence that each higher tier improves designs; this requirement remains an evaluation gate, not a marketing promise.

## Local model path

Qwen3-8B and Qwen3-4B GGUF are text models under Apache-2.0, not vision models. Official Q4_K_M files were identified as approximately 5.03 GB and 2.5 GB. The source script pins their SHA-256 values from the official file pages; the 8B file also has a full commit revision. This distribution includes **neither weights nor llama.cpp binaries**.

```bash
python scripts/download_model.py --model qwen3-8b --dry-run
python scripts/download_model.py --model qwen3-8b --accept-apache-2.0
# With a separately installed official llama-server executable:
python scripts/start_local_model.py --model qwen3-8b
```

For the lighter model replace `qwen3-8b` with `qwen3-4b`, then enter `Qwen3-4B` in the AI model field. The starter binds only to `127.0.0.1:8080`, uses 4096 context tokens and CPU offload defaults. `--gpu-layers` is explicit. No speed, RAM adequacy or quality result was measured for either model. Phi-4-mini is not bundled or implemented as an automatic fallback.

The downloader opt-in, source manifest and checksum code were authored and dry-run; the multi-gigabyte download/inference was not executed. Review current official llama.cpp installation instructions rather than executing arbitrary remote installation scripts. The starter is an optional integration recipe, not proof of inference compatibility on every release.

## Cloud path

Choose Anthropic or an OpenAI-compatible endpoint; paste a session key, the model ID and optionally current prices. The Anthropic Messages adapter fixes the destination to its official API host. Other compatible endpoints require HTTPS and reject embedded credentials/query strings. Local inference permits only literal loopback HTTP addresses. Provider redirects are refused.

Official model documentation retrieved during this work listed `claude-sonnet-5`, `claude-opus-5` and `claude-fable-5`. It did not establish the requested `Fable 5.1` identifier. The app's default is Sonnet 5; the model field is editable. Availability, API behaviour and billing require an actual account test. No cloud key was supplied and no paid request was made during implementation.

OpenAI-compatible support means the chat-completions contract, **not universal compatibility with every vendor/model/Responses-only API**. Vision, streaming live critique, free-form sketch interpretation and automatic concept ranking are not implemented.

## Sources checked 2026-09-06

- Official Claude model table: https://platform.claude.com/docs/en/about-claude/models/overview
- Official Qwen model: https://huggingface.co/Qwen/Qwen3-8B-GGUF
- 8B file/hash: https://huggingface.co/Qwen/Qwen3-8B-GGUF/blob/main/Qwen3-8B-Q4_K_M.gguf
- 4B file/hash: https://huggingface.co/Qwen/Qwen3-4B-GGUF/blob/main/Qwen3-4B-Q4_K_M.gguf

These sources establish identities/licenses/file hashes, not FloorForge model benchmarks.
