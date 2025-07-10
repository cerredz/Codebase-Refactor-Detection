from fastapi import FastAPI, File, UploadFile
from typing import List
import os
import shutil

app = FastAPI()
UPLOAD_DIR = os.path.join(os.path.pardir(__file__), "codebase")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/refactor")
async def refactor(files: List[UploadFile] = File(...)):
    saved_files = []
    for file in files:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_files.append(file.filename)
    return {"saved_files": saved_files}