#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 shira.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy as np
from gnuradio import gr

class decoder(gr.sync_block):
    """
    docstring for block decoder
    """
    def __init__(self, Ts, pn_len, fs):
        gr.sync_block.__init__(self,
            name="decoder",
            in_sig=[np.complex64],
            out_sig=None)

        self.Ts = Ts
        self.fs = fs

        sps = 4
        preamble_reps = 5

        self.sps = sps
        self.preamble_reps = preamble_reps

        # relative detection threshold
        self.k_thresh = 6

        pn_sequence = np.array([1]*pn_len)
        self.pn = np.array(pn_sequence, dtype=np.float32)
        self.pn_len = len(self.pn)

        # rectangular pulse shaping
        self.pn_pulse = np.repeat(self.pn, self.sps).astype(np.complex64)

        # PREAMBLE = PN repeated N times
        self.preamble_pulse = np.tile(self.pn_pulse, self.preamble_reps)

        # queue buffer
        self.buffer = np.array([], dtype=np.complex64)

        self.detected = False
        self.symbol_len = len(self.pn_pulse)
        self.preamble_len = len(self.preamble_pulse)

        # bit/char storage
        self.bit_buffer = []
        self.char_buffer = ""


    def correlate(self, x, ref):
        return np.correlate(x, np.conj(ref), mode='valid')


    def detect_preamble(self):

        if len(self.buffer) < self.preamble_len:
            return False

        corr = self.correlate(self.buffer, self.preamble_pulse)

        abs_corr = np.abs(corr)

        peak = np.max(abs_corr)
        noise = np.mean(abs_corr)

        if peak > self.k_thresh * noise:

            idx = np.argmax(abs_corr)

            print("PREAMBLE DETECTED")

            # align buffer after preamble
            self.buffer = self.buffer[idx + self.preamble_len:]

            return True

        # prevent unbounded growth
        self.buffer = self.buffer[-self.preamble_len:]

        return False


    def process_bit(self, bit):

        self.bit_buffer.append(bit)

        if len(self.bit_buffer) == 8:

            value = 0
            for b in self.bit_buffer:
                value = (value << 1) | b

            char = chr(value)

            print("char detected:", char)

            self.char_buffer += char

            print("message so far:", self.char_buffer)

            self.bit_buffer = []


    def decode_symbol(self):

        if len(self.buffer) < self.symbol_len:
            return None

        sym = self.buffer[:self.symbol_len]

        val = np.vdot(self.pn_pulse, sym)

        self.buffer = self.buffer[self.symbol_len:]

        bit = 1 if np.real(val) > 0 else 0

        return bit


    def work(self, input_items, output_items):

        in0 = input_items[0]

        # append incoming samples
        self.buffer = np.concatenate((self.buffer, in0))

        while True:

            if not self.detected:

                if not self.detect_preamble():
                    break

                self.detected = True

            bit = self.decode_symbol()

            if bit is None:
                break

            print("bit is:", bit)

            self.process_bit(bit)

        return len(in0)