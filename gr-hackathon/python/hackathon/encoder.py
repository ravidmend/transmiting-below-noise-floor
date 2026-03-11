#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from gnuradio import gr
from queue import Queue


class encoder(gr.sync_block):

    def __init__(self, string_input, pn_len, sps, fs):
        gr.sync_block.__init__(
            self,
            name="encoder",
            in_sig=None,
            out_sig=[np.complex64],
        )

        self.string_input = string_input
        self.sps = sps
        self.fs = fs
        self.pn_len = pn_len

        np.random.seed(0)
        self.pn = np.random.randint(0, 2, self.pn_len).astype(np.float32)

        self.preamble = [1,0,1,0]

        self.pn_pulse = np.repeat(self.pn, self.sps)
        self.preamble = np.tile(self.pn_pulse, self.preamble_reps)

        self.queue = Queue()
        self.generated = False



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
        pn_repeated = np.tile(pn_bits, len(duplicated) // len(pn_bits))

        # XOR
        result = np.bitwise_xor(duplicated, pn_repeated)

        return result

    def spread(self, bits):

        symbols = 2 * bits - 1  # BPSK

        chips = []

        for s in symbols:
            chips.append(s * self.pn)

        chips = np.concatenate(chips)

        samples = np.repeat(chips, self.sps)

        return samples




    def generate_packet(self):

        bits = self.string_to_bits(self.string_input)

        payload = self.spread(bits)

        packet = np.concatenate([self.preamble, payload])

        return packet.astype(np.complex64)


    def work(self, input_items, output_items):

        out = output_items[0]
        n = len(out)

        if not self.generated:

            packet = self.generate_packet()

            self.queue.put(packet)

            self.generated = True


        if self.queue.empty():

            out[:] = np.zeros(n, dtype=np.complex64)

            return n


        data = self.queue.get()

        if len(data) > n:

            out[:] = data[:n]

            self.queue.put(data[n:])

        else:

            out[:len(data)] = data
            out[len(data):] = 0


        return n