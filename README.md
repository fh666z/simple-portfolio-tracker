# Portfolio Tracker

A desktop application to track and visualize the allocation and performance of your investment portfolio. Import from images or spreadsheets, manage multi-currency holdings, set target allocations, and export to JSON, CSV, or Excel.

## Features

### Menu & shortcuts

- **Menu bar**: File, Edit, Help (standard application menu).
- **File**: Import Portfolio Data, Load Data, Export (JSON / CSV / Excel), Reset Data, Exit.
- **Edit**: Find (focus search in Portfolio tab).
- **Help**: About.
- **Keyboard shortcuts**:
  - **Ctrl+N** – Import portfolio data
  - **Ctrl+O** – Load data from JSON
  - **Ctrl+S** – Export to JSON
  - **Ctrl+F** – Focus search (Portfolio tab)
  - **Ctrl+Q** – Exit

### Import & data

- **Import portfolio data** from:
  - **Images**: PNG, JPG (OCR via Tesseract)
  - **Spreadsheets**: XLSX, XLS, CSV
- **Drag & drop** or **Browse** in the import dialog.
- **Review dialog** after import: edit extracted data, fix OCR errors; yellow cells may need attention. Confirm or Cancel.
- **Load Data**: Open a previously exported JSON file (restores portfolio, currencies, rates, mappings).
- **Reset Data**: Clear all holdings and free cash; two-step confirmation (warning + type "DELETE").

### Export

- **Export to JSON** (Ctrl+S): Portfolio, settings (currencies, exchange rates), and instrument mappings. Default filename includes date.
- **Export to CSV**: Holdings table for use in spreadsheets.
- **Export to Excel**: XLSX with formatted table and summary row.

### Portfolio tab

- **Holdings table** with columns:
  - Instrument, Position, Last Price, Market Value (original currency), Value (EUR), Cost Basis
  - Allocation %, Target %, Diff w/ Target %, Diff in Cash, Diff in Shares
  - Unrealized P&L
- **Editable**: Position, Last Price, Cost Basis, Target %, Unrealized P&L; Type and Region via dropdowns.
- **Delete**: × button per row or right-click → "Delete '[instrument]'".
- **Search**: Filter by instrument name (Ctrl+F focuses search).
- **Type filter**: All, Equity, Bonds, Commodity, Thematic, REIT.
- **Clear Filters** to reset search and type filter.
- **Summary**: Total Invested (EUR), Free Cash (EUR), Total (EUR). Free cash is editable and included in total.
- **Empty state**: When there are no holdings, an "Import Portfolio Data" button is shown.

### Instrument Config tab

- **Table**: Instrument (read-only), Currency, Type, Region.
- **Currency**: Dropdown from configured currencies (add new in Currency Exchange tab).
- **Type**: Equity, Bonds, Commodity, Thematic, REIT, Unassigned.
- **Region**: US, EU, EM, Global, Non, Unassigned.
- **Sortable** by column. Changes are saved and applied across the app.

### Currency Exchange tab

- **Exchange rates**: One row per currency; rate = units of that currency per 1 EUR (e.g. USD 1.09 means €1 = $1.09).
- **Edit rates** in the table; EUR is fixed at 1.0.
- **Update rates from internet**: Fetches latest rates from Frankfurter API (no API key). Shows last updated date.
- **Add currency**: Form at bottom (code + rate). EUR is always present; other currencies can be added or removed (× in table).
- **Column order** is saved (drag header to reorder).

### Statistics tab

- **Pie charts** (matplotlib):
  - **By Type**: Allocation by asset type (Equity, Bonds, etc.).
  - **By Region**: Allocation by region (US, EU, EM, etc.).
  - **Detailed**: Combined Type + Region breakdown.
- Charts update when portfolio or config changes.

### Persistence & layout

- **Automatic save**: Portfolio, mappings, and settings are saved on change.
- **Stored data** (in user data directory):
  - `portfolio.json` – Holdings and free cash
  - `mappings.json` – Instrument type/region/currency and target allocation
  - `settings.json` – Currencies, exchange rates, window geometry, tab order, table column orders, free cash, last import path, rates last updated
- **Window**: Size and position restored on restart.
- **Tabs**: Reorder by drag-and-drop; order is saved.
- **Tables**: Column order in Portfolio, Instrument Config, and Currency Exchange tables is saved.

## Prerequisites

- **Python 3.10+**
- **Tesseract OCR** (optional, for image import)

### Installing Tesseract (Windows)

1. Download: https://github.com/UB-Mannheim/tesseract/wiki
2. Run the installer (default options are fine)
3. Add Tesseract to PATH (e.g. `C:\Program Files\Tesseract-OCR`)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/simple-portfolio-tracker.git
   cd simple-portfolio-tracker
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Run the application

```bash
python main.py
```

### Import portfolio data

1. **File → Import Portfolio Data...** (or **Ctrl+N**).
2. Drag and drop a file onto the drop zone, or click **Browse Files...**.
3. Supported: **Images** (PNG, JPG – OCR), **Spreadsheets** (XLSX, XLS, CSV).
4. In the review dialog, edit if needed, then **Confirm** or **Cancel**.

### Load / save / reset

- **File → Load Data...** (Ctrl+O): Choose a JSON file previously exported; portfolio, currencies, rates, and mappings are restored.
- **File → Export → Export to JSON** (Ctrl+S): Save full snapshot (portfolio + settings + mappings).
- **File → Export → Export to CSV** or **Export to Excel**: Save holdings for use elsewhere.
- **File → Reset Data...**: Clear all data (requires typing "DELETE" to confirm).

### Portfolio tab

- Use **Search** and **Type** filters to narrow holdings.
- Edit cells (Position, Last Price, Cost Basis, Target %, etc.) and use **Currency**, **Type**, **Region** dropdowns where available.
- Set **Free Cash (EUR)** in the summary bar; it is included in **Total (EUR)**.
- Delete a holding with the × button or right-click → Delete.

### Instrument Config tab

- Set **Currency**, **Type**, and **Region** per instrument. Values are remembered for future imports.

### Currency Exchange tab

- Edit **Rate (per 1 EUR)** for each currency.
- Click **Update rates from internet** to fetch current rates (Frankfurter API).
- Use the form at the bottom to **Add** a currency; remove with × (EUR cannot be removed).

### Find

- **Edit → Find...** (Ctrl+F): Switches to Portfolio tab and focuses the search box.

## Building a standalone executable

```bash
python build.py
```

The executable is created in the `dist/` folder.

### Application icon

The app uses a custom icon (window title bar, taskbar, and `.exe` in Explorer). A default icon is generated by:

```bash
python create_icon.py
```

This creates `assets/icon.ico`. Replace that file with your own `.ico` (16×16, 32×32, 48×48, 256×256 recommended) to customize the icon, then rebuild.

## Data storage location

- **Windows**: `C:\Users\<username>\.portfolio-tracker\`
- **Files**: `portfolio.json`, `mappings.json`, `settings.json`

## Input file format

### Spreadsheet (XLSX, CSV)

Expected columns (flexible naming):

| Column        | Description            |
|---------------|------------------------|
| Instrument    | Ticker symbol          |
| Position      | Number of shares/units |
| Last          | Current price          |
| Change %      | Daily change %         |
| Cost Basis    | Total purchase cost    |
| Market Value  | Current market value   |
| Avg Price     | Average purchase price |
| Daily P&L     | Daily profit/loss      |
| Unrealized P&L| Total unrealized P&L   |

### Image (PNG, JPG)

Screenshots from broker/trading platforms. OCR extracts tabular data; use the review dialog to correct any mistakes.

## License

MIT License – see [LICENSE](LICENSE) for details.
