#!/usr/bin/env python3
"""Record local model identity and effective service settings without credentials."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cbm_drift_v2.common import read_json, sha256_file, write_json


def main() -> None:
    config = read_json(ROOT / "config/experiment_config.json")
    deployment = config["model"]["deployment"]
    model_root = Path(deployment["weights_path"])
    identity_files = ["config.json", "generation_config.json", "tokenizer_config.json", "model.safetensors.index.json"]
    generation_defaults = read_json(model_root / "generation_config.json")
    manifest = {
        "model_name": config["model"]["model_name"],
        "weights_path": str(model_root),
        "identity_file_sha256": {
            name: sha256_file(model_root / name) for name in identity_files if (model_root / name).exists()
        },
        "deployment": deployment,
        "service_endpoints": config["model"]["base_urls"],
        "launch_script_sha256": sha256_file(ROOT / "scripts/launch_qwen_service.sh"),
        "requested_generation": config["generation"],
        "chat_template_kwargs": config["model"]["extra_body"]["chat_template_kwargs"],
        "inherited_model_generation_defaults": generation_defaults,
        "effective_sampling_note": "request temperature=0.7 and top_p=0.9 override model defaults; top_k=20 is inherited from generation_config.json",
        "credentials_recorded": False,
    }
    write_json(ROOT / "manifests/model_runtime_manifest.json", manifest)
    print({"written": "manifests/model_runtime_manifest.json", "identity_files": len(manifest["identity_file_sha256"])})


if __name__ == "__main__":
    main()
