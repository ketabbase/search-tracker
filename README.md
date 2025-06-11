# Search Tracker

A Python-based tool developed by Ketabbase under the supervision of Dr. Mahsa Torabi to track and analyze web search behavior. This tool automatically records search queries, navigation patterns, and interaction with web pages while users browse.

## Research Goals

This tool is designed to support research in the following areas:

1. **Search Behavior Analysis**
   - Understand how users formulate search queries
   - Track navigation patterns between search results
   - Analyze time spent on different types of content

2. **User Interaction Patterns**
   - Study scrolling behavior and content engagement
   - Analyze tab management and multi-tasking behavior
   - Understand user attention patterns

3. **Search Efficiency Research**
   - Measure time spent on search tasks
   - Analyze query refinement patterns
   - Study information seeking strategies

4. **Educational Applications**
   - Support research in information literacy
   - Help understand student research behaviors
   - Improve search education and training

## Features

- Tracks Google search queries
- Records navigation between pages
- Monitors new tabs opened/closed
- Tracks scroll events
- Measures time spent on each URL
- Saves all data in CSV format for easy analysis

## Installation

### Quick Install (Recommended)

To install the latest version directly from GitHub, run:

```bash
pip install git+https://github.com/ketabbase/search-tracker.git@master
```

- Make sure you have the latest version of pip:
  ```bash
  python -m pip install --upgrade pip
  ```
- This will always install the latest code from the master branch.

### Install from Source
1. Clone the repository:
```bash
git clone https://github.com/ketabbase/search-tracker.git
cd search-tracker
```
2. Install the package:
```bash
pip install -e .
```

### Prerequisites
* Python 3.6 or higher
* Chrome browser installed
* ChromeDriver (will be automatically downloaded by Selenium)

### Verify Installation
After installation, you can verify it worked by running:
```bash
search-tracker --version
```

## Usage

### Basic Usage

Simply run the command:
```bash
search-tracker
```

This will start tracking your web search behavior. The data will be saved in a timestamped directory under `./data/`.

### Custom Data Directory

You can specify a custom directory to save the tracking data:
```bash
search-tracker --data-dir /path/to/your/directory
```

### Output Files

The tool creates several CSV files in the data directory:

- `queries.csv`: Records all Google search queries
- `navigation_links.csv`: Tracks page navigation
- `new_tabs.csv`: Records new tabs opened
- `scrolls.csv`: Tracks scroll events
- `url_durations.csv`: Records time spent on each URL

## How to Use

1. Start the tracker using one of the commands above
2. A Chrome browser window will open automatically
3. Navigate to Google and start searching
4. The tool will track your behavior in the background
5. Press Ctrl+C to stop tracking and save the data

## Data Privacy

- All data is stored locally on your computer
- No data is sent to any external servers
- You can delete the data directory at any time
- Data is collected for research purposes only

## Research Ethics

This tool is designed for research purposes and should be used in accordance with:
- Institutional Review Board (IRB) guidelines
- Research ethics protocols
- Data protection regulations
- Informed consent requirements

## Troubleshooting

### Chrome/ChromeDriver Issues

If you encounter issues with Chrome or ChromeDriver:

1. Make sure Chrome is installed and up to date
2. Try closing all Chrome windows before running the tracker
3. If problems persist, try running:
```bash
pip install --upgrade selenium
```

### Permission Issues

If you get permission errors:

1. Make sure you have write permissions in the data directory
2. Try running with administrator privileges
3. Specify a different data directory where you have write access

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Developed by Ketabbase
- Supervised by Dr. Mahsa Torabi
- Special thanks to all contributors and researchers who have provided feedback and suggestions

## Support

If you encounter any issues or have questions, please open an issue on GitHub. 
