# Neovim

Personal AstroNvim v6 configuration, managed by chezmoi.

The source of truth is `private_dot_config/nvim` in the chezmoi source
directory. Plugin revisions are pinned in `lazy-lock.json`.

## Managed language tools

Global tools are declared in `private_dot_config/mise/config.toml`:

- `http:kotlin-lsp` powers `kotlin.nvim`.
- `npm:@postgrestools/postgrestools` powers `postgres_lsp`.
- `pipx:mypy` completes Python linting alongside Ruff.

After changing the source, apply only this configuration with:

```sh
chezmoi apply ~/.config/nvim
```

Install the declared tools with:

```sh
mise install
```
