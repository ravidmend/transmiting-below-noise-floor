#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 shira.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy 
from gnuradio import gr

class encoder(gr.sync_block):
    """
    docstring for block encoder
    """
    def __init__(self):
        gr.sync_block.__init__(self,
            name="encoder",
            in_sig=None,
            out_sig=[numpy.float32, ])
        
        self.__sps__ = 2
        self.__string_input__ = numpy.random.randint(0, 2, 20)
        self.__pn__ = numpy.random.randint(0, 2, 100)
        
    def modulate_info(self,string, pn, n):
        
        # add preamble
        string = numpy.concatenate(([1, 1, 1, 1, 1], string))
        #xor info with pn sequence
        new_pn = numpy.tile(pn, len(string))
        new_string = numpy.repeat(string, len(pn))
        data_to_mod = new_string ^ new_pn
        
        # pulse shape
        data_to_mod = numpy.repeat(data_to_mod, self.__sps__)
        print("len of info is {}".format(len(data_to_mod)))

        # make sure we have exactly n samples to output
        if len(data_to_mod) < n:
            data_to_mod = numpy.concatenate([data_to_mod, numpy.random.randint(0, 2, n - len(data_to_mod))])
        if len(data_to_mod) > n:
            data_to_mod = data_to_mod[0:n]
            # to change

        # bpsk modulation: 0 -> -1, 1 -> +1:
        data_to_mod[data_to_mod == 0] = -1

        return data_to_mod.astype(numpy.float32)
        


    def work(self, input_items, output_items):
        out = output_items[0]

        # number of samples requested
        n = len(out)

        # generate random 0/1 array
        bits = self.modulate_info(self.__string_input__, self.__pn__, n)

        # copy to output buffer
        out[:] = bits

        return len(bits)