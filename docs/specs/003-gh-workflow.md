---
status: in-progress
---

# GitHub Actions Deployment with systemd

## Goal

Deploy the Python application to the existing Ubuntu server over SSH. GitHub Actions updates the repository, installs locked dependencies with `uv`, downloads the pinned test model into a persistent cache, and restarts the application through `systemd`.

## Scope and Assumptions

- The server has already been provisioned by Terraform and initialized by Ansible.
- The application entry point is the `app` object in `src/main.py`, served with Uvicorn as `src.main:app`.
- Python dependencies are declared in `pyproject.toml` and locked in `uv.lock`.
- Deployments target the `main` branch and can also be started manually from GitHub Actions.
- GitHub-hosted runners join the tailnet for the duration of the deployment and
  reach the server through its private Tailscale identity; public SSH is not
  required.
- The application checkout is `/opt/tiny-inference` and is owned by a non-root `tiny-inference` user.
- The service runs as the `tiny-inference` user with one application worker and one in-memory model instance.
- Brief downtime while systemd restarts the application is acceptable.
- Docker and Docker Compose are not part of this version.

## Model Configuration

- Test model: `HuggingFaceTB/SmolLM-135M`.
- Model revision: `1d461723eec654e65efdc40cf49301c89c0c92f4`.
- The model is a base text-completion model, not an instruction-tuned chat model. The API and tests must treat its output as prompt completion.
- Run inference on CPU using PyTorch and `transformers`; do not require vLLM, CUDA, ROCm, or `bitsandbytes`.
- Use float32 initially. Other dtypes or quantized formats may be evaluated later only after confirming ARM64 CPU compatibility and measuring performance.
- Limit generation concurrency to one request initially. Additional requests should be queued or rejected with a clear busy response rather than starting concurrent generations without a limit.
- Bound prompt length and generated tokens within the model's 2,048-token context window.
- Store Hugging Face data under `/var/lib/tiny-inference/huggingface`, owned by `tiny-inference`, so downloads survive deployments and service restarts.
- Set `HF_HOME` to the persistent cache path and pass both the model ID and pinned revision through the server-side environment file.
- Prefetch the pinned model revision during deployment before restarting the running service. The application should then load the files from the same cache.
- No Hugging Face token is required for this public model. If a future gated model requires one, store it only in the server-side environment file.

## Requirements

- Add a workflow at `.github/workflows/deploy.yml`.
- Trigger deployment on pushes to `main` and through `workflow_dispatch`.
- Use SSH keys only; password authentication must not be required.
- Connect the runner to the tailnet with the official Tailscale GitHub Action,
  a dedicated OAuth client, and an ephemeral `tag:ci` node identity.
- Limit the OAuth client to creating auth keys for `tag:ci`, and limit tailnet
  policy so `tag:ci` can reach only the deployment server on TCP port 22.
- Use the server's Tailscale MagicDNS name or Tailscale IP as `DEPLOY_HOST`.
- Verify the server host key instead of disabling `StrictHostKeyChecking`.
- Clone the repository when `/opt/tiny-inference/.git` does not exist.
- On later runs, fetch `main` and update only with a fast-forward operation so unexpected server-side changes cause deployment to fail instead of being overwritten.
- Run `uv sync --frozen` after updating the source.
- Run a stable application command that downloads the configured model and revision into `HF_HOME` before restarting the service.
- Run the application through systemd so it survives the SSH session and restarts after a failure or server reboot.
- Prevent overlapping deployments with a GitHub Actions concurrency group.
- Do not print, commit, or persist GitHub Actions secrets in workflow logs or tracked files.

## systemd Runtime

- Ansible creates the `tiny-inference` system user and required application and cache directories.
- Ansible installs a `tiny-inference.service` unit owned by root.
- The unit uses:
  - `User=tiny-inference`;
  - `WorkingDirectory=/opt/tiny-inference`;
  - `EnvironmentFile=/etc/tiny-inference.env`;
  - the virtual environment's Uvicorn executable for `ExecStart`;
  - `Restart=on-failure` with a short restart delay;
  - startup after networking is available.
- `/etc/tiny-inference.env` is root-owned, is not committed, and defines at least `HF_HOME`, `MODEL_ID`, and `MODEL_REVISION`.
- The service starts only one worker to avoid loading duplicate model instances and oversubscribing the CPU.
- The readiness endpoint must remain unhealthy until the model and tokenizer have loaded successfully.
- Application logs are written to the systemd journal and inspected with `journalctl -u tiny-inference`.

## Authentication and Secrets

Configure these GitHub Actions repository secrets:

- `TS_OAUTH_CLIENT_ID`: ID of a dedicated Tailscale OAuth client permitted to
  create auth keys only for `tag:ci`.
- `TS_OAUTH_SECRET`: secret for the dedicated Tailscale OAuth client.
- `DEPLOY_HOST`: server Tailscale MagicDNS name or Tailscale IP.
- `DEPLOY_USER`: SSH user used by the workflow.
- `DEPLOY_SSH_KEY`: private key authorized for `DEPLOY_USER` on the server.
- `DEPLOY_KNOWN_HOSTS`: pinned `known_hosts` entry for `DEPLOY_HOST`, collected from a trusted source.
- `TELEGRAM_BOT_TOKEN`: API token issued by Telegram's `@BotFather` for the
  deployment notification bot.
- `TELEGRAM_CHAT_ID`: numeric ID of the user, group, or channel that receives
  successful deployment notifications. Add the bot to that chat before using
  its ID.

The tailnet policy must define `tag:ci` and grant it access only to the
deployment server's normal SSH service on TCP port 22. The OAuth client must
not be reused from Terraform provisioning and must not have broader API scopes
or tags than the workflow requires. Tailscale authenticates and routes the
runner to the private server; it does not replace SSH user authentication or
SSH host-key verification.

Repository access from the server uses one of these approaches:

1. For a public repository, clone its read-only HTTPS URL without credentials.
2. For a private repository, install a separate read-only GitHub deploy key on the server during Ansible setup. Do not reuse the server-login key or enable SSH agent forwarding.

Any runtime secrets belong in `/etc/tiny-inference.env`. They must not be committed, passed on command lines, or copied from GitHub Actions during every deployment.

## Implementation Plan

1. Define the Python project metadata, committed lock file, and application start command.
2. Add `transformers`, PyTorch with ARM64 support, and required model dependencies to the locked project dependencies.
3. Add an application command that prefetches `MODEL_ID` at `MODEL_REVISION` into `HF_HOME` and exits unsuccessfully if the download or validation fails.
4. Configure the application to load the same pinned model from the persistent cache on startup and serve only one generation at a time.
5. Extend the Ansible setup to:
   - create the `tiny-inference` user;
   - create `/opt/tiny-inference` and `/var/lib/tiny-inference/huggingface` with the correct ownership;
   - create the root-owned environment file;
   - install and enable `tiny-inference.service`;
   - grant `DEPLOY_USER` permission to restart and inspect only this service without unrestricted passwordless sudo.
6. Create a dedicated Tailscale OAuth client that can create ephemeral nodes
   carrying only `tag:ci`, and add a tailnet policy rule allowing that tag to
   reach only the deployment server on TCP port 22.
7. Add `.github/workflows/deploy.yml` with push and manual triggers,
   `contents: read` permission, deployment concurrency, and SSH client setup.
8. Before SSH setup, use the official Tailscale GitHub Action to join the
   runner to the tailnet with `TS_OAUTH_CLIENT_ID`, `TS_OAUTH_SECRET`, and
   `tag:ci`, then verify reachability to `DEPLOY_HOST` with `tailscale ping`.
9. In the workflow, create an ephemeral SSH configuration and verify the server using the pinned host key.
10. Execute an idempotent remote deployment that:
   - clones the repository into `/opt/tiny-inference` when absent;
   - otherwise fetches `origin/main`, checks out `main`, and fast-forwards to the fetched commit;
   - runs `uv sync --frozen` as `tiny-inference`;
   - prefetches the pinned model into the persistent cache as `tiny-inference`;
   - restarts `tiny-inference.service` only after all previous steps succeed.
11. Wait for the readiness endpoint after restart and fail the workflow if the model-backed application does not become healthy within a defined startup timeout.
12. Record the deployed Git commit and model revision in the workflow summary or application logs.

## Failure and Rollback Behavior

- A failed Tailscale connection or reachability check, clone, fast-forward,
  dependency sync, model prefetch, service restart, or readiness check must
  fail the workflow.
- The running service must not be restarted when source update, dependency installation, or model prefetch fails.
- A failed model download must not remove a previously cached usable revision.
- For the first version, rollback is manual: check out a known-good commit, run `uv sync --frozen`, prefetch its configured model revision, restart the service, and verify readiness.
- Automated rollback and zero-downtime deployment are out of scope.

## Acceptance Criteria

- A developer can still connect manually with `make ssh`.
- A GitHub-hosted runner joins as an ephemeral `tag:ci` node, reaches the
  server over Tailscale, and is removed from the tailnet after the job.
- Tailnet policy allows `tag:ci` to reach the deployment server on TCP port 22
  and does not grant the runner general tailnet access.
- The deployment succeeds without exposing public TCP port 22 on the server.
- The first successful workflow run clones the repository, installs locked dependencies, downloads the pinned SmolLM model, starts the systemd service, and passes its readiness check.
- The model cache is stored outside the Git checkout and survives subsequent deployments and service restarts.
- A later push to `main` fast-forwards the checkout and restarts the service without downloading unchanged model files again.
- A manual workflow run deploys the current `main` revision.
- The application remains running after the GitHub Actions SSH session ends and after a server reboot.
- Only one application worker and model instance run by default.
- A bad dependency lock, divergent checkout, failed model download, failed process start, or failed readiness check produces a failed workflow rather than a false success.
- SSH host verification is enabled, and no private key, OAuth secret, token,
  runtime environment file, model weight, or generated SSH file is committed
  to Git.
- The deployment does not require Docker, vLLM, CUDA, ROCm, or GPU hardware.

## Out of Scope

- Building the FastAPI inference API itself.
- Instruction/chat behavior from the base SmolLM model.
- GPU infrastructure or GPU-specific inference dependencies.
- Multiple model replicas or concurrent generation workers.
- Preview environments, blue-green deployments, autoscaling, or zero-downtime releases.
- Docker and Docker Compose deployment.
