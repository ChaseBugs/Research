

# Repository Rules

## DOCX Math/Text Cleanup

When the user gives a folder path for document cleanup, use the Python converter script in this repository to process `.docx` files only.

Purpose: AI-generated text copied into documents can break math expressions and symbols. Convert LaTeX-style inline math artifacts to their correct plain-text meaning, and keep all other document content unchanged.

Whole-folder command:

```powershell
python -B fix_docx_math_text.py "D:\Research\6" --dry-run
python -B fix_docx_math_text.py "D:\Research\6"
```

Replace `"D:\Research\6"` with the folder path the user gives. Always run `--dry-run` first to preview affected `.docx` files. The real command edits matching `.docx` files in place and creates `.docx.bak` backups by default.

The listed rows are examples of the bug style, not the full bug list. Prefer regular-expression cleanup for the pattern family:

- Inline dollar math: `$...$`
- Text wrappers: `\text{...}`, `\mathrm{...}`, `\operatorname{...}`
- Comparison symbols: `\ge`, `\geq`, `\le`, `\leq`, `\gt`, `\lt`
- Degree markers: `^\circ`, `\circ`, `\degree`
- Numeric ranges and units inside math, such as `10\text{ to }20\text{ milliseconds}` or `<500\text{ kVA/t}`

Example conversions:

| Bad copied content | Correct content |
| --- | --- |
| `($2\text{ to }5\text{ seconds}$)` | `Slow (2 to 5seconds)` |
| `Ultra-fast ($10\text{ to }20\text{ milliseconds}$)` | `Ultra-fast (10 to 20 milliseconds)` |
| `$2.5\text{ kV}$` | `2.5 kV` |
| `$2.5\text{ kV}$ AC` | `2.5 kV AC` |
| `($1:2:4:8$ kVAR ratios)` | `(1:2:4:8 kVAR ratios)` |
| `exceed $45^\circ\text{C}$.` | `exceed 45 C.` |
| `$<500\text{ kVA/t}$` | `< 500kVA/t` |
| `$\ge 850\text{ kVA/t}$` | `>= 850 kVA/t` |
| `$>90\text{ minutes}$` | `> 90 minutes` |
| `$35\text{ to }50\text{ minutes}$` | `35 to 50 minutes` |

Do not modify PDFs, images, archives, or other file types. Do not rewrite whole documents manually. Only touch content matching this math/text artifact style unless the user gives more mappings.
