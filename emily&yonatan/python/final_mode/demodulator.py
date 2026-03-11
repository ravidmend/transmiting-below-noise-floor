#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 Emily_Yonatan.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy
from gnuradio import gr


class demodulator(gr.sync_block):

    def __init__(self, t, fs, v_sensitivity=0.0, timeout=100000, window_len= 100):

        gr.sync_block.__init__(
            self,
            name="demodulator",
            in_sig=[numpy.float32],
            out_sig=None
        )

        self.t = t
        self.fs = fs
        self.v_sensitivity= v_sensitivity
        self.timeout= timeout
        self.n = int(self.t * self.fs)

        self.found_preamble = False

        self.neg_count = 0
        self.pos_count = 0
        self.counter=0
        self.bits = []
        self.window= []
        self.window_s= window_len

    def push_bit(self, bit):
        self.bits.append(str(bit))
        if len(self.bits) == 8:
            byte_c = int(''.join(self.bits), 2)
            print(chr(byte_c), end='')
            self.bits = []

    def work(self, input_items, output_items):
        samples = input_items[0]

        for sample in samples:
            self.window.append(sample)
            if len(self.window)>self.window_s:
                self.window.pop(0)
            sample= numpy.mean(self.window)
            self.counter+=1 #for each sample and we edit in the loop
            if self.counter >= self.timeout:
                self.found_preamble= False
                self.neg_count=0
                self.pos_count=0
                self.bits=[]
                self.counter=0
                continue

            #find preamble
            if not self.found_preamble:
                if sample < -self.v_sensitivity:
                    self.neg_count += 1
                elif sample> self.v_sensitivity:
                    if self.neg_count >= self.n:
                        self.found_preamble = True
                    self.pos_count=1
                    self.neg_count = 0
                    self.counter=1
                continue

            #find repeat of v
            if sample > self.v_sensitivity:
                self.pos_count += 1

            elif sample< -self.v_sensitivity:
                if self.pos_count > 0: #change from pos to neg
                    if self.pos_count > 1.5 * self.n: #out threshold
                        bit = 1
                    elif self.pos_count> self.n/2:
                        bit = 0
                    else:
                        continue

                    self.push_bit(bit)
                    self.pos_count = 0
                    self.counter=0
                    
        return len(samples)