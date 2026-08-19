import argparse
import csv
import os
from yt_dlp import YoutubeDL
from pydub import AudioSegment


parser = argparse.ArgumentParser(description="A tool for creating klub100 tracks")
parser.add_argument("filename", type=str, help="The path to the input file to be parsed")
#optional fade argument with ms
parser.add_argument("--fade", type=int, default=500, help="The fade in/out duration in milliseconds (default: 500ms)")
parser.add_argument("-o", type=str, default="klub100.wav", help="The output filename (default: klub100.wav)")
args = parser.parse_args()
if not args.filename:
    print("Error: No filename provided.")
    exit(1)


def download_songs(sortedSongs):
    try:
        os.mkdir("songs")
    except FileExistsError:
        pass
    
    for song in sortedSongs:
        curnum = song[0]
        if os.path.exists(f"songs/{curnum}.wav"):
          print(f"Skipping number '{song[0]}'; '{song[1]}' from {song[2]} as it already exists...")
          continue  

        print(f"Downloading number '{song[0]}'; '{song[1]}' from {song[2]}...")
        opts = {
            "format": "bestaudio/best",
            "cookiesfrombrowser": ("safari",),
            "remote_components": ["ejs:github"],
            "noplaylist": True,
            "outtmpl": f"songs/{curnum}.%(ext)s",
            "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
        }],
        }
        ydl = YoutubeDL(opts)
        try:
            ydl.download([song[2]])
        except Exception as e:
            print(f"Error downloading '{song[1]}' from {song[2]}: {e}")
            continue

def minsectosec(minsec):
    if minsec == "":
        minsec = "0:00"
    m, s = map(int, minsec.split(":"))
    total_seconds = m * 60 + s
    return total_seconds

def merge_songs(sortedSongs):
    clips = []

    for head in sortedSongs:
        song_path = f"songs/{head[0]}.wav"

        if not os.path.exists(song_path):
            print(f"Error: The file '{song_path}' does not exist. Skipping this song.")
            continue

        print(f"Merging number '{head[0]}'; '{head[1]}' from {head[2]}...")
        curSong = AudioSegment.from_wav(song_path)

        start = 0
        end = 1000 * 60
        if head[3] != "" and head[4] != "":
            start = 1000 * minsectosec(head[3])
            end = 1000 * minsectosec(head[4])

        clips.append(curSong[start:end].fade_in(args.fade).fade_out(args.fade))

        # check if speak exists, and if it does, add it to clips
        try:
            speak_path = f"speaks/{head[0]}_speak.wav"
            curSpeak = AudioSegment.from_wav(speak_path)
            clips.append(curSpeak)
        except FileNotFoundError:
            print(f"Warning: The speak file '{speak_path}' does not exist. Skipping this speak.")

    full_mix = AudioSegment.empty()
    print("Merging all clips to single track")
    for clip in clips:
        full_mix += clip
    print("Exporting final track to klub100.wav")
    full_mix.export(args.o, format="wav")


try:
    with open(args.filename, 'r') as file:
        songlistreader = csv.reader(file)
        next(songlistreader)  # Skip the header row
        sortedSongs = sorted(songlistreader, key=lambda x: (int(x[0])))  # Sort by artist and then by title
        download_songs(sortedSongs)
        merge_songs(sortedSongs)

except FileNotFoundError:
    print(f"Error: The file '{args.filename}' was not found.")
    exit(1)