import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter
from typing import Annotated

from fastapi import Body, FastAPI, HTTPException, status

from src.model import MAX_NEW_TOKENS, generate, get_model_config, load_model


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    model_id, revision = get_model_config()
    app.state.ready = False
    app.state.generating = False
    app.state.tokenizer, app.state.model = await asyncio.to_thread(
        load_model,
        model_id,
        revision,
    )
    app.state.ready = True

    yield

    app.state.ready = False


app = FastAPI(title="Tiny Inference", lifespan=lifespan)


def process_memory_mb() -> float:
    with open("/proc/self/status") as status_file:
        for line in status_file:
            if line.startswith("VmRSS:"):
                return round(int(line.split()[1]) / 1_024, 1)
    raise RuntimeError("Could not read process memory usage")


@app.get("/")
async def root() -> dict[str, str]:
    return {"message": "Tiny Inference API"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.get("/ready")
async def ready() -> dict[str, str]:
    if not app.state.ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="model is not ready",
        )
    return {"status": "ready"}


@app.post("/generate")
async def generate_text(
    prompt: Annotated[str, Body(min_length=1)],
    max_new_tokens: Annotated[int, Body(ge=1, le=MAX_NEW_TOKENS)] = 32,
) -> dict[str, str | int | float]:
    if not app.state.ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="model is not ready",
        )
    if app.state.generating:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="model is busy",
        )

    app.state.generating = True
    try:
        memory_before_mb = process_memory_mb()
        started_at = perf_counter()
        result = await asyncio.to_thread(
            generate,
            app.state.tokenizer,
            app.state.model,
            prompt,
            max_new_tokens,
        )
        generation_time_ms = round((perf_counter() - started_at) * 1_000)
        memory_after_mb = process_memory_mb()

        # PyTorch may retain allocated memory for reuse, so memory can stay high
        # after generation instead of returning to its previous value.
        return {
            **result,
            "generation_time_ms": generation_time_ms,
            "memory_before_mb": memory_before_mb,
            "memory_after_mb": memory_after_mb,
            "memory_change_mb": round(memory_after_mb - memory_before_mb, 1),
        }
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
    finally:
        app.state.generating = False
