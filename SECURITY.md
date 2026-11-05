# Security notes

- The web app binds to loopback (127.0.0.1) by default. Keep it local.
- The current app has no authentication. Do not change the bind address to 0.0.0.0 or expose it through a tunnel.
- Source scanning is read-only and does not execute scanned files or contact hosts.
- A rule match is a heuristic lead. Validate reachability, attacker control, context, and impact before reporting a vulnerability.
- Do not paste credentials or personal data into prompts. Local storage is not encrypted.
- The model is not a trusted authority. Review generated commands before running them.
