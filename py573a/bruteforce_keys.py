import argparse
import base64
import binascii
import itertools

import hexdump

import bruteforce
import enc573

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('--input-dat', help='Input ciphertext file', required=True)
    parser.add_argument('--input-plain', help='Input plaintext file', required=True)
    parser.add_argument('--counter', help='Counter value', type=lambda x: int(x, 0), required=True)

    args = parser.parse_args()

    counter = args.counter

    data = open(args.input_dat, "rb").read()
    data_mp3 = open(args.input_plain, "rb").read()

    min_size = min(len(data), len(data_mp3))
    data = data[:min_size]
    data = data[:min_size]

    key_build, scramble_build, likely_key_size = bruteforce.bruteforce_key(data, len(data), data_mp3, len(data_mp3), counter)
    key_build = key_build[:likely_key_size]
    scramble_build = scramble_build[:likely_key_size]

    # Find scramble key, reusing existing key to reduce the search space greatly.
    # Set cur_idx to a smaller number toward the end of the file for optimization reasons.
    # If the key is inaccurate, increase the amount of data to comb through here
    cur_idx = len(data_mp3) - (likely_key_size * 8)
    scramble_build = bruteforce.bruteforce_scramble_key(data, len(data), data_mp3, len(data_mp3), counter, cur_idx, key_build, scramble_build)

    # Calculate final scramble pattern
    samples = [scramble_build[i:i + likely_key_size] for i in range(0, len(scramble_build), likely_key_size) if len(scramble_build[i:i + likely_key_size]) == likely_key_size]
    scramble_pattern = samples[0]

    for sample in samples[1:]:
        for idx, c in enumerate(sample):
            scramble_pattern[idx] |= c

    print("Key:", base64.b64encode(key_build).decode('ascii'))
    hexdump.hexdump(key_build)
    print()

    print("Scramble:", base64.b64encode(scramble_pattern).decode('ascii'))
    hexdump.hexdump(scramble_pattern)
