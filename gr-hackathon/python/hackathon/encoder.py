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
    def __init__(self, p0,p1, p2,p3,p4):
        gr.sync_block.__init__(self,
            name="encoder",
            in_sig=None,
            out_sig=[numpy.float32, ])
        
        self.__string_input__ = p0
        self.__string_input__ = [1,0,1,1,0]
        self.__pn__ = p1
        self.__pn__ = [1,-1,1,1,-1,1]
        
    def mosulate_info(string, pn):
        bpsk_string = string.replace(0, -1)
        modulated = []
        for elemant in bpsk_string:
            modulated = modulated + [elemant * x for x in pn]
        
        return modulated
        

    def work(self, input_items, output_items):
        out = output_items[0]
        # <+signal processing here+>
        out[:] = mosulate_info(self.__string_input__, self.__pn__ )
        return len(output_items[0])
