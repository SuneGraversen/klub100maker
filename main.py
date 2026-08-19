import argparse
import csv
import os
from yt_dlp import YoutubeDL
from pydub import AudioSegment


parser = argparse.ArgumentParser(description="A tool for creating klub100 tracks")
parser.add_argument("filename", type=str, help="The path to the input file to be parsed")
#optional fade argument with ms
parser.add_argument("--fade", type=int, default=800, help="The fade in/out duration in milliseconds (default: 800ms)")
parser.add_argument("-o", type=str, default="klub100.wav", help="The output filename (default: klub100.wav)")
parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without downloading or merging songs")
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
        curname = song[1].replace(" ", "_")
        if os.path.exists(f"songs/{curname}.wav"):
          print(f"Skipping number '{song[0]}'; '{song[1]}' from {song[2]} as it already exists...")
          continue  

        print(f"Downloading number '{song[0]}'; '{song[1]}' from {song[2]}...")
        opts = {
            "format": "bestaudio/best",
            "cookiesfrombrowser": ("safari",),
            "remote_components": ["ejs:github"],
            "noplaylist": True,
            "outtmpl": f"songs/{curname}.%(ext)s",
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

def match_target_amplitude(sound, target_dBFS):
    change_in_dBFS = target_dBFS - sound.dBFS
    return sound + change_in_dBFS

def merge_songs(sortedSongs):
    clips = []

    for head in sortedSongs:
        song_path = f"songs/{head[1].replace(' ', '_')}.wav"

        if not os.path.exists(song_path):
            print(f"Error: The file '{song_path}' does not exist. Skipping this song.")
            continue

        start = 0
        end = 1000 * 60
        if head[3] != "":
            start = 1000 * minsectosec(head[3])
        if head[4] == "":
            end = start+(1000*60)
        else:
            end = 1000 * minsectosec(head[4])

        print(f"Merging number '{head[0]}'; '{head[1]}' from {head[2]} ({start/1000}s - {end/1000}s)...")
        curSong = AudioSegment.from_wav(song_path)

        # check if speak exists, and if it does, add it to clips
        try:
            speak_path = f"speaks/{head[1].replace(' ', '_')}.wav"
            curSpeak = AudioSegment.from_wav(speak_path)
            clips.append(curSpeak)
        except FileNotFoundError:
            print(f"Warning: The speak file '{speak_path}' does not exist. Skipping this speak.")

        clips.append(curSong[start:end].fade_in(args.fade).fade_out(args.fade))

    clips = [match_target_amplitude(clip, -14.0) for clip in clips]
    full_mix = AudioSegment.empty()
    if not args.dry_run:
        print("Merging all clips to single track")
        for clip in clips:
            full_mix += clip
        print("Exporting final track to klub100.wav")
        full_mix.export(args.o, bitrate="256k", format="wav")

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