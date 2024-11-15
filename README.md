# Alliant Energy Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

This Home Assistant integration gets energy usage and cost data from Alliant Energy.

## Features

- Current billing period usage and cost
- Forecasted usage and cost
- Historical usage data
- Cost per kWh calculations (including customer charge adjustments)
- Billing period tracking
- Automatic cost estimation when Alliant data isn't available

## Installation

### HACS Installation

1. Open HACS in Home Assistant
2. Click on "Integrations"
3. Click the three dots in the top right
4. Select "Custom repositories"
5. Add this repository URL and select "Integration" as the category
6. Click "Add"
7. Find "Alliant Energy" in the list and click "Download"
8. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/alliant_energy` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings -> Devices & Services -> Add Integration
2. Search for "Alliant Energy"
3. Enter your Alliant Energy credentials

## Sensors

| Sensor                                 | Description                                        |
| -------------------------------------- | -------------------------------------------------- |
| Current Bill Electric Usage To Date    | Current billing period usage in kWh                |
| Current Bill Electric Forecasted Usage | Projected usage for current billing period         |
| Typical Monthly Electric Usage         | Average monthly usage                              |
| Current Bill Electric Cost To Date     | Current billing period cost                        |
| Current Bill Electric Forecasted Cost  | Projected cost for current billing period          |
| Typical Monthly Electric Cost          | Average monthly cost                               |
| Electric Cost per kWh                  | Calculated energy rate (excluding customer charge) |
| Current Bill Electric Start Date       | Start date of current billing period               |
| Current Bill Electric End Date         | End date of current billing period                 |

## Cost Calculation Details

The integration calculates costs using:

- Energy rate (per kWh) derived from previous billing period
- Daily customer charge of $0.4932
- Actual Alliant Energy data when available
- Estimated costs when Alliant data isn't available

## Debugging

Set up logging for troubleshooting:

```yaml
logger:
  default: info
  logs:
    custom_components.alliant_energy: debug
```

## Contributing

Feel free to submit issues and pull requests.

## License

MIT License - see LICENSE file

## Testing

### Command Line Testing

For quick testing of the API client:

1. Install test requirements:

```bash
pip install -r tests/requirements_test.txt
```

2. Run the CLI test script:

```bash
python tests/test_alliant_cli.py
```

You can also create a `.env` file with your credentials:

```
ALLIANT_USERNAME=your_username
ALLIANT_PASSWORD=your_password
```

### Running Unit Tests

To run the unit tests:

```bash
pytest tests/
```
