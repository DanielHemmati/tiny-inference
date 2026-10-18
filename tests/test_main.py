import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.main import app


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.model_config = patch(
            "src.main.get_model_config",
            return_value=("model", "revision"),
        )
        self.load_model = patch(
            "src.main.load_model",
            return_value=(object(), object()),
        )
        self.model_config.start()
        self.load_model.start()
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self) -> None:
        self.client.__exit__(None, None, None)
        self.load_model.stop()
        self.model_config.stop()

    def test_health_and_readiness(self) -> None:
        self.assertEqual(self.client.get("/health").json(), {"status": "healthy"})
        self.assertEqual(self.client.get("/ready").json(), {"status": "ready"})

    def test_generates_completion(self) -> None:
        result = {
            "completion": " world",
            "prompt_tokens": 1,
            "generated_tokens": 1,
        }
        with (
            patch("src.main.generate", return_value=result),
            patch("src.main.process_memory_mb", side_effect=[300.0, 304.0]),
            patch("src.main.perf_counter", side_effect=[10.0, 10.5]),
        ):
            response = self.client.post(
                "/generate",
                json={"prompt": "Hello", "max_new_tokens": 8},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                **result,
                "tokens_per_second": 2.0,
                "memory_before_mb": 300.0,
                "memory_after_mb": 304.0,
                "memory_change_mb": 4.0,
            },
        )

    def test_rejects_request_while_busy(self) -> None:
        app.state.generating = True
        try:
            response = self.client.post("/generate", json={"prompt": "Hello"})
        finally:
            app.state.generating = False

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"detail": "model is busy"})

    def test_validates_max_new_tokens(self) -> None:
        response = self.client.post(
            "/generate",
            json={"prompt": "Hello", "max_new_tokens": 129},
        )
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
