# cython: cdivision=True

cpdef bytearray decrypt(unsigned char *data, int data_len, unsigned char *key, int key_len, unsigned char *scramble, int scramble_len, unsigned char counter):
    cdef unsigned int output_idx = 0
    cdef unsigned int idx = 0
    cdef unsigned int even_bit_shift = 0
    cdef unsigned int odd_bit_shift = 0
    cdef unsigned int is_even_bit_set = 0
    cdef unsigned int is_odd_bit_set = 0
    cdef unsigned int is_key_bit_set = 0
    cdef unsigned int is_scramble_bit_set = 0
    cdef unsigned int is_counter_bit_set = 0
    cdef unsigned int is_counter_bit_inv_set = 0
    cdef unsigned int cur_bit = 0
    cdef unsigned int output_word = 0

    output_data = bytearray(data_len * 2)

    while idx < data_len:
        output_word = 0
        cur_data = (data[(idx * 2) + 1] << 8) | data[(idx * 2)]

        cur_bit = 0
        while cur_bit < 8:
            even_bit_shift = (cur_bit * 2) & 0xff
            odd_bit_shift = (cur_bit * 2 + 1) & 0xff

            is_even_bit_set = int((cur_data & (1 << even_bit_shift)) != 0)
            is_odd_bit_set = int((cur_data & (1 << odd_bit_shift)) != 0)
            is_key_bit_set = int((key[idx % key_len] & (1 << cur_bit)) != 0)
            is_scramble_bit_set = int((scramble[idx % scramble_len] & (1 << cur_bit)) != 0)
            is_counter_bit_set = int((counter & (1 << cur_bit)) != 0)
            is_counter_bit_inv_set =  int(counter & (1 << ((7 - cur_bit) & 0xff)) != 0)

            if is_scramble_bit_set == 1:
                is_even_bit_set, is_odd_bit_set = is_odd_bit_set, is_even_bit_set

            if ((is_even_bit_set ^ is_counter_bit_inv_set ^ is_key_bit_set)) == 1:
                output_word |= 1 << even_bit_shift

            if (is_odd_bit_set ^ is_counter_bit_set) == 1:
                output_word |= 1 << odd_bit_shift

            cur_bit += 1

        output_data[output_idx] = (output_word >> 8) & 0xff
        output_data[output_idx+1] = output_word & 0xff
        output_idx += 2

        counter += 1

        idx += 1

    return output_data


cpdef bytearray encrypt(unsigned char *data, int data_len, unsigned char *key, int key_len, unsigned char *scramble, int scramble_len, unsigned char counter):
    cdef unsigned int output_idx = 0
    cdef unsigned int idx = 0
    cdef unsigned int even_bit_shift = 0
    cdef unsigned int odd_bit_shift = 0
    cdef unsigned int is_even_bit_set = 0
    cdef unsigned int is_odd_bit_set = 0
    cdef unsigned int is_key_bit_set = 0
    cdef unsigned int is_scramble_bit_set = 0
    cdef unsigned int is_counter_bit_set = 0
    cdef unsigned int is_counter_bit_inv_set = 0
    cdef unsigned int cur_bit = 0
    cdef unsigned int output_word = 0
    cdef unsigned int set_even_bit = 0
    cdef unsigned int set_odd_bit = 0

    output_data = bytearray(data_len * 2)

    while idx < data_len:
        output_word = 0
        cur_data = (data[(idx * 2)] << 8) | data[(idx * 2) + 1]

        cur_bit = 0
        while cur_bit < 8:
            even_bit_shift = (cur_bit * 2) & 0xff
            odd_bit_shift = (cur_bit * 2 + 1) & 0xff

            is_even_bit_set = int((cur_data & (1 << even_bit_shift)) != 0)
            is_odd_bit_set = int((cur_data & (1 << odd_bit_shift)) != 0)
            is_key_bit_set = int((key[idx % key_len] & (1 << cur_bit)) != 0)
            is_scramble_bit_set = int((scramble[idx % scramble_len] & (1 << cur_bit)) != 0)
            is_counter_bit_set = int((counter & (1 << cur_bit)) != 0)
            is_counter_bit_inv_set =  int(counter & (1 << ((7 - cur_bit) & 0xff)) != 0)

            set_even_bit = is_even_bit_set ^ is_counter_bit_inv_set ^ is_key_bit_set
            set_odd_bit = is_odd_bit_set ^ is_counter_bit_set

            if is_scramble_bit_set == 1:
                set_even_bit, set_odd_bit = set_odd_bit, set_even_bit

            if set_even_bit == 1:
                output_word |= 1 << even_bit_shift

            if set_odd_bit == 1:
                output_word |= 1 << odd_bit_shift

            cur_bit += 1

        output_data[output_idx] = output_word & 0xff
        output_data[output_idx+1] = (output_word >> 8) & 0xff
        output_idx += 2

        counter += 1

        idx += 1

    return output_data
