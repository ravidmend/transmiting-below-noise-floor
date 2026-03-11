#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from gnuradio import gr
from queue import Queue


class encoder(gr.sync_block):

    def __init__(self, string_input, pn_len, sps):
        gr.sync_block.__init__(
            self,
            name="encoder",
            in_sig=None,
            out_sig=[np.complex64],
        )

        np.random.seed(0)
        pn = np.random.randint(0, 2, pn_len).astype(np.float32)

        preamble = [1,0,1,0]

        bits_to_send = np.concatenate([preamble,self.string_to_bits(string_input)])

        spreaded_bits = self.spread_bits(bits_to_send, pn, pn_len)

        modulated_bits = self.bpsk_mod(spreaded_bits)

        pulse_shaped = np.repeat(modulated_bits, sps) 
        self.signal = pulse_shaped


    def string_to_bits(self, string):
        bits = []

        for c in string:
            ascii_val = ord(c)
            bin_str = format(ascii_val, '08b')  # 8-bit ASCII
            for b in bin_str:
                bits.append(int(b))

        return np.array(bits, dtype=np.uint8)


    def spread_bits(self,data_bits, pn_bits, pn_len):  # duplicate and xor
        # duplicate each bit n times
        duplicated = np.repeat(data_bits, pn_len)

        # repeat the PN sequence to match the length
        pn_repeated = np.tile(pn_bits,len(pn_bits))

        # XOR
        result = np.bitwise_xor(duplicated, pn_repeated)

        return result
    

    def bpsk_mod(bits: np.ndarray) -> np.ndarray:
        bits = np.asarray(bits)
        return 2*bits - 1


def work(self, input_items, output_items):
    out = output_items[0]
    n = len(out)

    available = len(self.signal)

    if available >= n:
        out[:] = self.signal[:n]
        self.signal = self.signal[n:]
    else:
        out[:available] = self.signal
        out[available:] = 0
        self.signal = np.array([], dtype=self.signal.dtype)

    return n