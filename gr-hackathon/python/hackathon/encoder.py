#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 shira.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy 
from gnuradio import gr
from queue import Queue

class encoder(gr.sync_block):
    """
    docstring for block encoder
    """
    def __init__(self, string_input, pn_length, sps, fs):
        gr.sync_block.__init__(self,
            name="encoder",
            in_sig=None,
            out_sig=[numpy.float32, ])
        
        self.__sps__ = sps
        self.__string_input__ = string_input
        # to change: generate pn sequence based on input length and sps
        # self.__pn__ = numpy.random.randint(0, 2, pn_length)
        self.__pn__ = numpy.array([1]*int(pn_length)) # example pn sequence
        self.__queue__ = Queue()
        self.__fs__ = fs
        
    def modulate_info(self,string, pn, n):
        # make string to bits
        # string = [int(x) for x in string]
        # string = ''.join(f'{x:08b}' for x in string)
        # string = numpy.array([int(x) for x in string])
        string_bytes = string.encode('ascii')
        string = numpy.unpackbits(numpy.frombuffer(string_bytes, dtype=numpy.uint8))

        # add preamble
        string = numpy.concatenate(([1, 1, 1, 1, 1], string))
        #xor info with pn sequence
        new_pn = numpy.tile(pn, len(string))
        new_string = numpy.repeat(string, len(pn))
        data_to_mod = new_string ^ new_pn
        
        # pulse shape
        data_to_mod = numpy.repeat(data_to_mod, self.__sps__)
        #print("len of info is {}".format(len(data_to_mod)))


        # bpsk modulation: 0 -> -1, 1 -> +1:
        data_to_mod[data_to_mod == 0] = -1

        #check if queue not empty, if not, send its data and add new info
        if not self.__queue__.empty():
            data_to_mod = numpy.concatenate((self.__queue__.get(), data_to_mod))


        # make sure we have exactly n samples to output
        if len(data_to_mod) < n:
            #data_to_mod = numpy.concatenate([data_to_mod, numpy.random.randint(0, 2, n - len(data_to_mod))])
            data_to_mod = numpy.concatenate([data_to_mod, -1 * numpy.ones(n - len(data_to_mod))]) # pad with -1 (no signal)
        if len(data_to_mod) > n:
            self.__queue__.put(data_to_mod[n:])
            data_to_mod = data_to_mod[0:n]
            # to change

        return data_to_mod.astype(numpy.float32)
        


    def work(self, input_items, output_items):
        #print("BW is {}".format(2/((1/self.__fs__)*self.__sps__)))
        out = output_items[0]

        # number of samples requested
        n = len(out)

        # generate random 0/1 array
        bits = self.modulate_info(self.__string_input__, self.__pn__, n)

        # copy to output buffer
        out[:] = bits

        return len(bits)