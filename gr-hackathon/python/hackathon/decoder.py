# #!/usr/bin/env python
# # -*- coding: utf-8 -*-
# #
# # Copyright 2026 fucking-me.
# #
# # SPDX-License-Identifier: GPL-3.0-or-later
# #


# from gnuradio import gr
# import numpy as np

# from gnuradio import gr
# import numpy as np

# class decoder(gr.sync_block):
#     def __init__(self, Ts, pn_len, fs):
#         gr.sync_block.__init__(self,
#             name="decoder",
#             in_sig=[np.complex64],
#             out_sig=None)

#         self.Ts = Ts
#         self.fs = fs

#         threshold = 20
#         sps = 4
#         self.sps = sps
#         self.threshold = threshold

#         pn_sequence = [1, -1, -1, -1, -1, -1, 1, 1]
#         self.pn = np.array(pn_sequence, dtype=np.float32)
#         self.pn_len = len(self.pn)

#         # rectangular pulse shaping
#         self.pn_pulse = np.repeat(self.pn, self.sps).astype(np.complex64)

#         # queue buffer
#         self.buffer = np.array([], dtype=np.complex64)

#         self.detected = False
#         self.symbol_len = len(self.pn_pulse)

#     def correlate(self, x):
#         # matched filter correlation
#         return np.correlate(x, np.conj(self.pn_pulse), mode='valid')

#     def detect_preamble(self):

#         if len(self.buffer) < self.symbol_len:
#             return False

#         corr = self.correlate(self.buffer)

#         max_val = np.max(np.abs(corr))

#         if max_val > self.threshold:

#             idx = np.argmax(np.abs(corr))

#             # align buffer to start of next symbol
#             self.buffer = self.buffer[idx + self.symbol_len:]

#             print("PREAMBLE DETECTED")

#             return True

#         # prevent buffer explosion
#         self.buffer = self.buffer[-self.symbol_len:]

#         return False


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

#         # append samples to queue
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

#         return len(in0)

from gnuradio import gr
import numpy as np

class decoder(gr.sync_block):
    def __init__(self, Ts, pn_len, fs):
        gr.sync_block.__init__(self,
            name="decoder",
            in_sig=[np.complex64],
            out_sig=None)

        self.Ts = Ts
        self.fs = fs

        threshold = 60
        sps = 2
        preamble_reps = 5

        self.sps = sps
        self.threshold = threshold
        self.preamble_reps = preamble_reps

        pn_sequence = [1,-1,-1,-1,-1,-1,1,1] # after bpsk modulation, 0->1, 1->-1
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


    def correlate(self, x, ref):
        return np.correlate(x, np.conj(ref), mode='valid')


    def detect_preamble(self):

        if len(self.buffer) < self.preamble_len:
            return False

        corr = self.correlate(self.buffer, self.preamble_pulse)

        max_val = np.max(np.abs(corr))

        if max_val > self.threshold:

            idx = np.argmax(np.abs(corr))

            print("PREAMBLE DETECTED")

            # align buffer after preamble
            self.buffer = self.buffer[idx + self.preamble_len:]

            return True

        # prevent unbounded growth
        self.buffer = self.buffer[-self.preamble_len:]

        return False


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

        return len(in0)