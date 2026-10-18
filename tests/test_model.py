import os
import unittest
from typing import Protocol, cast
from unittest.mock import patch

import torch

from src.model import CONTEXT_LENGTH, generate, get_model_config


class Streamer(Protocol):
    def put(self, value: torch.Tensor) -> None: ...

    def end(self) -> None: ...


class FakeTokenizer:
    eos_token_id = 0

    def __init__(self, prompt_tokens: int = 2) -> None:
        self.prompt_tokens = prompt_tokens

    def __call__(self, prompt: str, return_tensors: str) -> dict[str, torch.Tensor]:
        return {"input_ids": torch.arange(self.prompt_tokens).unsqueeze(0)}

    def decode(self, token_ids: torch.Tensor, skip_special_tokens: bool) -> str:
        return "completion"


class FakeModel:
    inference_mode_enabled = False

    def generate(self, input_ids: torch.Tensor, **kwargs: object) -> torch.Tensor:
        self.inference_mode_enabled = not torch.is_grad_enabled()
        generated = torch.tensor([[10, 11]])
        streamer = cast(Streamer, kwargs["streamer"])
        streamer.put(input_ids)
        streamer.put(generated[:, 0])
        streamer.end()
        return torch.cat((input_ids, generated), dim=1)


class ModelConfigTests(unittest.TestCase):
    def test_reads_required_environment(self) -> None:
        environment = {"MODEL_ID": "model", "MODEL_REVISION": "revision"}
        with patch.dict(os.environ, environment, clear=True):
            self.assertEqual(
                get_model_config(),
                ("model", "revision"),
            )

    def test_rejects_missing_environment(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "must be set"):
                get_model_config()


class ModelRuntimeTests(unittest.TestCase):
    def test_generates_only_completion_in_inference_mode(self) -> None:
        model = FakeModel()
        with patch("src.model.perf_counter", side_effect=[10.0, 10.25]):
            result = generate(FakeTokenizer(), model, "A prompt", max_new_tokens=2)

        self.assertEqual(result["completion"], "completion")
        self.assertEqual(result["prompt_tokens"], 2)
        self.assertEqual(result["generated_tokens"], 2)
        self.assertEqual(result["time_to_first_token_ms"], 250.0)
        self.assertTrue(model.inference_mode_enabled)

    def test_rejects_more_than_128_new_tokens(self) -> None:
        with self.assertRaisesRegex(ValueError, "between 1 and 128"):
            generate(FakeTokenizer(), FakeModel(), "A prompt", max_new_tokens=129)

    def test_rejects_requests_larger_than_context(self) -> None:
        with self.assertRaisesRegex(ValueError, "fit within 2048 tokens"):
            generate(
                FakeTokenizer(CONTEXT_LENGTH),
                FakeModel(),
                "A prompt",
                max_new_tokens=1,
            )


if __name__ == "__main__":
    unittest.main()
