#!/bin/bash
# assistant by perplexity
# https://www.perplexity.ai/search/how-to-translate-adoc-to-markd-ekW4AJ58QuiM9gSow8cVlA

# adoc-to-md-converter.sh
# Converts Asciidoc to Markdown with table formatting preservation

# Input validation
if [ -z "$1" ]; then
    echo "Usage: $0 <input.adoc>"
    exit 1
fi

INPUT_FILE="$1"
OUTPUT_FILE="${INPUT_FILE%.*}.md"
TEMP_XML=$(mktemp)

# Verify dependencies
command -v asciidoctor >/dev/null 2>&1 || { echo >&2 "Error: asciidoctor required but not found."; exit 1; }
command -v pandoc >/dev/null 2>&1 || { echo >&2 "Error: pandoc required but not found."; exit 1; }

# Convert to DocBook with proper encoding
asciidoctor -b docbook "$INPUT_FILE" -o - | \
iconv -f utf-8 -t utf-8 >  "$TEMP_XML"
if [ "$?" != "0" ]; then
	asciidoctor -a encoding=UTF-8 -a compat-mode=legacy -b docbook "$INPUT_FILE" -o "$TEMP_XML"
fi

# Convert DocBook to Markdown and Post-processing for table alignment and checkmarks
pandoc -f docbook -t gfm+pipe_tables \
       --columns=120 \
       --wrap=preserve \
        "$TEMP_XML" | \
sed -E '
s/\[\[(.*)\]\]/<a name="\1"><\/a>/g;    # Convert anchor links
s/\|:---/\|:---:/g;                      # Fix table alignment markers
s/✓/[✓]/g;                               # Ensure checkmark visibility
s/<<#(.*)>>/[§\1]/g;                    # Convert cross-references
' > "$OUTPUT_FILE"

# Cleanup
rm "$TEMP_XML"

echo "Converted: $INPUT_FILE -> $OUTPUT_FILE"
