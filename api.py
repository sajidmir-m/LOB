from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from lob_app import generate_lob_summary
from lob_app.csv_parser import CSVParser
import os
from typing import Dict, Any, List


app = FastAPI(title="LOB Summary Generator", version="1.0.0")

# Mount static files using an absolute path so it works on serverless
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_STATIC_DIR = os.path.join(_BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=_STATIC_DIR), name="static")

# Initialize CSV parser (env override supported) with robust path resolution
def _resolve_csv_path(path: str) -> str:
    # If absolute and exists, return
    if os.path.isabs(path) and os.path.exists(path):
        return path
    # Try relative to CWD
    if os.path.exists(path):
        return os.path.abspath(path)
    # Try relative to project base (next to api.py)
    candidate = os.path.join(_BASE_DIR, path)
    if os.path.exists(candidate):
        return candidate
    return path  # Let downstream raise helpful error

csv_file_path = _resolve_csv_path(os.getenv(
    "CSV_FILE_PATH",
    "Copy of Knowledge Hub - Premium Electronics- Queue 1 -  Electronics Policy.csv",
))
csv_parser = CSVParser(csv_file_path)


def reload_csv_parser(new_csv_path: str) -> None:
    """Reload the global CSV parser with a new CSV file path."""
    global csv_parser, csv_file_path
    if not os.path.exists(new_csv_path):
        raise FileNotFoundError(f"CSV file not found at path: {new_csv_path}")
    csv_file_path = new_csv_path
    csv_parser = CSVParser(csv_file_path)


class GenerateRequest(BaseModel):
    issue_type: str = Field(..., description="Issue type label, e.g., 'Ordered by Mistake'")
    voc: str = Field(..., description="Customer statement / Voice of Customer")
    stock_available: str | bool = Field(..., description="Yes/No or boolean")
    follow_up_date: str | None = Field(None, description="Optional follow up date")
    dp_sm_call: str | None = Field(None, description="Optional DP/SM call value; default NA")


class GenerateResponse(BaseModel):
    summary: str
    csv_validation: Dict[str, Any] | None = None


class IssueTypesResponse(BaseModel):
    issue_types: List[str]
    knowledge_base: Dict[str, Any]


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page."""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


@app.get("/api/issue-types", response_model=IssueTypesResponse)
def get_issue_types():
    """Get all available issue types from CSV knowledge base."""
    try:
        issue_types = csv_parser.get_issue_types()
        knowledge_base = csv_parser.knowledge_base
        return IssueTypesResponse(
            issue_types=issue_types,
            knowledge_base=knowledge_base
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading CSV data: {str(e)}")


@app.post("/generate", response_model=GenerateResponse)
def generate(req: GenerateRequest) -> GenerateResponse:
    """Generate LOB summary with CSV validation."""
    try:
        # Generate the LOB summary
        summary = generate_lob_summary(
            issue_type=req.issue_type,
            voc=req.voc,
            stock_available=req.stock_available,
            follow_up_date=req.follow_up_date,
            dp_sm_call=req.dp_sm_call,
        )
        
        # Get CSV validation data
        csv_validation = get_csv_validation(req.issue_type, req.voc)
        
        return GenerateResponse(
            summary=summary,
            csv_validation=csv_validation
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating LOB summary: {str(e)}")


def get_csv_validation(issue_type: str, voc: str) -> Dict[str, Any]:
    """Get CSV-based validation and suggestions."""
    validation = {}
    
    try:
        # Find best matching issue type
        best_match = csv_parser.find_best_match(f"{issue_type} {voc}")
        if best_match:
            validation["matched_issue_type"] = best_match
            
            # Get resolution for the matched issue type
            resolution = csv_parser.get_resolution(best_match, "gold")
            validation["suggested_resolution"] = resolution
            
            # Get SOP details
            sop_details = csv_parser.get_sop_details(best_match)
            validation["sop_details"] = sop_details
            
            # Get VOC examples
            voc_examples = csv_parser.get_voc_examples(best_match)
            validation["voc_examples"] = voc_examples[:3]  # Limit to 3 examples
        
        return validation
        
    except Exception as e:
        print(f"Error in CSV validation: {e}")
        return {}


@app.get("/api/csv-info")
def get_csv_info():
    """Get information about the CSV knowledge base."""
    try:
        issue_types = csv_parser.get_issue_types()
        total_issues = len(issue_types)
        
        return {
            "total_issue_types": total_issues,
            "csv_file": csv_file_path,
            "issue_types": issue_types,
            "status": "loaded"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting CSV info: {str(e)}")


@app.post("/api/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV file and reload the knowledge base.

    Accepts multipart/form-data with a single 'file' field.
    Saves to ./uploads and reloads the CSV parser.
    """
    try:
        if not file.filename.lower().endswith(".csv"):
            raise HTTPException(status_code=400, detail="Only .csv files are supported")

        # Use /tmp on Vercel (serverless is read-only except /tmp); fallback to local 'uploads'
        uploads_dir = os.getenv("UPLOADS_DIR") or ("/tmp" if os.getenv("VERCEL") else os.path.join(_BASE_DIR, "uploads"))
        os.makedirs(uploads_dir, exist_ok=True)
        destination_path = os.path.join(uploads_dir, file.filename)

        # Save file to disk
        content = await file.read()
        with open(destination_path, "wb") as f:
            f.write(content)

        # Reload parser
        reload_csv_parser(destination_path)

        issue_types = csv_parser.get_issue_types()
        return {
            "message": "CSV uploaded and loaded successfully",
            "csv_file": destination_path,
            "total_issue_types": len(issue_types),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading CSV: {str(e)}")


@app.get("/api/validate/{issue_type}")
def validate_issue_type(issue_type: str):
    """Validate a specific issue type against CSV data."""
    try:
        if issue_type in csv_parser.knowledge_base:
            data = csv_parser.knowledge_base[issue_type]
            return {
                "issue_type": issue_type,
                "exists": True,
                "voc_examples": data.get("voc_examples", []),
                "resolutions": data.get("resolutions", {}),
                "sop_details": data.get("sop_details", "")
            }
        else:
            return {
                "issue_type": issue_type,
                "exists": False,
                "suggestions": csv_parser.get_issue_types()
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error validating issue type: {str(e)}")


# Duplicate routes without "/api" prefix for Vercel serverless compatibility
@app.get("/issue-types", response_model=IssueTypesResponse)
def get_issue_types_plain():
    return get_issue_types()


@app.get("/csv-info")
def get_csv_info_plain():
    return get_csv_info()


@app.get("/validate/{issue_type}")
def validate_issue_type_plain(issue_type: str):
    return validate_issue_type(issue_type)


