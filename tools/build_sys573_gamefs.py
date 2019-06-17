import argparse
import ctypes
import glob
import json
import os
import pathlib
import struct

def get_filename_hash(filename):
    hash = 0

    for cidx, c in enumerate(filename):
        for i in range(6):
            hash = ctypes.c_int(((hash >> 31) & 0x4c11db7) ^ ((hash << 1) | ((ord(c) >> i) & 1))).value

    return hash & 0xffffffff


def encrypt_data(data, input_key):
    def calculate_key(input):
        key = 0

        for c in input.upper():
            if c in string.ascii_uppercase:
                key -= 0x37

            elif c in string.ascii_lowercase:
                key -= 0x57

            elif c in string.digits:
                key -= 0x30

            key += ord(c)

        return key & 0xff

    val = 0x41C64E6D
    key1 = (val * calculate_key(input_key)) & 0xffffffff
    counter = 0

    # TODO: Verify that this works for encryption too
    for idx, c in enumerate(data):
        val = ((key1 + counter) >> 5) ^ c
        data[idx] = val & 0xff
        counter += 0x3039

    return data


def get_filetable(input_folder):
    entries = []

    metadata_path = os.path.join(input_folder, "_metadata.json")
    if os.path.exists(metadata_path):
        entries = json.load(open(metadata_path))

        entry_idx = max([entry.get('idx', 0) for entry in entries]) + 1

        for entry in entries:
            entry['_path'] = os.path.join(input_folder, entry['filename'])
            entry['filesize'] = os.path.getsize(entry['_path'])

            if 'idx' not in entry:
                entry['idx'] = entry_idx
                entry_idx += 1

            if 'filename_hash' not in entry:
                entry['filename_hash'] = get_filename_hash(entry['filename'])

    else:
        files = [str(pathlib.Path(*pathlib.Path(f).parts[1:])) for f in glob.glob(os.path.join(input_folder, "**"), recursive=True) if os.path.isfile(f) and "_metadata.json" not in f]

        for c in files:
            c = c.replace("\\", "/")

            filename_hash = get_filename_hash(c)

            filename = os.path.splitext(os.path.basename(c))[0]
            if filename.startswith("_output_"):
                filename_hash = int(filename[len("_output_"):], 16)

            entry = {
                '_path': os.path.join(input_folder, c),
                'filename': c,
                'filename_hash': filename_hash,
                'filesize': os.path.getsize(os.path.join(input_folder, c)),
                'flag_comp': False,
                'flag_enc': False,
            }

            entries.append(entry)

    return sorted(entries, key=lambda x: x['filename_hash'])


def create_gamedata(entries, base_offset, memory_size=0x01000000):
    memory = bytearray([0xff] * memory_size)
    memory_map = bytearray([0] * memory_size)

    file_table_size = len(entries) * 0x10
    file_table_size += 0x800 - (file_table_size % 0x800)

    first_half_start = 0
    first_half_size = base_offset
    second_half_start = base_offset + file_table_size
    second_half_size = memory_size - (base_offset + file_table_size)

    # Find the data
    entries_work = entries[::]
    cur_memory = first_half_start

    for entry in entries_work[::]:
        if 'offset' in entry:
            cur_memory = entry['offset']
            memory[cur_memory:cur_memory + entry['filesize']] = bytearray(open(entry['_path'], "rb").read())
            memory_map[cur_memory:cur_memory + entry['filesize']] = [1] * entry['filesize']
            entries_work.remove(entry)

    for entry in entries_work[::]:
        cur_memory = 0

        while cur_memory < 0x00f00000:
            idx = memory_map.find(0, cur_memory)

            if idx == -1:
                break

            cur_memory = idx
            idx = memory_map[cur_memory:cur_memory + entry['filesize']].find(1)

            if idx != -1:
                cur_memory += idx

            else:
                 break


        if cur_memory == -1 or cur_memory >= 0x00f00000:
            print("Couldn't find position for", entry)
            exit(1)

        print("Placing @ %08x" % cur_memory)

        memory[cur_memory:cur_memory + entry['filesize']] = bytearray(open(entry['_path'], "rb").read())
        memory_map[cur_memory:cur_memory + entry['filesize']] = [1] * entry['filesize']

        for e in entries:
            if e == entry:
                e['offset'] = cur_memory

        entries_work.remove(entry)


    for idx, entry in enumerate(entries):
        memory[base_offset + (idx * 0x10):base_offset + ((idx + 1) * 0x10)] = struct.pack("<IIII", entry['filename_hash'], entry['offset'], entry['filesize'], entry.get('flags', 0))

    return memory


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--input', help='Input folder', default=None, required=True)
    parser.add_argument('--output', help='Output file', default="output.dat")
    parser.add_argument('--key', help='Encryption key', choices=['EXTREME', 'EURO2', 'MAX2', 'DDR5', 'MAMBO'])
    parser.add_argument('--type', help='Game Type', choices=['ddr', 'gfdm', 'mambo'])

    args = parser.parse_args()

    if args.type == "ddr":
        base_offset = 0xFE4000

    elif args.type == "gfdm":
        base_offset = 0x198000

    elif args.type == "mambo":
        base_offset = 0xFE4000

    else:
        print("Unknown format!")
        exit(1)

    filetable = get_filetable(args.input)
    gamedata = create_gamedata(filetable, base_offset)

    open(args.output, "wb").write(gamedata)
