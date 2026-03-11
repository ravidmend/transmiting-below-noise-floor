#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
from gnuradio import gr


class decoder(gr.sync_block):

    def __init__(self, pn_len, sps,recived_amp):

        gr.sync_block.__init__(
            self,
            name="decoder",
            in_sig=[np.complex64],
            out_sig=None,
        )
        self.sps = sps
        self.pn_len = pn_len
        preamble = [1,0,1,0]
        self.buffer = np.array([], dtype=np.complex64)
        self.detection_mode = True
        self.recived_amp = recived_amp

        np.random.seed(0)
        pn = np.random.randint(0, 2, pn_len).astype(np.float32)
        
        modulated_bits = self.bpsk_mod(pn)
        pulse_shaped = np.repeat(modulated_bits, sps) 
        self.pn = pulse_shaped


        spreaded_bits = self.spread_bits(preamble, pn, pn_len)
        modulated_bits = self.bpsk_mod(spreaded_bits)
        pulse_shaped = np.repeat(modulated_bits, sps) 
        self.preamble = pulse_shaped

        self.preamble_len = len(self.preamble)

        # self.pn_pulse = np.repeat(self.pn, self.sps)

        # self.preamble = np.tile(self.pn_pulse, self.preamble_reps)

        self.symbol_len = pn_len * sps
        # self.preamble_len = len(self.preamble)



        self.bit_buffer = []
        self.message = ""


    def correlate(self, x, ref):

        return np.correlate(x, np.conj(ref), mode="full")


    def detect_preamble(self):

        if len(self.buffer) < self.preamble_len:
            return False

        corr = self.correlate(self.buffer, self.preamble)

        abs_corr = np.abs(corr)

        peak = np.max(abs_corr)
        # noise = np.mean(abs_corr)

        # print("peak:", peak, "noise:", noise,"index:", np.argmax(abs_corr))

        threshold = 0.8 * self.recived_amp * self.preamble_len
        # if peak > 5 * noise:
        if peak > threshold:

            idx = np.argmax(abs_corr)

            print("PREAMBLE DETECTED")

            self.buffer = self.buffer[idx+1:]

            return True

        self.buffer = self.buffer[-(self.preamble_len-1) :]

        return False


    def decode_symbol(self):

        if len(self.buffer) < self.symbol_len:
            return None

        sym = self.buffer[: self.symbol_len]

        self.buffer = self.buffer[self.symbol_len :]

        val = np.vdot(self.pn, sym)

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
    

    def bpsk_mod(self, bits: np.ndarray) -> np.ndarray:
        bits = np.asarray(bits)
        return 2 * bits - 1


    def checktimeout(self): 
        if len(self.buffer) < self.symbol_len:
            return None

        sym = self.buffer[: self.symbol_len]

        val = np.vdot(self.pn, sym)

        if np.abs(val) > 0.5 * self.recived_amp * self.symbol_len:
            return False
    
        print("TIMEOUT")
        self.detection_mode = True
        self.bit_buffer = []
        self.message = ""
        return True


    def work(self, input_items, output_items):

        in0 = input_items[0]

        self.buffer = np.concatenate((self.buffer, in0))

        while True:

            if self.detection_mode:

                if not self.detect_preamble():
                    break

                self.detected = True

            if self.checktimeout():
                break

            bit = self.decode_symbol()

            if bit is None:
                break

            self.process_bit(bit)

        return len(in0)