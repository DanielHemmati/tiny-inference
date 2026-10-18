import argparse
import os
from time import perf_counter
from typing import cast

import torch
from huggingface_hub import snapshot_download
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    LlamaForCausalLM,
    PreTrainedTokenizerBase,
)
from transformers.generation.streamers import BaseStreamer

CONTEXT_LENGTH = 2_048
MAX_NEW_TOKENS = 128


class FirstTokenTimingStreamer(BaseStreamer):
    def __init__(self) -> None:
        self.started_at = perf_counter()
        self.received_prompt = False
        self.time_to_first_token_ms: float | None = None

    def put(self, value: torch.Tensor) -> None:
        if not self.received_prompt:
            self.received_prompt = True
            return
        if self.time_to_first_token_ms is None:
            self.time_to_first_token_ms = round(
                (perf_counter() - self.started_at) * 1_000,
                2,
            )

    def end(self) -> None:
        pass


def get_model_config() -> tuple[str, str]:
    model_id = os.getenv("MODEL_ID", "").strip()
    revision = os.getenv("MODEL_REVISION", "").strip()
    if not model_id or not revision:
        raise RuntimeError("MODEL_ID and MODEL_REVISION must be set")
    return model_id, revision


def load_model(
    model_id: str,
    revision: str,
) -> tuple[PreTrainedTokenizerBase, LlamaForCausalLM]:
    tokenizer = cast(
        PreTrainedTokenizerBase,
        AutoTokenizer.from_pretrained(model_id, revision=revision),
    )
    model = cast(
        LlamaForCausalLM,
        AutoModelForCausalLM.from_pretrained(
            model_id,
            revision=revision,
            dtype=torch.float32,
        ),
    )
    model.to("cpu")  # pyright: ignore[reportArgumentType]
    model.eval()
    return tokenizer, model


def generate(
    tokenizer: PreTrainedTokenizerBase,
    model: LlamaForCausalLM,
    prompt: str,
    max_new_tokens: int,
) -> dict[str, str | int | float]:
    if not prompt:
        raise ValueError("prompt must not be empty")
    if not 1 <= max_new_tokens <= MAX_NEW_TOKENS:
        raise ValueError(f"max_new_tokens must be between 1 and {MAX_NEW_TOKENS}")

    timing_streamer = FirstTokenTimingStreamer()
    inputs = tokenizer(prompt, return_tensors="pt")
    prompt_tokens = int(inputs["input_ids"].shape[-1])
    if prompt_tokens + max_new_tokens > CONTEXT_LENGTH:
        raise ValueError(
            f"prompt and completion must fit within {CONTEXT_LENGTH} tokens"
        )
    with torch.inference_mode():
        output = model.generate(  # pyright: ignore[reportAttributeAccessIssue]
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
            streamer=timing_streamer,
        )

    if timing_streamer.time_to_first_token_ms is None:
        raise RuntimeError("Model generation did not emit a token")

    generated_ids = output[0, prompt_tokens:]
    return {
        "completion": cast(
            str,
            tokenizer.decode(generated_ids, skip_special_tokens=True),
        ),
        "prompt_tokens": prompt_tokens,
        "generated_tokens": int(generated_ids.shape[-1]),
        "time_to_first_token_ms": timing_streamer.time_to_first_token_ms,
    }


def prefetch(model_id: str, revision: str) -> None:
    snapshot_download(repo_id=model_id, revision=revision)


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage the configured language model")
    parser.add_argument(
        "--prefetch",
        action="store_true",
        help="download the pinned model snapshot and exit",
    )
    args = parser.parse_args()

    if not args.prefetch:
        parser.error("an action is required; use --prefetch")

    model_id, revision = get_model_config()
    prefetch(model_id, revision)
    print(f"Prefetched {model_id} at revision {revision}")


if __name__ == "__main__":
    main()
