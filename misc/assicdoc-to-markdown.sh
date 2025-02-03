#!/bin/bash
# assistant by perplexity
# https://www.perplexity.ai/search/how-to-translate-adoc-to-markd-ekW4AJ58QuiM9gSow8cVlA

# adoc-to-md-converter.sh
# Converts Asciidoc to Markdown with table formatting preservation

INPUT_FILE="$1"
OUTPUT_FILE="${INPUT_FILE%.*}.md"

# Verify dependencies
command -v asciidoctor >/dev/null 2>&1 || { echo >&2 "Error: asciidoctor required but not found."; exit 1; }
command -v pandoc >/dev/null 2>&1 || { echo >&2 "Error: pandoc required but not found."; exit 1; }

# Conversion pipeline
asciidoctor -b docbook "$INPUT_FILE" -o - | \
iconv -f utf-8 -t utf-8 | \
pandoc -f docbook -t gfm+pipe_tables \
       --columns=120 \
       --wrap=preserve \
       - | \
# Post-processing for table alignment and checkmarks
sed -E '
s/\[\[(.*)\]\]/<a name="\1"><\/a>/g;    # Convert anchor links
s/\|:---/\|:---:/g;                      # Fix table alignment markers
s/✓/[✓]/g;                               # Ensure checkmark visibility
s/<<#(.*)>>/[§\1]/g;                    # Convert cross-references
' > "$OUTPUT_FILE"

echo "Converted: $INPUT_FILE -> $OUTPUT_FILE"

