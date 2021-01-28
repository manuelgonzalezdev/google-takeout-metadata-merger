# Google Takeout metadata Merger

### Previous notes

This script was code for personal use quickly and without focusing on quality or best practices. I'm sure can be optimized, cleaned and refactored.

## Motivation

The goal of this code is fix the piece of shit Google made with Takeout downloading GPhotos content splitting media and metadata.
The script scan path given trying to find out creation date (cdate) of each `media` search json files or filenames.

### Media extensions included to scanning

- jpg
- png
- gif
- mov
- mp4
- dng

## Requirements

- Python 3.8 or greater

## Usage

```
python fixer.py {path}
```

### Arguments

`path`: A valid path where media files were extracted.

### Results

Script creates a `out` folder inside of path specified where copy media and fixes all possible metadata.
Every media cannot be repairable is copied to `out/_failed` folder.
