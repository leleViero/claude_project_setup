---
name: markdown-extractor-personal
description: Converts a URL, local file, or a folder containing a downloaded .md file into a self-contained, offline-capable markdown note using the markitdown MCP server. Downloads all images locally, rewrites links, and formats output using the personal note template.
triggers:
  - "extract markdown"
  - "convert to note"
  - "save page as note"
  - "markdown extractor"
---

# markdown-extractor-personal

You are executing the **markdown-extractor-personal** skill. Your job is to convert a URL, local file path, or a folder containing a downloaded markdown file into a fully self-contained markdown note, formatted with the personal knowledge base template, with all images saved locally.

## Input

The user provides one of:
- A URL: `https://example.com/article`
- A local file path: `/path/to/file.pdf` or `C:\path\to\file.docx`
- A folder path containing a downloaded `.md` file and its referenced assets: `/path/to/folder/` or `C:\path\to\folder\`

If no input was provided with the skill invocation, ask the user:
> "Please provide a URL, local file path, or a folder containing a downloaded markdown file to convert."

## Execution Steps

### Step 1 — Detect Input Type

Determine which of the three input modes applies:

**Mode A — URL**: input starts with `http://` or `https://` → proceed to Step 2A.

**Mode B — Local file**: input is a path to an existing file (has a file extension) → proceed to Step 2B.

**Mode C — Folder**: input is a path to a directory → proceed to Step 2C.

To distinguish Mode B from Mode C on an ambiguous path, check whether the path ends with `/` or `\`, or has no file extension. If still ambiguous, use the Bash tool: `test -d "<path>" && echo dir || echo file`.

### Step 2 — Obtain Markdown Content and Read Template (in parallel where possible)

Always read the template file in parallel with the content acquisition step.

**Read the template file (all modes):**
Read `template/{{01 Knowledge base}}.md` located in the same directory as this skill file.

---

**Step 2A — URL input:**

Convert to URI (use as-is since it already starts with `http://` / `https://`) and call the MCP tool:
```
mcp__markitdown__convert_to_markdown(uri="<URL>")
```
If the MCP tool returns an error or empty content, stop and report the error to the user. Do not proceed with empty content.

---

**Step 2B — Local file input:**

Convert the file path to a `file://` URI:
- Unix: `/home/user/file.pdf` → `file:///home/user/file.pdf`
- Windows: `C:\path\file.pdf` → `file:///C:/path/file.pdf` (replace backslashes with forward slashes)

Call the MCP tool:
```
mcp__markitdown__convert_to_markdown(uri="<file URI>")
```
If the MCP tool returns an error or empty content, stop and report the error to the user. Do not proceed with empty content.

---

**Step 2C — Folder input:**

1. Locate the `.md` file inside the folder:
   - Prefer a file whose name matches the folder name (e.g. `folder-name/folder-name.md`).
   - If not found, take the first `.md` file in the folder root.
   - If no `.md` file exists, stop and tell the user: "No markdown file found in the provided folder."
2. Read the `.md` file content directly using the Read tool — **do not call the MCP tool**.
3. Note any existing local asset files (images, PDFs, etc.) already present in the folder; these will be treated as already-local references and should be preserved as-is during image processing.
4. Set `source` to the folder path provided by the user.

### Step 3 — Extract Metadata from Converted Markdown

From the raw converted markdown:

1. **Title**: Extract the first `# Heading` found. If none, derive from the URL path or filename (strip extension, replace hyphens/underscores with spaces, title-case).
2. **Description**: Extract the first non-heading paragraph (max 200 characters). This becomes `descriptionValue`.
3. **Source**: The original URL or file path provided by the user.
4. **Date**: Today's date in ISO format (`YYYY-MM-DD`).
5. **Content body**: Everything after the first `# Heading` (or all content if no heading found).
6. **Tags**: Scan the content for recurring domain keywords (tech stack names, proper nouns, topic words with 3+ occurrences). Propose up to 5 tags as a YAML list. Leave `clusterTags` as `[]`.

### Step 4 — Build the Output Slug and Folder

1. Slug = title → lowercase → replace spaces and special chars with `-` → truncate to 60 chars → strip leading/trailing `-`

2. Determine the output base path based on the current environment:
   - **Windows (native)**: `C:\Users\davi\Documents\01 Local repo\Daniele Personal\Daniele Personal_remoteSync\00 Markitdown-agent-IN`
   - **WSL**: `/mnt/c/Users/davi/Documents/01 Local repo/Daniele Personal/Daniele Personal_remoteSync/00 Markitdown-agent-IN`

   To detect the environment, use the Bash tool:
   ```bash
   uname -s
   ```
   If the result contains `Linux` and the path `/mnt/c` is accessible, use the WSL path. Otherwise use the Windows path.

3. Output folder: `<base-path>/<slug>/`
4. Output markdown file: `<base-path>/<slug>/<slug>.md`
5. Create the output folder and `<base-path>/<slug>/ref/` before writing.

### Step 5 — Apply the Template

Take the template content and produce the final note by substituting the following:

| Template field | Value |
|---|---|
| `strategicValue: 0` | Keep as `0` (user fills later) |
| `innovationValue: 0` | Keep as `0` |
| `digitalTransformationValue: 0` | Keep as `0` |
| `leadershipValue: 0` | Keep as `0` |
| `technologyValue: 0` | Keep as `0` |
| `tags: []` | Replace with extracted tags list, e.g. `tags: [python, llm, api]` |
| `clusterTags: []` | Keep as `[]` |
| `descriptionValue: string` | Replace `string` with the extracted description |
| `[[]]` (Graph connections) | Keep as `[[]]` — user fills Obsidian links manually |
| `###### Links` section | Add a line below: `- [Source](<source URL or path>)` |
| `# Main description` | Replace with `# <extracted title>` |
| `Main content` | Replace with the full extracted content body |
| `## Header section` / `Content` blocks | Remove these placeholder blocks — the extracted content replaces them |
| `### Header section` / `Content` | Remove |
| `#### Checkbox if necessary` block | Remove |
| `###### File Attachments` block | Keep the section header, remove the placeholder line; images will be listed here after download |

Write the assembled note to `<base-path>/<slug>/<slug>.md`.

### Step 6 — Download Images

Determine the absolute path to this skill file's directory, then run:

```bash
python "<absolute-path-to-skill-dir>/scripts/image_downloader.py" "<base-path>/<slug>/<slug>.md"
```

The skill directory is `markdown-extractor-personal/` — resolve its absolute path at runtime using the project root or the path from which the skill was invoked.

Use the same path format (Windows or WSL) as determined in Step 4 when passing the markdown file path to the script.

Wait for the script to complete and capture its output summary (images found / downloaded / failed).

**For folder input (Mode C):** If the source folder contained existing asset files (images already local), they will be skipped by the script (not remote URLs). The script will only download any remaining remote image URLs found in the content.

If the script is not yet available (file doesn't exist at `scripts/image_downloader.py`), skip this step and inform the user:
> "Image downloader script not found at scripts/image_downloader.py. Images remain as remote links."

### Step 7 — Report to User

Output a clean summary:

```
✓ Note created: <base-path>/<slug>/<slug>.md
  Title    : <title>
  Source   : <original input>
  Images   : <N downloaded> / <M found> (saved to ref/)
  Tags     : <extracted tags>

Open the file or copy to your knowledge base.
```

## Error Handling

| Situation | Action |
|---|---|
| MCP tool unavailable | Stop. Tell user: "The markitdown MCP server is not running. Start it and retry." |
| MCP returns empty markdown | Stop. Ask user to verify the URL/file is accessible. |
| Image download fails | Keep original URL, append `<!-- download-failed -->` inline. Continue with remaining images. |
| Template file missing | Create a minimal default template (see below) at the template path, then continue. |
| Output folder already exists | Proceed — overwrite the `.md` file but do not delete existing assets. |
| Output base path not accessible | Stop. Tell user: "Cannot access the output folder at <base-path>. Make sure the drive is mounted (WSL: /mnt/c) or the path exists." |

**Minimal fallback template** (create at `template/{{01 Knowledge base}}.md` if missing):
```markdown
---
strategicValue: 0
innovationValue: 0
digitalTransformationValue: 0
leadershipValue: 0
technologyValue: 0
tags: []
clusterTags: []
descriptionValue: string
---
###### Graph connections
[[]]

###### Links

# Main description
Main content
```

## Notes

- The fixed output base path is `C:\Users\davi\Documents\01 Local repo\Daniele Personal\Daniele Personal_remoteSync\00 Markitdown-agent-IN` (Windows) or `/mnt/c/Users/davi/Documents/01 Local repo/Daniele Personal/Daniele Personal_remoteSync/00 Markitdown-agent-IN` (WSL). Always use the path format matching the detected environment.
- The skill directory path (`scripts/image_downloader.py`) must be resolved to an absolute path before calling via Bash.
- The Python script handles all image downloading and in-place link rewriting. Do not attempt to download images yourself.
- Do not modify the template file itself — only use it as a read-only scaffold.
- The output note should be valid Obsidian-compatible markdown (frontmatter + wikilinks preserved).
- For folder input (Mode C): downloaded markdown files often have a mismatch between the image subfolder name referenced in the `.md` (e.g. `i-spent-20/<filename>`) and the actual assets folder name on disk (e.g. `references/<filename>`). When this happens, copy images from the actual assets folder to `ref/` in the output and rewrite all image paths in the output note to `ref/<filename>`, regardless of the original subfolder name used in the source `.md`.
- For folder input (Mode C): the source folder is read-only — never move or delete files from it. The output is always written to `<base-path>/<slug>/` as with all other modes.
