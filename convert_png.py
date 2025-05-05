#
#   Bad apple dataset conversion
#   adapted from here: https://github.com/kevinjycui/bad-apple/blob/master/preprocess/main.py
#
from PIL import Image
import os
import hashlib

# config
WIDTH = 112
HEIGHT = 72
FRAMES = 4383
FPS = 30

MAP_WIDTH = 14
MAP_HEIGHT = 9

BASE_PNG_DIR = 'pngs'
BASE_PNG_PATH = BASE_PNG_DIR + '/png%d.png'
OUTPUT_DIR = 'res'
DATA_FILE = 'src/data.c'
DATA_HEADER = 'src/data.h'

os.makedirs(OUTPUT_DIR, exist_ok=True)

header_list = []
frame_list = []
output_files = []   # save in generation order

print(f"Converting {FRAMES} frames {WIDTH}x{HEIGHT}@{FPS}fps...")

# main conversion
frame_idx = 1
for i in range(0, FRAMES, 60 // FPS):
    input_path = BASE_PNG_PATH % (i + 1)
    with Image.open(input_path).resize((WIDTH, HEIGHT)) as im:
        im = im.convert('L')
        im = im.point(lambda p: 0 if p < 125 else 255, 'L')
        palette_im = im.convert('P', palette=Image.ADAPTIVE, colors=2)
        palette = [0,0,0, 255,255,255] + [0,0,0]*253
        palette_im.putpalette(palette)

        name = f'f{frame_idx:04}'
        out_png = os.path.join(OUTPUT_DIR, name + '.png')
        palette_im.save(out_png)

        output_files.append(name)  
        frame_idx += 1

ANIMATION_FRAME_COUNT = len(output_files)

# detect dupes by hash
hash_to_original = {}
duplicates = {}   # name -> original

print("Finding duplicated frames...")

for name in output_files:
    path = os.path.join(OUTPUT_DIR, name + '.png')
    data = open(path,'rb').read()
    h = hashlib.md5(data).hexdigest()
    if h in hash_to_original:
        # already existed, dupe
        duplicates[name] = hash_to_original[h]
    else:
        hash_to_original[h] = name

# delete dupes
for dup in duplicates:
    os.remove(os.path.join(OUTPUT_DIR, dup + '.png'))

# reconstruct header_list e frame_list, changing dupes to point to originals
new_header_list = []
new_frame_list  = []
included_headers = set()

print("Generating header files...")

for name in output_files:
    # if dupe, point to original
    original = duplicates.get(name, name)
    # dont include the same header more than once
    if original not in included_headers:
        new_header_list.append(f'#include "{original}.h"')
        included_headers.add(original)
    new_frame_list.append(
        f'    {{.tiles = {original}_tiles, .bank = BANK({original}_tiles)}}'
    )

# data.h
with open(DATA_HEADER, 'w') as f:
    f.write('#ifndef __DATA_H_INCLUDE__\n#define __DATA_H_INCLUDE__\n')
    f.write('#include <stdint.h>\n\n')
    f.write(f'#define MAP_WIDTH {MAP_WIDTH}\n')
    f.write(f'#define MAP_HEIGHT {MAP_HEIGHT}\n')
    f.write(f'#define ANIMATION_FRAME_COUNT {ANIMATION_FRAME_COUNT}\n\n')
    f.write('typedef struct frame_desc_t {\n'
            '    const uint8_t * tiles;\n'
            '    uint8_t bank;\n'
            '} frame_desc_t;\n\n')
    f.write('extern const frame_desc_t frames[ANIMATION_FRAME_COUNT];\n')
    f.write('#endif\n')

# data.c
with open(DATA_FILE, 'w') as f:
    f.write('#pragma bank 0\n')
    f.write('#include <gbdk/platform.h>\n#include <stdint.h>\n\n')
    f.write('#include "data.h"\n\n')
    for h in new_header_list:
        f.write(h + '\n')
    f.write('\nconst frame_desc_t frames[ANIMATION_FRAME_COUNT] = {\n')
    f.write(',\n'.join(new_frame_list))
    f.write('\n};\n')

# show stats
total = len(output_files)
dups  = len(duplicates)
unique = len(hash_to_original)

print(f"Total frames converted:           {total}")
print(f"Duplicated frames found:          {dups}")
print(f"Unique frames after removal:      {unique}")