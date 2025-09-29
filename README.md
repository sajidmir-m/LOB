## LOB Summary Generator

Generates Customer Support LOB summaries from inputs (Issue Type, VOC, Stock/Slot) per SOP rules. Includes a CLI, FastAPI service, and web frontend with CSV knowledge base integration.

### Features

- **Web Frontend**: Beautiful, responsive UI with form validation
- **CSV Integration**: Loads issue types and SOP rules from CSV file
- **Auto-suggestions**: Intelligent issue type matching based on VOC
- **Validation**: CSV-based validation and correct answers display
- **CLI Tool**: Command-line interface for batch processing
- **API**: RESTful API for integration with other systems

### Install

1. Ensure Python 3.10+ is installed.
2. In PowerShell:

```bash
py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

### Deploy to Vercel

1. Ensure your account has the Python runtime enabled.
2. Push this repository to GitHub.
3. Import the project in Vercel.
4. Set Environment Variable (optional): `CSV_FILE_PATH` to a CSV URL or path.
5. Vercel will deploy using `vercel.json` routing:
   - Serverless function at `api/index.py` serves all API routes
   - Static files served from project root (we serve `static/index.html` via route to `/`)

Endpoints available on Vercel:

- `POST /generate`
- `GET /issue-types` and `GET /api/issue-types`
- `GET /csv-info` and `GET /api/csv-info`
- `GET /validate/{issue_type}` and `GET /api/validate/{issue_type}`
- `POST /api/upload-csv` (multipart)

### Web Frontend Usage

Start the server:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

Open your browser and go to: `http://localhost:8000`

The web interface provides:
- Dropdown with all issue types from CSV
- Auto-suggestions based on VOC input
- Real-time validation against CSV knowledge base
- Beautiful, responsive design

### CLI Usage

```bash
py cli.py --issue "Ordered by Mistake" --voc "I accidentally ordered the wrong product, did not open the package." --stock No --follow 25-06-2025
```

Output is printed in the exact LOB template.

### API Usage

Start the server:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

#### Generate LOB Summary

```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "issue_type": "Ordered by Mistake",
    "voc": "I accidentally ordered the wrong product, did not open the package.",
    "stock_available": "No",
    "follow_up_date": "25-06-2025"
  }'
```

#### Get Issue Types from CSV

```bash
curl http://localhost:8000/api/issue-types
```

#### Get CSV Information

```bash
curl http://localhost:8000/api/csv-info
```

#### Validate Issue Type

```bash
curl http://localhost:8000/api/validate/Ordered%20by%20Mistake
```

### CSV Knowledge Base

The application automatically loads issue types, VOC examples, and SOP rules from:
`Copy of Knowledge Hub - Premium Electronics- Queue 1 -  Electronics Policy.csv`

The CSV parser extracts:
- Issue types (e.g., "Ordered by Mistake", "Expectation Mismatch")
- VOC examples for each issue type
- Resolution rules for different tiers (Gold, Silver & Bronze, New & Iron)
- SOP details and procedures

### Project Structure

```
├── lob_app/
│   ├── __init__.py
│   ├── generator.py      # Core LOB generation logic
│   └── csv_parser.py     # CSV knowledge base parser
├── static/
│   ├── index.html        # Web frontend
│   └── script.js         # Frontend JavaScript
├── api.py                # FastAPI server with endpoints
├── cli.py                # Command-line interface
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

### Response Format

The API returns LOB summaries in the exact template format:

```
Brief summary of customer concern: Ordered by Mistake / By mistake ordered / Service No

DP/SM call: NA

Resolution shared along with the reason: Service No – As per SOP for accidental orders, no RPU is initiated for unintended purchases. Customer advised politely.

Stock/Slot Available: No

Offered resolution: Service No

Customer response: Pending

Follow up – date and time: 25-06-2025
```


