import os
import threading
from pydub import AudioSegment
from tkinter import Tk, StringVar, messagebox
from tkinter.filedialog import askdirectory
from tkinter import ttk
from mutagen.id3 import ID3, ID3NoHeaderError


class AudioNormalizer:
    def __init__(self):
        self.root = Tk()
        self.root.title("Audio Normalizer")
        self.root.geometry("400x200")

        self.style = ttk.Style()
        self.style.configure("TLabel", font=("Arial", 12), padding=10)
        self.style.configure("TButton", font=("Arial", 12), padding=10)

        self.intro_label = ttk.Label(
            self.root, text="Select a directory to normalize audio files."
        )
        self.intro_label.pack()

        self.label_text = StringVar()
        self.label = ttk.Label(self.root, textvariable=self.label_text)
        self.label.pack()

        self.file_label_text = StringVar()
        self.file_label = ttk.Label(self.root, textvariable=self.file_label_text)
        self.file_label.pack()

        self.cancelling_label = ttk.Label(self.root, text="Cancelling...")

        self.select_button = ttk.Button(
            self.root, text="Select Directory", command=self.select_directory
        )
        self.select_button.pack()

        self.stop_button = ttk.Button(
            self.root, text="Stop", command=self.stop_normalization
        )
        self.stop_requested = False

        self.close_button = ttk.Button(self.root, text="Close", command=self.root.quit)

        self.image_label = ttk.Label(self.root)
        self.image_label.pack()

        self.image_path = None

        self.thread = None

    def normalize_files(self, folder_path):
        output_folder = os.path.join(folder_path, "normalized")
        os.makedirs(output_folder, exist_ok=True)
        files = [file for file in os.listdir(folder_path) if file.endswith(".mp3")]
        total_files = len(files)

        if total_files == 0:
            self.label_text.set("No audio files found in the selected directory.")
            self.select_button.pack()
            return

        self.stop_button.pack()

        for i, file in enumerate(files):
            if self.stop_requested:
                break

            self.label_text.set(f"Normalizing {i + 1}/{total_files}...")
            self.file_label_text.set(f"Current File: {file}")
            self.root.update()

            audio = AudioSegment.from_file(os.path.join(folder_path, file))
            normalized_audio = self.match_target_amplitude(audio, -20.0)

            cover_output_path = None

            try:
                # Extract the cover image
                mp3 = ID3(os.path.join(folder_path, file))
                for tag in mp3.getall("APIC"):
                    cover_data = tag.data
                    cover_output_path = os.path.join(output_folder, "cover.jpg")
                    with open(cover_output_path, "wb") as f:
                        f.write(cover_data)
            except ID3NoHeaderError:
                print(f"No ID3 tag found for {file}")

            output_file = os.path.join(output_folder, file)

            if cover_output_path:
                normalized_audio.export(
                    output_file,
                    format="mp3",
                    bitrate="320k",
                    cover=cover_output_path,
                )
            else:
                normalized_audio.export(
                    output_file,
                    format="mp3",
                    bitrate="320k",
                )

            print(f"Normalized {i + 1}/{total_files} - {file}")

        if self.stop_requested:
            self.label_text.set("Volume normalization cancelled.")
        else:
            self.label_text.set("Volume normalization success.")

        self.file_label_text.set("")
        self.stop_button.pack_forget()
        self.cancelling_label.pack_forget()
        self.close_button.pack()

    def match_target_amplitude(self, sound, target_dBFS):
        change_in_dBFS = target_dBFS - sound.dBFS
        return sound.apply_gain(change_in_dBFS)

    def select_directory(self):
        folder_path = askdirectory()
        if folder_path:
            self.intro_label.pack_forget()
            self.select_button.pack_forget()
            self.thread = threading.Thread(
                target=self.normalize_files, args=(folder_path,)
            )
            self.thread.start()

    def stop_normalization(self):
        result = messagebox.askyesno(
            "Stop Normalization",
            "Are you sure you want to stop the volume normalization?",
        )
        if result:
            self.stop_requested = True
            self.stop_button.pack_forget()
            self.cancelling_label.pack()

    def run(self):
        self.root.mainloop()
        if self.thread and self.thread.is_alive():
            self.stop_requested = True
            self.thread.join()


if __name__ == "__main__":
    normalizer = AudioNormalizer()
    normalizer.run()
