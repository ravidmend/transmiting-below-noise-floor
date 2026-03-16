#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 shira.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from gnuradio import gr


class decoder(gr.sync_block):
    """
    Decoder with preamble detection.
    Expected preamble: [1,1,1,1,1]
    Input: float32 stream from encoder
    Output: no output, prints decoded message
    """

    def __init__(self, pn_length, sps, msg_len, thresh=6, key=0):
        gr.sync_block.__init__(
            self,
            name="decoder",
            in_sig=[np.float32],
            out_sig=None
        )

        self.__thresh__ = thresh
        self.pn_length = int(pn_length)
        self.sps = int(sps)
        self.msg_len = int(msg_len)

        # Must match encoder exactly
        #key = 
        np.random.seed(key)
        self.pn_bits = np.random.randint(0, 2, self.pn_length).astype(np.float32) 
        

        # Preamble = five 1s
        self.preamble_bits = np.array([1, 0, 0, 1, 1, 0, 1, 1, 1], dtype=np.uint8)

        # Buffer for incoming samples
        self.buffer = np.array([], dtype=np.float32)

        # State
        self.detected = False
        self.done = False
        self.bit_buffer = []
        self.char_buffer = ""

        # Build reference symbol waveforms
        self.symbol0 = self.build_symbol_template(0)
        self.symbol1 = self.build_symbol_template(1)

        self.symbol_len = len(self.symbol0)

        # Full waveform of the preamble
        self.preamble_waveform = np.tile(self.symbol1, len(self.preamble_bits))
        self.preamble_len = len(self.preamble_waveform)

    def build_symbol_template(self, bit):
        """
        Build exactly the same waveform the encoder creates for one bit.
        """
        bit_arr = np.array([bit], dtype=np.uint8)

        repeated_bit = np.repeat(bit_arr, self.pn_length)
        spread_bits = np.logical_xor(repeated_bit, self.pn_bits)

        bpsk = spread_bits.astype(np.float32)
        bpsk[bpsk == 0] = -1.0

        pulse = np.repeat(bpsk, self.sps).astype(np.float32)
        return pulse

    def detect_preamble(self):
        """
        Search for preamble in the buffer using correlation.
        """
        if len(self.buffer) < self.preamble_len:
            return False

        corr = np.correlate(self.buffer, self.preamble_waveform, mode='valid')
        abs_corr = np.abs(corr)

        idx = int(np.argmax(abs_corr))
        peak = abs_corr[idx]
        print(f"[decoder] preamble correlation peak: {peak:.2f} at index {idx}")

        # Simple threshold
        thresh = 0.8 * np.sum(self.preamble_waveform ** 2)
        thresh = self.__thresh__

        if peak >= thresh:
            print(f"[decoder] PREAMBLE DETECTED at index {idx}, peak={peak:.2f}")

            # Remove samples up to the end of the preamble
            self.buffer = self.buffer[idx + self.preamble_len:]
            return True

        # Keep only enough trailing samples so buffer does not grow forever
        if len(self.buffer) > self.preamble_len:
            self.buffer = self.buffer[-self.preamble_len:]

        return False

    def decode_one_bit(self):
        """
        Decode one spread symbol from buffer.
        """
        if len(self.buffer) < self.symbol_len:
            return None

        sym = self.buffer[:self.symbol_len]
        self.buffer = self.buffer[self.symbol_len:]

        score0 = np.dot(sym, self.symbol0)
        score1 = np.dot(sym, self.symbol1)

        bit = 0 if score0 > score1 else 1
        return bit

    def process_bit(self, bit):
        self.bit_buffer.append(bit)

        if len(self.bit_buffer) == 8:
            value = 0
            for b in self.bit_buffer:
                value = (value << 1) | b

            # ASCII only
            if 32 <= value <= 126:
                char = chr(value)
            else:
                char = '?'

            print(f"[decoder] bits: {self.bit_buffer}")
            print(f"[decoder] byte: {value} ({format(value, '08b')})")
            print(f"[decoder] char: {char}")

            self.char_buffer += char
            self.bit_buffer = []

            print(f"[decoder] message so far: {self.char_buffer}")

            if len(self.char_buffer) >= self.msg_len:
                print(f"\n[decoder] FINAL MESSAGE: {self.char_buffer[:self.msg_len]}\n")
                self.done = True

    def work(self, input_items, output_items):
        in0 = input_items[0]

        if self.done:
            return len(in0)

        # Add new samples to buffer
        self.buffer = np.concatenate((self.buffer, in0))

        while True:
            if not self.detected:
                if not self.detect_preamble():
                    break
                self.detected = True

            bit = self.decode_one_bit()
            if bit is None:
                break

            print(f"[decoder] decoded bit: {bit}")
            self.process_bit(bit)

            if self.done:
                break

        return len(in0)
















# import numpy as np
# from gnuradio import gr


# class decoder(gr.sync_block):
#     """
#     Decoder for the given encoder.
#     Input: float32 stream from the encoder
#     Output: no output (sink) - prints recovered string
#     """
#     def __init__(self, pn_length, sps, msg_len):
#         gr.sync_block.__init__(
#             self,
#             name="decoder",
#             in_sig=[np.float32],
#             out_sig=None
#         )

#         self.pn_length = int(pn_length)
#         self.sps = int(sps)
#         self.msg_len = int(msg_len)

#         # Must match encoder exactly
#         self.pn_bits = np.array([1] * self.pn_length, dtype=np.uint8)
#         self.preamble_bits = np.array([1, 1, 1, 1, 1], dtype=np.uint8)

#         # Internal buffer
#         self.buffer = np.array([], dtype=np.float32)

#         # Decoder state
#         self.detected = False
#         self.done = False
#         self.bit_buffer = []
#         self.char_buffer = ""

#         # Build symbol templates
#         # Encoder does:
#         # spread_bit = bit XOR pn_bit
#         # then 0 -> -1, 1 -> +1
#         #
#         # So template for bit=0 is:
#         #   bpsk(pn_bits)
#         #
#         # template for bit=1 is:
#         #   negative of that
#         self.symbol0 = self.build_symbol_template(bit=0)
#         self.symbol1 = self.build_symbol_template(bit=1)

#         self.symbol_len = len(self.symbol0)

#         # Preamble waveform = 5 symbols of bit=1
#         self.preamble_waveform = np.tile(self.symbol1, len(self.preamble_bits))
#         self.preamble_len = len(self.preamble_waveform)

#     def build_symbol_template(self, bit):
#         # Spread one bit with PN exactly like encoder
#         bit_array = np.array([bit], dtype=np.uint8)

#         repeated_bit = np.repeat(bit_array, self.pn_length)
#         spread_bits = repeated_bit ^ self.pn_bits

#         # BPSK map: 0 -> -1, 1 -> +1
#         bpsk = spread_bits.astype(np.float32)
#         bpsk[bpsk == 0] = -1.0

#         # Rectangular pulse shaping
#         pulse = np.repeat(bpsk, self.sps).astype(np.float32)

#         return pulse

#     def detect_preamble(self):
#         if len(self.buffer) < self.preamble_len:
#             return False

#         corr = np.correlate(self.buffer, self.preamble_waveform, mode='valid')
#         abs_corr = np.abs(corr)

#         idx = int(np.argmax(abs_corr))
#         peak = abs_corr[idx]
        

#         # In noiseless/direct connection this should be very large
#         # compared to mismatches, so a simple threshold works
#         thresh = 0.8 * np.sum(self.preamble_waveform ** 2)
#         thresh = 6
#         if peak >= thresh:
#             print(f"[decoder] preamble correlation peak: {peak:.2f} at index {idx}")
#             print("[decoder] PREAMBLE DETECTED")

#             # Remove everything up to the end of the preamble
#             self.buffer = self.buffer[idx + self.preamble_len:]
#             return True

#         # Keep only enough trailing samples
#         if len(self.buffer) > self.preamble_len:
#             self.buffer = self.buffer[-self.preamble_len:]

#         return False

#     def decode_one_bit(self):
#         if len(self.buffer) < self.symbol_len:
#             return None

#         sym = self.buffer[:self.symbol_len]
#         self.buffer = self.buffer[self.symbol_len:]

#         # Compare correlation with bit-0 and bit-1 templates
#         score0 = np.dot(sym, self.symbol0)
#         score1 = np.dot(sym, self.symbol1)

#         bit = 0 if score0 > score1 else 1
#         return bit

#     def process_bit(self, bit):
#         self.bit_buffer.append(bit)

#         if len(self.bit_buffer) == 8:
#             value = 0
#             for b in self.bit_buffer:
#                 value = (value << 1) | b

#             char = chr(value)
#             self.char_buffer += char
#             self.bit_buffer = []

#             print(f"[decoder] char detected: {char}")
#             print(f"[decoder] message so far: {self.char_buffer}")

#             if len(self.char_buffer) == self.msg_len:
#                 print(f"\n[decoder] FINAL MESSAGE: {self.char_buffer}\n")
#                 self.done = True

#     def work(self, input_items, output_items):
        
#         in0 = input_items[0]

#         if self.done:
#             return len(in0)

#         # Append incoming samples
#         self.buffer = np.concatenate((self.buffer, in0))

#         while True:
#             # print(2)
#             if not self.detected:
#                 if not self.detect_preamble():
#                     break
#                 self.detected = True

#             print(3)
#             bit = self.decode_one_bit()
#             print(f"[decoder] decoded bit: {bit}")
#             if bit is None:
#                 break

#             #print(f"[decoder] bit: {bit}")
#             self.process_bit(bit)

#             if self.done:
#                 break

#         return len(in0)








# import numpy as np
# from gnuradio import gr
# from queue import Queue

# class decoder(gr.sync_block):
#     """
#     docstring for block decoder
#     """
#     def __init__(self, fs, pn_len, sps):
#         gr.sync_block.__init__(self,
#             name="decoder",
#             in_sig=[np.complex64],
#             out_sig=None)

#         self.__pn__ = np.array([1]*int(pn_len)) # example pn sequence
#         self.__queue__ = Queue()
#         self.__fs__ = fs
#         self.__sps__ = sps









#     def correlate(self, x, ref):
#         return np.correlate(x, np.conj(ref), mode='valid')


#     def detect_preamble(self):

#         if len(self.buffer) < self.preamble_len:
#             return False

#         corr = self.correlate(self.buffer, self.preamble_pulse)

#         abs_corr = np.abs(corr)

#         peak = np.max(abs_corr)
#         noise = np.mean(abs_corr)
#         print(f"peak: {peak:.2f}, noise: {noise:.2f}, ratio: {peak/noise:.2f}")

#         # if peak > self.k_thresh * noise:
#         if peak > 10000:

#             idx = np.argmax(abs_corr)
#             print(f"preamble detected at index {idx}, correlation value: {corr[idx]:.2f}")
#             print("PREAMBLE DETECTED")

#             # align buffer after preamble
#             self.buffer = self.buffer[idx + self.preamble_len:]

#             return True

#         # prevent unbounded growth
#         self.buffer = self.buffer[-self.preamble_len:]

#         return False


#     def process_bit(self, bit):

#         self.bit_buffer.append(bit)

#         if len(self.bit_buffer) == 8:

#             value = 0
#             for b in self.bit_buffer:
#                 value = (value << 1) | b

#             char = chr(value)

#             print("char detected:", char)

#             self.char_buffer += char

#             print("message so far:", self.char_buffer)

#             self.bit_buffer = []


#     def decode_symbol(self):

#         if len(self.buffer) < self.symbol_len:
#             return None

#         sym = self.buffer[:self.symbol_len]

#         val = np.vdot(self.pn_pulse, sym)

#         self.buffer = self.buffer[self.symbol_len:]

#         bit = 1 if np.real(val) > 0 else 0

#         return bit


#     def work(self, input_items, output_items):

#         in0 = input_items[0]

#         # append incoming samples
#         self.buffer = np.concatenate((self.buffer, in0))

#         while True:

#             if not self.detected:

#                 if not self.detect_preamble():
#                     break

#                 self.detected = True

#             bit = self.decode_symbol()

#             if bit is None:
#                 break

#             print("bit is:", bit)

#             self.process_bit(bit)

#         return len(in0)