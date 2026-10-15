# tiny-inference

A small inference engineering lab for learning how LLM inference works on a single GPU.

The goal is not to build a production platform. The goal is to run a small model, expose it through an API, measure what happens, change one thing at a time, and document what we learn.

## Goals

- Run a small open model on a single hetzner using normal CPU and then move to RunPod for GPU.
- Serve it through an OpenAI-compatible API.
- Send requests from a simple client.
- Observe latency, throughput, token generation, GPU memory, and utilization.
- Experiment with a few inference concepts such as concurrency, batching, KV cache, context length, and quantization.
- Document results and lessons in the X/linkedin/Youtube.
- use smlLM-135M model from huggingface: <https://huggingface.co/HuggingFaceTB/SmolLM-135M>

## Non-goals

For now, do not add:

- Kubernetes
- multi-node inference
- multi-GPU inference
- autoscaling
- load balancers
- complex CI/CD
- production authentication
- service meshes
- distributed monitoring
