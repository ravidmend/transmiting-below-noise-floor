#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from gnuradio import gr

class decoder(gr.sync_block):

    def __init__(self, pn_len, sps, recived_amp):
        gr.sync_block.__init__(
            self,
            name="decoder",
            in_sig=[np.complex64],
            out_sig=None,
        )

        self.sps = sps
        self.pn_len = pn_len
        self.buffer = np.array([], dtype=np.complex64)
        self.detection_mode = True
        self.recived_amp = recived_amp

        # Preamble as bits
        preamble_bits = np.array([1,1,0,1,0,0,0,1,1,0,1,1,1,0,1,0], dtype=np.uint8)

        # PN sequence as integers (needed for bitwise operations)
        np.random.seed(0)
        pn = np.random.randint(0, 2, pn_len).astype(np.uint8)
        self.pn_bits = pn

        # BPSK-modulated PN for correlation
        modulated_pn = self.bpsk_mod(pn)
        pulse_shaped_pn = np.repeat(modulated_pn, sps)
        self.pn = pulse_shaped_pn

        # Prepare preamble waveform (spread + BPSK + pulse shaping)
        spreaded_preamble = self.spread_bits(preamble_bits, pn, pn_len)
        modulated_preamble = self.bpsk_mod(spreaded_preamble)
        pulse_shaped_preamble = np.repeat(modulated_preamble, sps)
        self.preamble = pulse_shaped_preamble
        self.preamble_len = len(self.preamble)

        # Symbol length = PN length * samples per symbol
        self.symbol_len = pn_len * sps

        # Buffers for bits and decoded message
        self.bit_buffer = []
        self.message = ""

    # ---- Utility Methods ----

    def correlate(self, x, ref):
        """Compute correlation (conjugate dot product)."""
        return np.correlate(x, np.conj(ref), mode="full")

    def detect_preamble(self):
        """Check if preamble exists in the buffer."""
        if len(self.buffer) < self.preamble_len:
            return False

        corr = self.correlate(self.buffer, self.preamble)
        abs_corr = np.abs(corr)
        peak = np.max(abs_corr)
        threshold = 0.8 * self.recived_amp * self.preamble_len

        if peak > threshold:
            idx = np.argmax(abs_corr)
            print("PREAMBLE DETECTED")
            self.buffer = self.buffer[idx+1:]
            return True

        # Keep only the last preamble_len-1 samples for sliding window
        self.buffer = self.buffer[-(self.preamble_len-1):]
        return False

    def decode_symbol(self):
        """Decode one symbol from the buffer using PN correlation."""
        if len(self.buffer) < self.symbol_len:
            return None

        sym = self.buffer[:self.symbol_len]
        self.buffer = self.buffer[self.symbol_len:]
        val = np.vdot(self.pn, sym)
        bit = 1 if np.real(val) > 0 else 0
        return bit

    def process_bit(self, bit):
        """Collect bits into bytes and convert to ASCII."""
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

    def checktimeout(self):
        """Reset detection if no valid symbol is received."""
        if len(self.buffer) < self.symbol_len:
            return None

        sym = self.buffer[:self.symbol_len]
        val = np.vdot(self.pn, sym)

        if np.abs(val) > 0.5 * self.recived_amp * self.symbol_len:
            return False

        print("TIMEOUT")
        self.detection_mode = True
        self.bit_buffer = []
        self.message = ""
        return True

    # ---- Bit and PN operations ----

    def string_to_bits(self, string):
        bits = []
        for c in string:
            ascii_val = ord(c)
            bin_str = format(ascii_val, '08b')  # 8-bit ASCII
            bits.extend(int(b) for b in bin_str)
        return np.array(bits, dtype=np.uint8)

    def spread_bits(self, data_bits, pn_bits, pn_len):
        """Duplicate each bit n times and XOR with PN sequence."""
        duplicated = np.repeat(data_bits, pn_len)
        pn_repeated = np.tile(pn_bits, len(data_bits))
        result = np.bitwise_xor(duplicated, pn_repeated)
        return result

    def bpsk_mod(self, bits: np.ndarray) -> np.ndarray:
        bits = np.asarray(bits)
        return 2*bits - 1  # 0 -> -1, 1 -> +1

    # ---- GNU Radio work method ----

    def work(self, input_items, output_items):
        in0 = input_items[0]
        self.buffer = np.concatenate((self.buffer, in0))

        while True:
            if self.detection_mode:
                if not self.detect_preamble():
                    break
                self.detection_mode = False

            if self.checktimeout():
                break

            bit = self.decode_symbol()
            if bit is None:
                break

            self.process_bit(bit)

        return len(in0)