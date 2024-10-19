from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from pydub import AudioSegment

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
NORMALIZED_FOLDER = "normalized"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(NORMALIZED_FOLDER, exist_ok=True)


@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())
    normalized_filename = normalize_file(file_path)
    normalized_file_url = f"/normalized/{normalized_filename}"
    return {"filename": file.filename, "normalized_file_url": normalized_file_url}


@app.get("/normalized/{filename}")
async def get_normalized_file(filename: str):
    file_path = os.path.join(NORMALIZED_FOLDER, filename)
    return FileResponse(file_path)


def normalize_file(file_path):
    audio = AudioSegment.from_file(file_path)
    normalized_audio = match_target_amplitude(audio, -20.0)
    output_file = os.path.join(NORMALIZED_FOLDER, os.path.basename(file_path))
    normalized_audio.export(output_file, format="mp3", bitrate="320k")
    return os.path.basename(output_file)


def match_target_amplitude(sound, target_dBFS):
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound.apply_gain(change_in_dBFS)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
