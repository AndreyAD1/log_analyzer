# Log Analyzer

This script parses logs of a web server, calculate statistics of request 
processing time and renders an HTML report file.

# Project Goal
The code is written for educational purposes. 
Training course for Python developers: [OTUS.ru](https://otus.ru/lessons/razrabotchik-python/).

# Getting Started
 
## How to Install
Python v3.7 should be already installed. No third-party dependencies are required.

## Quick Start 
1. Download this repository;
2. Configure the script setting the path to log files and report properties.
There are to ways to configure the script: change the variable `default_config` 
in the module `log_analyzer.py` or make your own config file.
An example of configuration file:
```json
{
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log",
    "SCRIPT_LOG_PATH": "script.log"
}
```

To run script on Linux enter the command:
```bash
$ python3 log_analyzer.py --config <path_to_config_file>
```

## Script functionality
If user did not set the parameter `--config`, script uses the variable 
`default_config`. Otherwise, the script composes configuration merging
dicts from a config file and the variable. 

The script searches the log file in the format `nginx-access-ui.log-YYYYDDMMM`.
If script found the newest unprocessed log file, it begins to process it.
It calculates statistics of request processing time per each URL: 
+ number,
+ number percent per total request number, 
+ processing time per URL,
+ processing time percent per total processing time, 
+ average processing time,
+ maximum processing time, 
+ median processing time.

Finally, the script renders an HTML report. A report template is located in
`/data/report.html`.