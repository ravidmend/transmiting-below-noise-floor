#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 shira.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy
from gnuradio import gr

class decoder(gr.sync_block):
    """
    docstring for block decoder
    """
    def __init__(self, p0,p1,p2,p3,p4):
        gr.sync_block.__init__(self,
            name="decoder",
            in_sig=[<+numpy.float32+>, ],
            out_sig=None)


    def work(self, input_items, output_items):
        in0 = input_items[0]
        # <+signal processing here+>
        return len(input_items[0])
