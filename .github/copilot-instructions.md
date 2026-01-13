# Copilot Instructions for cv_migrator

## Project Overview

**cv_migrator** is a Python utility that converts LaTeX CV documents (typically `.tex` files) into structured YAML format. The primary use case is migrating academic/professional CVs from LaTeX markup to machine-readable YAML while preserving formatting information and handling multiple languages (English/Spanish).

## Architecture & Data Flow

1. **Input**: LaTeX CV file (`.tex`) with sections like `\section{}`, `\subsection{}`, `\cventry{}`, etc.
2. **Processing Pipeline**:
   - Read LaTeX file line-by-line
   - Apply regex-based formatting transformations (bold, italics, underline, superscript to Markdown equivalents)
   - Parse LaTeX macros (`\cventry`, `\cvitemwithcomment`, `\title`, etc.) based on section context
   - Extract key-value pairs and structure data hierarchically
3. **Output**: YAML file with section-organized CV data

## Key Files & Patterns

- [old_text_to_yaml.py](old_text_to_yaml.py): Main conversion logic
  - `convert_tex_to_yaml(filepath)`: Entry point; orchestrates parsing
  - `latex_*_to_markdown()` functions: Regex-based formatting conversions (bold → `**text**`, italics → `*text*`)
  - `parse_*()` functions: Section-specific parsers (education, publication, poster, course, language_exam)

## Parser Selection Logic

Section parsing is **context-aware** and uses `section_name` + optional `subsection_name` to route to correct parser:

- **Education**: Used for "Education", "Experience" sections → extracts `{date, name, location, description}`
- **Publication**: "Production" → "Publications" → extracts `{title, date, journal, authors, description}`
- **Poster**: "Production" → "Posters/Oral Presentations" or "Outreach" → extracts `{title, date, event, authors, description}`
- **Course**: "Participation in Conferences and Schools" → extracts `{name, date, extension, location, language, description}`
- **Language Exam**: "Languages" → "International Exams" → extracts `{name, date, description}`

*Bilingual handling*: English section names are prioritized; Spanish equivalents (e.g., "Educación", "Experiencia") are fallback options.

## Development Workflow

1. **Setup**: Uses `pixi` for environment management (Python 3.13.2, PyYAML 6.0.2)
   ```bash
   pixi run python old_text_to_yaml.py "path\to\main.tex"
   ```

2. **Input Requirements**: LaTeX file must follow `moderncv` package conventions with proper macro structure

3. **Debugging**: Print statements in parse functions output unrecognized entry formats; raise `ValueError` for critical parsing failures

## Common Patterns & Conventions

- **Line Iteration**: Uses generator pattern (`make_lines_iterator()`) to apply formatting while reading
- **LaTeX Parsing**: Regex splits on braces `{...}` and ampersands `&` (for tables); handles trailing `\\` continuations
- **Type Handling**: 
  - Sections can be dict (most) or list ("Participation in Conferences" is list-only)
  - Subsections always list entries
  - Free-text fallback for unparseable lines
- **Unicode Support**: File I/O explicitly uses UTF-8 encoding for international character support

## Known Limitations & Edge Cases

- `parse_course()` has a bug (line 273-280): compares `len(parts) == 4` but slices from `parts[:5]`
- Multi-line entries (ending with `\\`) need manual continuation handling in generator loop
- Free-text fallback (`content_dict[section].setdefault("free_text", [])`) captures unmatched lines; inspect these for parser gaps
- Superscript regex (`\$\^\{...\}\$`) is specific; may not match all LaTeX superscript styles

## Testing & Validation

- No formal test suite; validate by:
  1. Running converter on sample CV
  2. Comparing YAML structure against input LaTeX sections
  3. Checking for formatting loss (missing bold/italics/underlines in output)
  4. Inspecting `free_text` arrays for incomplete parses

## Enhancement Guidelines

When adding features:
- **New sections**: Define parser function, add to routing logic in main loop
- **New formatting**: Add regex function + call in `make_lines_iterator()` + update markdown mapping
- **Multilingual support**: Add Spanish/other section names as fallback conditions
- **Error handling**: Extend rather than replace current ValueError strategy to preserve context
