# Refactor Analyzer

A powerful code analysis tool that automatically identifies similar code regions across your codebase using advanced Locality Sensitive Hashing (LSH) algorithms. Find potential refactoring opportunities by detecting duplicate or near-duplicate code patterns that could be extracted into shared functions or modules.

## Overview

The Refactor Analyzer employs sophisticated similarity detection algorithms to scan your entire codebase and identify regions of code that share similar patterns or functionality. By using k-shingles (character n-grams) and MinHash signatures, it can efficiently detect both exact and near-exact duplicates across different files.

### How It Works

1. **Codebase Preprocessing**: Reads and normalizes all files in your project directory
2. **Shingling**: Converts each line of code into k-shingles (5-character substrings) for comparison
3. **LSH Algorithm**: Uses MinHash signatures and banding techniques to efficiently find similar lines
4. **Similarity Graph**: Creates connections between similar lines based on configurable Jaccard similarity thresholds
5. **Region Expansion**: Uses sliding window approach to identify contiguous blocks of similar code
6. **Results Generation**: Outputs ranked similar regions that are candidates for refactoring

## Features

- ✅ **Efficient Similarity Detection**: LSH algorithm enables fast comparison across large codebases
- ✅ **Configurable Thresholds**: Adjust sensitivity for both line-level and region-level similarity
- ✅ **Cross-File Analysis**: Only identifies similarities between different files (avoids false positives from same-file duplicates)
- ✅ **Region-Based Results**: Groups similar lines into meaningful code blocks rather than individual line matches
- ✅ **Detailed Output**: Provides exact line numbers and code content for each similar region
- ✅ **JSON Export**: Machine-readable results for integration with other tools
- ✅ **Progress Tracking**: Real-time feedback during analysis with step-by-step progress indicators

## Prerequisites

- Python 3.6 or higher
- Required dependencies (see requirements.txt)

## Installation

1. Clone the repository:

```bash
git clone <your-repo-url>
cd refactor-analyzer
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## How to Use

### Basic Usage

Run the analyzer from the project root directory:

```bash
python -m main
```

This will:

1. Read the configuration from `config.json`
2. Analyze the codebase specified in your configuration
3. Generate similarity analysis results
4. Save findings to `results.json`

### Configuration

Customize the analysis behavior by editing `config.json`:

```json
{
  "region_length": 10, // Minimum lines required for a similar region
  "candidate_threshold": 0.7, // LSH candidate selection threshold (0.0-1.0)
  "line_threshold": 0.8 // Final similarity threshold for line matching (0.0-1.0)
}
```

**Configuration Parameters:**

- `region_length`: Minimum number of consecutive similar lines to constitute a refactorable region
- `candidate_threshold`: Controls how selective the initial similarity detection is (lower = more candidates)
- `line_threshold`: Final threshold for determining if two lines are truly similar (higher = more strict)

### Understanding Results

The tool generates `results.json` containing:

- **Regions**: Similar code blocks with exact line content
- **File References**: Source file paths for each similar region
- **Line Numbers**: Precise locations of similar code blocks
- **Similarity Scores**: Quantified similarity between regions

## More to Come

🚧 **Coming Soon:**

- **CLI Interface**: Command-line tool with advanced options and filtering
- **REST API**: HTTP API for integration with IDEs and CI/CD pipelines
- **Web Dashboard**: Interactive web interface for visualizing refactoring opportunities
- **IDE Plugins**: Direct integration with popular code editors

## Example Output

```json
[
  {
    "regions": {
      "file1_region": ["def process_data():", "    data = load_data()", "    return transform(data)"],
      "file2_region": ["def handle_input():", "    input = get_input()", "    return process(input)"]
    },
    "file1": "src/module_a.py",
    "file2": "src/module_b.py"
  }
]
```

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

[Add your license information here]
