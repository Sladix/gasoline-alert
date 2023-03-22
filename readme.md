# Gas Availability Alert
This script monitors gas stations in France and alerts you when the availability of a specific gas type changes. The script uses the API provided by the French government to retrieve the latest data on gas prices and availability.

## Features
- Monitors gas stations in a specific postal code or all stations in France (Up tp 1000 results, increase the count at your own risks)
- Alerts when the availability of the specified gas type changes
- Stores the gas availability history in a CSV file
- Optionally, set a custom time interval between checks
## Requirements
- Python 3.x
- requests library
- simpleaudio library

To install the required libraries, run:

```bash
pip install requests simpleaudio
```
## Usage
To run the script, use the following command:

```
python app.py <gas_type> <postal_code> <interval>
```
`<gas_type>`: The type of gas you want to monitor. Choose from E10, SP98, SP95, E85, Gazole, or GPLc.

`<postal_code>`: (Optional) The postal code of the area you want to monitor. If not provided, the script will monitor all gas stations in France (first 1000 results). Note that you must input the exact postal code, it won't work with regional ones (44300 will work but 44000 won't)

`<interval>`: (Optional) The time interval (in seconds) between checks. The default and minimal value is 60 seconds (The API is updated with 1mn interval at most).

## Example
To monitor the availability of E10 gas in the 75001 postal code area and check every 5 minutes (300 seconds), run:

```bash
python app.py E10 75001 300
```
## Output
The script will output the following information:

- An alert message when the availability of the specified gas type changes
- The number of gas stations with changed availability after each check
- The most recently updated available gas station on the first run

The script will also store the gas availability history in a CSV file within the data folder. The filename will be in the format `<postal_code>_<gas_type>_gas_availability_log.csv`. If the postal code is not specified, it will be replaced with `all`.

## Notes
This script relies on the API provided by the French government, which may be subject to change. Ensure you have the latest version of the script and that the API is still functioning as expected.

Remember to respect the API usage policy and avoid making excessive requests in a short period of time.