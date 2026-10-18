---
status: complete
---

# SmolLM MVP

Serve `HuggingFaceTB/SmolLM-135M` as a single-request CPU text-completion API.

## Phase 1: Runtime dependencies

- Add and lock PyTorch and Transformers with Linux ARM64/Python 3.13 support.
- Verify imports locally.

## Phase 2: Model runtime

- Add a module that loads the pinned model and tokenizer from environment configuration.
- Add a prefetch command for the persistent Hugging Face cache.
- Generate deterministic completions with `torch.inference_mode()`.
- Enforce the 2,048-token context limit and a 128-token output maximum.

## Phase 3: API

- Load one model instance during FastAPI startup.
- Add `GET /health`, `GET /ready`, and `POST /generate`.
- Accept `prompt` and `max_new_tokens`; return completion and token counts.
- Permit one active generation and return a clear busy response otherwise.

## Phase 4: Deployment

- Prefetch the pinned model before restarting systemd.
- Check `/ready` instead of `/` during deployment.
- Test one prompt against the deployed service.

## Phase 5: Per-request metrics

- Return generation duration and process memory before, after, and change.
- Document that PyTorch may retain memory for reuse after generation.

## MVP boundaries

CPU float32, one worker, greedy decoding, no streaming, batching, chat format, GPU, or OpenAI compatibility.
