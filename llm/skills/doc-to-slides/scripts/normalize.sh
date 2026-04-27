#!/usr/bin/env bash
# normalize.sh — Stage 1 of doc-to-slides.
# Convert .md / .docx / .pdf / .html input to clean Markdown.
# Prints the absolute path of the normalized file on stdout.
# Warnings / progress go to stderr.

set -euo pipefail

usage() { echo "usage: $0 <input-file>" >&2; exit 64; }
[ $# -eq 1 ] || usage
INPUT="$1"
[ -f "$INPUT" ] || { echo "error: $INPUT not found" >&2; exit 66; }

WORKDIR="$(mktemp -d -t doc-to-slides-XXXXXX)"
OUT="$WORKDIR/normalized.md"
ext="${INPUT##*.}"
ext="$(echo "$ext" | tr '[:upper:]' '[:lower:]')"

case "$ext" in
  md|markdown|txt)
    # Passthrough. Strip HTML comments and inline <style> blocks.
    sed -E 's/<!--[^>]*-->//g; /<style[^>]*>/,/<\/style>/d' "$INPUT" > "$OUT"
    ;;
  docx|html|htm)
    if ! command -v markitdown >/dev/null 2>&1; then
      echo "error: markitdown not installed. pip install 'markitdown[all]'" >&2
      exit 69
    fi
    markitdown "$INPUT" > "$OUT"
    ;;
  pdf)
    if command -v markitdown >/dev/null 2>&1; then
      if markitdown "$INPUT" > "$OUT" 2>"$WORKDIR/markitdown.err"; then
        :
      else
        echo "warn: markitdown failed on PDF, falling back to pdftotext" >&2
        pdftotext -layout "$INPUT" "$OUT"
      fi
    elif command -v pdftotext >/dev/null 2>&1; then
      pdftotext -layout "$INPUT" "$OUT"
    else
      echo "error: need markitdown or pdftotext to handle PDF" >&2
      exit 69
    fi
    ;;
  *)
    echo "error: unsupported extension .$ext (supported: md, docx, pdf, html, txt)" >&2
    exit 65
    ;;
esac

# Sanity warnings — surfaced to stderr for the agent to relay.
words=$(wc -w < "$OUT" | tr -d ' ')
if [ "$words" -lt 100 ]; then
  echo "warn: normalized output is only $words words — input may be image-only or extraction failed" >&2
fi
if grep -q '\f\|^[[:space:]]*Page [0-9]\+' "$OUT" 2>/dev/null; then
  echo "warn: page-break artifacts detected — consider manual cleanup before planning" >&2
fi

echo "$OUT"
