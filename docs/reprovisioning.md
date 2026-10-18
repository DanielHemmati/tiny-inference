# Reprovisioning after `make destroy`

`make destroy` deletes the server. The next `make apply` creates a new server
with a new SSH host key, even though its Tailscale hostname remains
`tiny-inference`.

After the new server is available, update the GitHub Actions repository secret
`DEPLOY_KNOWN_HOSTS`. The deploy workflow pins this key and will reject the new
server until the secret is updated. The other deployment secrets do not need to
be changed unless their credentials or settings have also changed.

## Recreate the server and update the secret

1. Recreate the server:

   ```bash
   make apply
   ```

2. If the old server key is still in the local SSH `known_hosts` file, remove
   it:

   ```bash
   ssh-keygen -R tiny-inference
   ```

3. Configure the replacement server:

   ```bash
   make configure
   ```

4. Get the new ED25519 host-key entry:

   ```bash
   ssh-keyscan -t ed25519 tiny-inference 2>/dev/null
   ```

5. Before trusting it, compare its fingerprint with the fingerprint shown from
   a trusted server console:

   ```bash
   ssh-keyscan -t ed25519 tiny-inference 2>/dev/null | ssh-keygen -lf -
   ```

   On the server console, run:

   ```bash
   sudo ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
   ```

   The SHA256 fingerprints must match.

6. Set the new repository secret with the GitHub CLI:

   ```bash
   ssh-keyscan -t ed25519 tiny-inference 2>/dev/null | gh secret set DEPLOY_KNOWN_HOSTS
   ```

The command in step 6 reads the new host key from standard input, so the value
is not placed directly in the shell command line.
