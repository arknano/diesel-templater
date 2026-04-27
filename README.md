# Diesel Templater

![License](https://img.shields.io/github/license/arknano/diesel-templater)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)

Diesel-kun is a helpful html website templater for creating simple static sites.

Using a configurable template marker like `%template_name%`, you can easily insert reused html elements like navbars and footers without relying on any complex templating tools.

## Quick Start

Build the included example:

```bash
python diesel.py example/diesel.config
```

The default output folder is `export/` next to `diesel.py`.

To choose a different output folder, pass it as the second argument:

```bash
python diesel.py example/diesel.config "D:\Web\my-cool-website"
```

The export folder is deleted and rebuilt on every run.

## Configuration

Config files are JSON. Relative paths are resolved from the config file's directory.

```json
{
  "template_dir": "site/templates",
  "source_dir": "site",
  "template_pattern": "%(\\w+)%",
  "exclude_dirs": ["templates"],
  "exclude_files": []
}
```

Options:

- `template_dir`: folder containing template snippets.
- `source_dir`: folder containing the site files to copy and process.
- `template_pattern`: regex used to find template markers. The first capture group is used as the template name.
- `exclude_dirs`: directory names to skip while copying.
- `exclude_files`: filenames, source-relative paths, or glob patterns to skip, such as `README.md`, `pages/draft.html`, or `*.tmp`.

The export directory is a command-line option, not a config value.

## Templates

Any HTML file copied to the export folder can include template markers:

```html
<body>
  %header%
  <main>Hello</main>
</body>
```

Diesel-kun looks for a matching file in `template_dir`:

```html
<!-- site/templates/header.html -->
<header>My Site</header>
```

After building, the exported page contains the expanded template content.

## Nested Pages

Template links are adjusted for nested output pages. If `site/templates/header.html` contains:

```html
<a href="index.html">Home</a>
```

then `site/pages/nested.html` receives:

```html
<a href="../index.html">Home</a>
```

Absolute URLs, root-relative paths, anchors, `mailto:`, and paths that already start with `../` are left unchanged.