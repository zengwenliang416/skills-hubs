# Permission Policy

The runtime package requires no network access and does not install dependencies or modify package manifests.

Local writes are allowed only in the explicitly selected target:

- `inspect_frontend.py` and `verify_amicro_style.py` may write a target-relative report supplied through `--output`.
- `install_style_layer.py` may manage bundled assets only after `--apply`; dry-run is the default.
- Absolute paths, `../` traversal, and resolved symlink escapes are rejected.
- Installer writes are atomic and recorded in `.amicro-install.json`.
- Update and uninstall reject locally drifted managed files unless the user explicitly supplies `--force`.

The package starts no subprocess other than the Python process the user invokes and makes no network request.
