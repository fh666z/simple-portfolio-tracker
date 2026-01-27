# Portfolio Tracker

A simple desktop application to track and visualize the allocation and performance of your investment portfolio.

## Features

- **Import portfolio data** from images (PNG, JPG) or spreadsheets (XLSX, CSV)
- **OCR support** for extracting data from screenshots using Tesseract
- **Data review** - Edit imported data before confirmation to fix any OCR errors
- **Multi-currency support**:
  - Assign currency to each instrument (EUR, USD, GBP, CNH, etc.)
  - Configure exchange rates in the Currency Exchange tab
  - All allocations calculated in EUR
  - Add custom currencies as needed
- **Portfolio visualization** with holdings table showing:
  - Position, Market Value (in original currency)
  - Market Value in EUR (converted)
  - Allocation percentage (based on EUR values)
  - Daily P&L and Unrealized P&L
  - Editable Type, Region, and Currency classification
  - Target allocation and difference tracking
- **Statistics view** with allocation breakdown by:
  - Asset Type (Equity, Bonds, Commodity, Thematic, REIT)
  - Region (US, EU, EM, Global)
  - Combined Type + Region view
- **Automatic persistence** of portfolio data, currency settings, and exchange rates
- **Free Cash tracking** - Enter free cash (in EUR) to see total portfolio value

## Prerequisites

- **Python 3.10+**
- **Tesseract OCR** (for image import feature)

### Installing Tesseract OCR (Windows)

1. Download the installer from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (use default options)
3. Add Tesseract to your PATH:
   - Default location: `C:\Program Files\Tesseract-OCR`
   - Add this to your system PATH environment variable

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/simple-portfolio-tracker.git
   cd simple-portfolio-tracker
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Running the Application

```bash
python main.py
```

### Importing Portfolio Data

1. Click the **"New Input"** button
2. Either:
   - Drag and drop a file onto the drop zone
   - Click "Browse Files..." to select a file
3. Supported formats:
   - **Images**: PNG, JPG (uses OCR)
   - **Spreadsheets**: XLSX, XLS, CSV

### Data Review

After importing, a review dialog shows the extracted data:
- All fields are editable
- Yellow highlighted cells may need attention
- Click **"Confirm"** to accept or **"Cancel"** to discard

### Managing Holdings

In the Portfolio tab:
- **Currency** column - select the currency for each instrument
- **Type** and **Region** columns have dropdown menus for classification
- **Target %** column is editable - enter target allocation percentages
- **Value (EUR)** column shows the market value converted to EUR
- **Free Cash** input at the bottom - enter your available cash (in EUR)

### Managing Currencies

In the Currency Exchange tab:
- View and edit exchange rates for all currencies
- **Rate to EUR** - enter how many EUR equals 1 unit of the currency
  - Example: If 1 USD = 0.92 EUR, enter `0.92`
- EUR is always 1.0 and cannot be modified
- **Add new currencies** using the form at the bottom
- Changes are auto-saved and immediately reflected in allocations

Default currencies: EUR, USD, GBP, CNH

### Viewing Statistics

The Statistics tab shows allocation breakdown:
- **STATS by Type**: Allocation grouped by asset type
- **STATS by Region**: Allocation grouped by geographic region  
- **STATS Detailed**: Combined Type + Region breakdown

## Building Standalone Executable

To create a standalone .exe file:

```bash
python build.py
```

The executable will be created in the `dist/` folder.

## Data Storage

The application stores data in your home directory:
- Windows: `C:\Users\<username>\.portfolio-tracker\`
- Files:
  - `portfolio.json` - Portfolio holdings (including currency per instrument)
  - `mappings.json` - Instrument type/region/currency mappings
  - `settings.json` - Application settings (currencies list, exchange rates, free cash)

## Input File Format

### Spreadsheet Format

Expected columns (flexible naming):
| Column | Description |
|--------|-------------|
| Instrument | Ticker symbol |
| Position | Number of shares/units |
| Last | Current price |
| Change % | Daily change percentage |
| Cost Basis | Total purchase cost |
| Market Value | Current market value |
| Avg Price | Average purchase price |
| Daily P&L | Daily profit/loss |
| Unrealized P&L | Total unrealized profit/loss |

### Image Format

Screenshots from trading platforms are supported. The OCR will attempt to extract tabular data with the same columns as above.

## License

MIT License - see [LICENSE](LICENSE) file for details.
