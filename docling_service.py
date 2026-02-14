import logging
import os
import signal
import sys
import tempfile
from typing import Optional

import structlog
import uvicorn
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from fastapi import FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

# Configure structured logging (JSON format for Coolify)
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Configuration from environment variables
API_KEY = os.getenv("DOCLING_SERVICE_API_KEY", "")
PORT = int(os.getenv("PORT", "8000"))
WORKERS = int(os.getenv("WORKERS", "2"))
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(50 * 1024 * 1024)))  # 50MB default
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# Log startup configuration
logger.info(
    "service_starting",
    port=PORT,
    workers=WORKERS,
    max_file_size_mb=MAX_FILE_SIZE / (1024 * 1024),
    api_key_configured=bool(API_KEY),
    allowed_origins=ALLOWED_ORIGINS,
)

app = FastAPI(title="Docling PDF Processing Service", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def verify_api_key(api_key: Optional[str]):
    """Verify the provided API key."""
    if API_KEY and api_key != API_KEY:
        logger.warning("invalid_api_key_attempt")
        raise HTTPException(status_code=401, detail="Invalid API key")


@app.get("/health")
async def health_check():
    """Health check endpoint for Coolify."""
    return {"status": "healthy", "service": "docling-pdf-processor", "version": "1.0.0"}


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "Docling PDF Processing Service",
        "version": "1.0.0",
        "endpoints": {"health": "/health", "convert": "/convert-pdf"},
    }


@app.post("/convert-pdf")
async def convert_pdf_to_text(
    file: UploadFile = File(...),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
):
    """Convert PDF file to markdown text."""
    # Verify API key
    verify_api_key(x_api_key)

    # Validate file type
    if not file.filename.lower().endswith(".pdf"):
        logger.warning("invalid_file_type", filename=file.filename)
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    temp_path = None
    try:
        # Read file content
        content = await file.read()

        # Check file size
        if len(content) > MAX_FILE_SIZE:
            logger.warning(
                "file_too_large",
                filename=file.filename,
                size_bytes=len(content),
                max_size_bytes=MAX_FILE_SIZE,
            )
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum limit of {MAX_FILE_SIZE / (1024 * 1024):.0f}MB",
            )

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        logger.info(
            "processing_file",
            filename=file.filename,
            size_bytes=len(content),
            temp_path=temp_path,
        )

        # Configure pipeline options
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = True
        pipeline_options.do_table_structure = True
        pipeline_options.table_structure_options.do_cell_matching = True

        # Create converter
        converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=pipeline_options, backend=PyPdfiumDocumentBackend
                )
            }
        )

        # Convert document
        result = converter.convert(temp_path)
        markdown_text = result.document.export_to_markdown()

        logger.info(
            "conversion_successful",
            filename=file.filename,
            output_length=len(markdown_text),
        )

        return {
            "status": "success",
            "filename": file.filename,
            "text_length": len(markdown_text),
            "markdown": markdown_text,
        }

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(
            "conversion_error", filename=file.filename, error=str(e), exc_info=True
        )
        raise HTTPException(
            status_code=500, detail="An error occurred while processing the PDF file"
        )
    finally:
        # Clean up temporary file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                logger.debug("temp_file_cleaned", path=temp_path)
            except Exception as e:
                logger.error("temp_file_cleanup_failed", path=temp_path, error=str(e))


# Graceful shutdown handler
def handle_shutdown(signum, frame):
    logger.info("shutdown_signal_received", signal=signum)
    sys.exit(0)


signal.signal(signal.SIGTERM, handle_shutdown)
signal.signal(signal.SIGINT, handle_shutdown)

# Only run uvicorn directly if not running under gunicorn
if __name__ == "__main__":
    logger.info("starting_direct_mode", port == PORT, workers=1)
    uvicorn.run(app, host="0.0.0.0", port=PORT, workers=1)
