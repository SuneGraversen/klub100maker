import argparse
import csv
import os
from yt_dlp import YoutubeDL
from pydub import AudioSegment


parser = argparse.ArgumentParser(description="A tool for creating klub100 tracks")
parser.add_argument("filename", type=str, help="The path to the input file to be parsed")
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
    def inner(songs, acc):
        if len(songs) == 0:
            return acc
        head = songs[0]
        tail = songs[1:]
        if not os.path.exists("songs/" + head[0] + ".wav"):
            print(f"Error: The file 'songs/{head[0]}.wav' does not exist. Skipping this song.")
            return inner(tail, acc)
        print(f"Merging number '{head[0]}'; '{head[1]}' from {head[2]}...")
        curSong = AudioSegment.from_wav("songs/" + head[0] + ".wav")
        # convert start end to seconds
        start = 0
        end = 1000*60
        if head[3] != "" and head[4] != "":
            start = 1000*minsectosec(head[3])
            end =   1000*minsectosec(head[4])
        newAcc = acc + curSong[start:end]
        del curSong
        return inner(tail, newAcc)

    full_mix = inner(sortedSongs, AudioSegment.empty())
    full_mix.export("klub100.wav", format="wav")


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