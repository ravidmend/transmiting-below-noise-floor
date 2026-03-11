#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from gnuradio import gr


class decoder(gr.sync_block):

    def __init__(self, Ts, pn_len, fs):

        gr.sync_block.__init__(
            self,
            name="decoder",
            in_sig=[np.complex64],
            out_sig=None,
        )

        self.fs = fs

        self.sps = 4
        self.preamble_reps = 5

        np.random.seed(0)
        self.pn = np.random.choice([-1, 1], pn_len).astype(np.float32)

        self.pn_len = pn_len

        self.pn_pulse = np.repeat(self.pn, self.sps)

        self.preamble = np.tile(self.pn_pulse, self.preamble_reps)

        self.symbol_len = len(self.pn_pulse)
        self.preamble_len = len(self.preamble)

        self.buffer = np.array([], dtype=np.complex64)

        self.detected = False

        self.bit_buffer = []
        self.message = ""


    def correlate(self, x, ref):

        return np.correlate(x, np.conj(ref), mode="valid")


    def detect_preamble(self):

        if len(self.buffer) < self.preamble_len:
            return False

        corr = self.correlate(self.buffer, self.preamble)

        abs_corr = np.abs(corr)

        peak = np.max(abs_corr)
        noise = np.mean(abs_corr)
        print("peak:", peak, "noise:", noise,"index:", np.argmax(abs_corr))
        if peak > 5 * noise:

            idx = np.argmax(abs_corr)

            print("PREAMBLE DETECTED")

            self.buffer = self.buffer[idx + self.preamble_len :]

            return True

        self.buffer = self.buffer[-self.preamble_len :]

        return False


    def decode_symbol(self):

        if len(self.buffer) < self.symbol_len:
            return None

        sym = self.buffer[: self.symbol_len]

        self.buffer = self.buffer[self.symbol_len :]

        val = np.vdot(self.pn_pulse, sym)

        bit = 1 if np.real(val) > 0 else 0

        return bit


    def process_bit(self, bit):

        self.bit_buffer.append(bit)

        print("bit:", bit)

        if len(self.bit_buffer) == 8:

            value = 0

            for b in self.bit_buffer:
                value = (value << 1) | b

            char = chr(value)

            print("char:", char)

            self.message += char

            print("message:", self.message)

            self.bit_buffer = []


    def work(self, input_items, output_items):

        in0 = input_items[0]

        self.buffer = np.concatenate((self.buffer, in0))

        while True:

            if not self.detected:

                if not self.detect_preamble():
                    break

                self.detected = True

            bit = self.decode_symbol()

            if bit is None:
                break

            self.process_bit(bit)

        return len(in0)