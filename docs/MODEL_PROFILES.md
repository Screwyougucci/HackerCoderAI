# Model profiles

HackerCoderAI uses one model architecture and two GGUF quantization choices.

## v2 — Q2_K

- Choose a Q2_K quantized GGUF of Qwen2.5-Coder-3B-Instruct.
- Lower disk/RAM use, but noticeably more quantization loss.
- Best when the machine is memory constrained.

## v4 — Q4_K_M

- Choose a Q4_K_M quantized GGUF of the same model.
- Higher memory use than Q2_K; usually better code reasoning and output fidelity.
- Recommended starting point on a 16 GB CPU-only machine.

## Important

The profile label is a user-facing preset name; it does not transform a model. The GGUF file itself determines quantization. Set `MODEL_PATH` to the matching file and set `MODEL_PROFILE` to `v2` or `v4`. Do not simply rename a differently quantized file.

Model repositories and filenames can change. Download from a trusted publisher, read its model card and license, and verify any published SHA-256 checksum. Never commit model weights to this source repository.

## CPU tuning

The default context is 4096 tokens and thread count is 4. On an i7-8665U-class CPU, start with 4 threads; adjust based on responsiveness and thermal behavior. Lower `N_CTX` or `MAX_TOKENS` if memory pressure is high. The application explicitly sets `n_gpu_layers=0`.
