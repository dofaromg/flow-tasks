# Conversation Knowledge Extractor

**Author**: MR.liou × Claude (empathetic.mirror)  
**Version**: v1.0  
**Location**: `particle_core/src/conversation_extractor.py`

## Overview

The Conversation Knowledge Extractor is a powerful tool for analyzing, packaging, and exporting conversation records. It automatically identifies key points, logical structures, and knowledge insights from conversations, generating structured analysis reports.

## Key Features

### 1. Conversation Packaging & Export

Package conversation records into structured formats with multiple export options:

- **JSON**: Complete data structure with metadata and statistics
- **Markdown**: Human-readable format for documentation
- **Plain Text**: Simple text format

### 2. Attention Mechanism Analysis

Automatically identify conversation highlights using attention mechanisms:

- **Key Moments**: Identify important Q&A pairs
- **Topic Shifts**: Detect changes in conversation topics
- **High-Density Segments**: Mark paragraphs with many keywords

### 3. Logical Structure Extraction

Analyze the logical structure of conversations:

- **Core Concepts**: Extract proper nouns and important concepts
- **Causal Relations**: Identify cause-effect logic chains
- **Reasoning Chains**: Extract logical reasoning sequences
- **Conclusions**: Mark conclusive statements

### 4. AI Deep Analysis

Optional feature requiring Anthropic API Key:

- Deep analysis using Claude API
- Generate core insights
- Build knowledge graphs
- Extract reusable mental models

### 5. Report Generation

Generate complete analysis reports in Markdown format, including:

- Basic statistics
- Attention analysis results
- Logical structure analysis
- AI deep analysis (optional)

## Quick Start

### Basic Usage

```python
from conversation_extractor import ConversationExtractor

# Prepare conversation data
conversation = [
    {
        "role": "user",
        "content": "What is the Particle Language Core System?"
    },
    {
        "role": "assistant",
        "content": "The Particle Language Core System is an innovative logic execution framework..."
    }
]

# Initialize extractor
extractor = ConversationExtractor()

# Package conversation
package = extractor.package_conversation(
    conversation,
    metadata={
        "title": "Particle Language Discussion",
        "date": "2026-01-04",
        "tags": ["particle-language", "system-architecture"]
    }
)

# Export to different formats
extractor.export_to_file(package, "conversation.json", "json")
extractor.export_to_file(package, "conversation.md", "markdown")
extractor.export_to_file(package, "conversation.txt", "txt")
```

### Analyze Conversations

```python
# Attention analysis
attention = extractor.analyze_attention(conversation)
print(f"Key moments: {len(attention['key_moments'])}")
print(f"Topic shifts: {len(attention['topic_shifts'])}")

# Logical structure extraction
structure = extractor.extract_logical_structure(conversation)
print(f"Core concepts: {structure['concepts']}")
print(f"Causal relations: {len(structure['relationships'])}")
```

### Generate Reports

```python
# Generate complete analysis report
report = extractor.generate_report(conversation, include_ai_analysis=False)

# Save report
with open("analysis_report.md", "w", encoding="utf-8") as f:
    f.write(report)
```

### Use AI Deep Analysis (Requires API Key)

```python
# Initialize with API Key
extractor = ConversationExtractor(api_key="your_anthropic_api_key")

# Perform deep analysis
ai_result = extractor.deep_analysis_with_ai(conversation)
print(ai_result["raw_analysis"])

# Or include in report
report = extractor.generate_report(conversation, include_ai_analysis=True)
```

## Demo Scripts

### Run Complete Demo

```bash
cd particle_core
python demo_conversation_extractor.py
```

This runs four demonstrations:
1. Basic conversation packaging and export
2. Attention mechanism analysis
3. Logical structure extraction
4. Complete report generation

### Run Built-in Example

```bash
cd particle_core/src
python conversation_extractor.py
```

## Testing

Run the test suite:

```bash
cd particle_core
python test_conversation_extractor.py
```

Test coverage:
- ✓ Extractor initialization
- ✓ Conversation packaging
- ✓ Statistics calculation
- ✓ JSON/Markdown/TXT export
- ✓ Keyword extraction
- ✓ Attention analysis
- ✓ Concept extraction
- ✓ Causal relation extraction
- ✓ Reasoning chain extraction
- ✓ Conclusion extraction
- ✓ Logical structure extraction
- ✓ Report generation
- ✓ AI analysis (without API key test)

## API Reference

### ConversationExtractor

#### `__init__(api_key: str = None)`

Initialize the extractor.

**Parameters**:
- `api_key` (str, optional): Anthropic API Key for AI deep analysis

#### `package_conversation(messages: List[Dict], metadata: Dict = None) -> Dict`

Package conversation records.

**Parameters**:
- `messages`: List of messages in format `[{"role": "user/assistant", "content": "..."}]`
- `metadata` (optional): Metadata containing title, date, tags, etc.

**Returns**: Packaged conversation data dictionary

#### `export_to_file(package: Dict, filepath: str, format: str = "json")`

Export conversation package to file.

**Parameters**:
- `package`: Conversation package
- `filepath`: File path
- `format`: Format, options are "json", "markdown", "txt"

#### `analyze_attention(messages: List[Dict]) -> Dict`

Identify conversation highlights using attention mechanism.

**Returns**: Dictionary containing key_moments, topic_shifts, high_density_segments

#### `extract_logical_structure(messages: List[Dict]) -> Dict`

Extract logical structure from conversations.

**Returns**: Dictionary containing concepts, relationships, reasoning_chains, conclusions

#### `deep_analysis_with_ai(messages: List[Dict]) -> Dict`

Perform deep analysis using Claude API (requires API Key).

**Returns**: Dictionary containing raw_analysis and analyzed_at, or error message

#### `generate_report(messages: List[Dict], include_ai_analysis: bool = False) -> str`

Generate complete analysis report.

**Parameters**:
- `messages`: Conversation records
- `include_ai_analysis`: Whether to include AI deep analysis

**Returns**: Markdown-formatted report string

## Dependencies

```
anthropic  # For AI deep analysis (optional)
```

Added to `particle_core/requirements.txt`.

If AI analysis is not needed, the anthropic library is not required - the system degrades gracefully.

## Output Examples

### JSON Export Example

```json
{
  "metadata": {
    "title": "Particle Language Discussion",
    "date": "2026-01-04",
    "tags": ["particle-language", "system-architecture"]
  },
  "messages": [...],
  "statistics": {
    "total_messages": 4,
    "user_messages": 2,
    "assistant_messages": 2,
    "total_chars": 283,
    "avg_user_length": 15.5,
    "avg_assistant_length": 126.5
  },
  "exported_at": "2026-01-04T16:44:34.123456",
  "version": "1.0"
}
```

### Markdown Export Example

```markdown
# Particle Language Discussion
**Date**: 2026-01-04
**Tags**: particle-language, system-architecture

---

### 👤 User

What is the Particle Language Core System?

---

### 🤖 Assistant

The Particle Language Core System is an innovative logic execution framework...

---
```

### Analysis Report Example

Generated reports include:
- 📈 Basic Statistics
- 🎯 Attention Analysis
- 🧬 Logical Structure
- 🤖 AI Deep Analysis (optional)

## Use Cases

1. **Conversation Archiving**: Organize AI conversations into structured documents
2. **Knowledge Extraction**: Extract key concepts and logical relationships from conversations
3. **Meeting Minutes Analysis**: Analyze meeting records, identify important decisions and action items
4. **Study Notes Generation**: Generate study notes from educational conversations
5. **Research Interview Analysis**: Analyze interview records, extract core insights

## Important Notes

1. **API Key Security**: If using AI analysis, keep your API Key secure and don't commit it to version control
2. **Text Length Limits**: AI analysis limits conversation content to first 500 characters to control API costs
3. **Language Support**: Supports both Chinese and English, can process bilingual conversations
4. **Performance Considerations**: For very long conversations, consider processing in segments

## Future Improvements

- [ ] Support more export formats (PDF, DOCX)
- [ ] Enhanced keyword extraction (using TF-IDF or BERT)
- [ ] Support hierarchical analysis of multi-turn conversations
- [ ] Add visualization features (knowledge graphs, timelines)
- [ ] Support custom analysis rules
- [ ] Add sentiment analysis

## Contributing

Issues and Pull Requests are welcome!

## License

Follows the FlowAgent project license.

---

**Last Updated**: 2026-01-04  
**Maintainer**: FlowAgent Team
