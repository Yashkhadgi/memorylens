# MemoryLens Backend

This is the backend for MemoryLens, a FastAPI application that provides powerful search capabilities using both Face Recognition and Document parsing.

## Features

* **Face Search Pipeline**: Uses AWS Rekognition to index faces from images and allows searching for specific people using a reference photo.
* **Document Search Pipeline**: Parses PDF and DOCX files, creates vector embeddings for the text, and stores them in a local FAISS index for fast semantic search.
* **Unified API**: A single endpoint (`/api/index`) to trigger background indexing for both faces and documents in a given folder.

## Setup Instructions

1.  **Install Dependencies**:
    Requires Python 3.9+. Install the dependencies using pip:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Environment Variables**:
    Create a `.env` file in this backend directory based on `.env.example`. You will need to provide your AWS credentials for the face recognition pipeline.
    ```env
    AWS_ACCESS_KEY_ID=your_key
    AWS_SECRET_ACCESS_KEY=your_secret
    AWS_REGION=your_region
    ```

3.  **Run the Server**:
    Start the FastAPI server using Uvicorn:
    ```bash
    uvicorn main:app --reload --port 8000
    ```

    The API will be available at `http://localhost:8000`. You can view the automated API documentation at `http://localhost:8000/docs`.

## Key Files

*   `main.py`: The main FastAPI application routing requests to the respective pipelines.
*   `face_indexer.py` & `face_search.py`: Handles AWS Rekognition logic for faces.
*   `doc_indexer.py` & `doc_search.py`: Handles text extraction, embedding generation, and FAISS indexing for documents. 
