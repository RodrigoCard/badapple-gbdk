from PIL import Image
import os

# Configurações
WIDTH = 112
HEIGHT = 72
FRAMES = 4383
FPS = 15

MAP_WIDTH = 14
MAP_HEIGHT = 9
ANIMATION_FRAME_COUNT = FRAMES

BASE_PNG_DIR = 'pngs'             # Pasta de origem
BASE_PNG_PATH = BASE_PNG_DIR + '/png%d.png'
OUTPUT_DIR = 'res'         # Pasta de destino
DATA_FILE = 'src/data.c'
DATA_HEADER = 'src/data.h'
os.makedirs(OUTPUT_DIR, exist_ok=True)  # Cria se não existir

header_list = []  # Lista para armazenar nomes para o include
frame_list = []   # Lista para armazenar os frames

frame_idx = 1

for i in range(0, FRAMES, 60 // FPS):
    input_path = BASE_PNG_PATH % (i + 1)
    
    with Image.open(input_path).resize((WIDTH, HEIGHT)) as im:
        im = im.convert('L')  # Escala de cinza
        im = im.point(lambda p: 0 if p < 125 else 255, 'L')  # Binariza
        palette_im = im.convert('P', palette=Image.ADAPTIVE, colors=2)
        
        # Forçar paleta preto e branco
        palette = [0, 0, 0, 255, 255, 255] + [0, 0, 0] * 253
        palette_im.putpalette(palette)
        
        # Nome de saída com 4 dígitos, ex: png0001.png
        output_filename = f'f{frame_idx:04}.png'
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        
        palette_im.save(output_path)

        # Monta strings para o CSV C-like
        header_name = f'f{frame_idx:04}'
        header_list.append(f'#include "{header_name}.h"')
        frame_list.append(f'    {{.tiles = {header_name}_tiles, .bank = BANK({header_name})}}')

        frame_idx += 1

ANIMATION_FRAME_COUNT = frame_idx-1

with open(DATA_HEADER, 'w') as f:
    f.write('#ifndef __DATA_H_INCLUDE__\n')
    f.write('#define __DATA_H_INCLUDE__\n')
    f.write('#include <stdint.h>\n\n')
    f.write(f'#define MAP_WIDTH {MAP_WIDTH}\n')
    f.write(f'#define MAP_HEIGHT {MAP_HEIGHT}\n')
    f.write(f'#define ANIMATION_FRAME_COUNT {ANIMATION_FRAME_COUNT}\n')
    f.write('typedef struct frame_desc_t {\n\
    const uint8_t * tiles;\n\
    uint8_t bank;\n\
} frame_desc_t;\n\
extern const frame_desc_t frames[ANIMATION_FRAME_COUNT];\n\
#endif\n')
    f.write('\n')

# Agora, salva o arquivo output_list.csv nesse formato
with open(DATA_FILE, 'w') as f:
    f.write('#pragma bank 0\n')
    f.write('#include <gbdk/platform.h>\n')
    f.write('#include <stdint.h>\n\n')
    f.write('#include "data.h"\n\n')
    
    # Includes dos headers
    for header in header_list:
        f.write(header + '\n')
    
    f.write('\n')
    f.write('const frame_desc_t frames[ANIMATION_FRAME_COUNT] = {\n')
    
    # Lista de frames
    f.write(',\n'.join(frame_list))
    f.write('\n};\n')
