# cython: cdivision=True

import enc573

cpdef int find_key_size(unsigned char *key, int key_len, int counter_step=1):
    cdef unsigned int ks = 0
    cdef unsigned int idx = 0
    cdef unsigned int i = 0
    cdef unsigned int j = 0
    cdef unsigned int k = 0
    cdef unsigned int is_match = 0
    cdef unsigned int available_chunks = 0
    cdef unsigned int max_key_size = 0
    cdef int max_key_size_idx = -1
    cdef unsigned int key_sizes[8]
    cdef unsigned int confidence[8]

    idx_step = 0x10 if counter_step == 0 else 0x1e

    idx = idx_step

    while idx < key_len:
        found = True if idx + 10 >= key_len else False

        while found and j < 10:
            if key[j] != key[idx+j]:
                found = False

            j += 1

        if found:
            return idx

        idx += idx_step

    return -1


cdef int is_match(unsigned char *a, int a_len, unsigned char *b, int b_len, int idx, int block_size):
    cdef int match = 0
    cdef unsigned int i = idx * 2
    cdef unsigned int min_val = min(a_len, b_len)

    while i < min_val:
        if a[i] != b[i] or a[i+1] != b[i+1]:
            match = 0
            break

        else:
            match = 1

        i += block_size * 2

    return match


cpdef bruteforce_key(unsigned char *data, int data_len, unsigned char *data_mp3, int data_mp3_len, unsigned char counter, int counter_step=1):
    cdef unsigned int MAX_KEY_LEN = 0xf0

    cdef unsigned int i = 0
    cdef unsigned int j = 0
    cdef unsigned int cur_idx = 0
    cdef int key_build_len = 0
    cdef int scramble_build_len = 0
    cdef int chunk_size = 0

    key_build = bytearray()
    scramble_build = bytearray()

    while cur_idx + 1 < data_mp3_len:
        likely_key_size = find_key_size(key_build, key_build_len, counter_step)

        if likely_key_size != -1:
            break

        cur_key_len = len(key_build)

        found_match = False
        i = 0
        while i <= 0xff:
            j = 0

            while j <= 0xff:
                key = key_build + bytearray([i])
                scramble = scramble_build + bytearray([j])

                chunk = data[:cur_idx+2]
                chunk_size = len(chunk) // 2
                output = enc573.decrypt(chunk, chunk_size, key, key_build_len + 1, scramble, scramble_build_len + 1, counter, counter_step)

                # TODO: Rewrite this check to be more Cythonic
                if output[:cur_idx+2] == data_mp3[:cur_idx+2]:
                    key_build = key
                    scramble_build = scramble
                    key_build_len += 1
                    scramble_build_len += 1
                    found_match = True
                    break

                j += 1

            if found_match:
                break

            i += 1

        if len(key_build) == cur_key_len:
            return None, None, None

        #if len(key_build) >= MAX_KEY_LEN:
        #    break

        cur_idx += 2

    return key_build, scramble_build, likely_key_size


cpdef bruteforce_key_counter(unsigned char *data, int data_len, unsigned char *data_mp3, int data_mp3_len):
    cdef unsigned int MAX_KEY_LEN = 0xf0

    cdef unsigned int i = 0
    cdef unsigned int j = 0
    cdef unsigned int counter = 0
    cdef unsigned int cur_idx = 0
    cdef int key_build_len = 0
    cdef int scramble_build_len = 0
    cdef int chunk_size = 0
    cdef int max_key = 0x100
    cdef int found_counter = 0

    key_build = bytearray()
    scramble_build = bytearray()

    while cur_idx + 1 < data_mp3_len:
        likely_key_size = find_key_size(key_build, key_build_len)

        if likely_key_size != -1:
            break

        cur_key_len = len(key_build)

        found_match = False
        i = 0
        while i <= 0xff:
            j = 0

            while j <= 0xff:
                if not found_counter:
                    counter = 0

                while counter < max_key:
                    key = key_build + bytearray([i])
                    scramble = scramble_build + bytearray([j])

                    chunk = data[:cur_idx+2]
                    chunk_size = len(chunk) // 2
                    output = enc573.decrypt(chunk, chunk_size, key, key_build_len + 1, scramble, scramble_build_len + 1, counter)

                    # TODO: Rewrite this check to be more Cythonic
                    if output[:cur_idx+2] == data_mp3[:cur_idx+2]:
                        key_build = key
                        scramble_build = scramble
                        key_build_len += 1
                        scramble_build_len += 1
                        found_match = True
                        break

                    counter += 1

                if found_match and not found_counter:
                    max_key = counter + 1
                    found_counter = 1
                    print("Found counter: %02x" % (counter))
                    break

                if found_match:
                    break

                j += 1

            if found_match:
                break

            i += 1

        if len(key_build) == cur_key_len:
            continue

        cur_idx += 2

    return key_build, scramble_build, likely_key_size, counter


cpdef bruteforce_scramble_key(unsigned char *data, int data_len, unsigned char *data_mp3, int data_mp3_len, unsigned char counter, unsigned int cur_idx, key_build, scramble_build, int counter_step=1):
    cdef unsigned int j = 0
    cdef int key_size = len(key_build)
    cdef int key_build_len = len(key_build)
    cdef int scramble_build_len = len(scramble_build)
    cdef int chunk_size = 0
    cdef int output_len = 0
    cdef int c = 0

    while cur_idx + 1 < data_mp3_len:
        c = (cur_idx // 2) % scramble_build_len

        j = 0
        while j < 0x100:
            if scramble_build[c] == j:
                j += 1
                continue

            scramble = scramble_build[::]
            scramble[c] = j

            chunk = data[:cur_idx+2]
            chunk_size = len(chunk) // 2
            output = enc573.decrypt(chunk, chunk_size, key_build, key_build_len, scramble, scramble_build_len, counter, counter_step)
            output_len = len(output)

            if is_match(output, output_len, data_mp3, data_mp3_len, c, key_size) == 1:
                scramble_build = scramble
                break

            j += 1

        cur_idx += 2

    return scramble_build
