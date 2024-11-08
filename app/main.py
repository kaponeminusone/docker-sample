
from fastapi import FastAPI, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
import os
import subprocess
import shutil

app = FastAPI()

UPLOADS_DIR = "uploads"
os.makedirs(UPLOADS_DIR, exist_ok=True)

@app.post("/compile-latex/")
async def compile_latex(file: UploadFile, background_tasks: BackgroundTasks):
    if file.content_type != "application/x-tex":
        raise HTTPException(status_code=400, detail="Invalid file type")

    tex_path = os.path.join(UPLOADS_DIR, file.filename)
    pdf_output_path = os.path.join(UPLOADS_DIR, file.filename.replace(".tex", ".pdf"))

    with open(tex_path, "wb") as tex_file:
        tex_file.write(await file.read())

    try:
        subprocess.run(
            ["pdflatex", "-output-directory", UPLOADS_DIR, "-interaction=nonstopmode", tex_path],
            check=True
        )
    except subprocess.CalledProcessError:
        cleanup_uploads()
        raise HTTPException(status_code=500, detail="LaTeX compilation failed")

    if not os.path.exists(pdf_output_path):
        cleanup_uploads()
        raise HTTPException(status_code=500, detail="PDF file not generated")

    background_tasks.add_task(cleanup_uploads)  # Limpieza en segundo plano después de servir el archivo
    return FileResponse(pdf_output_path, media_type="application/pdf", filename="output.pdf")

def cleanup_uploads():
    for file in os.listdir(UPLOADS_DIR):
        file_path = os.path.join(UPLOADS_DIR, file)
        os.remove(file_path)
