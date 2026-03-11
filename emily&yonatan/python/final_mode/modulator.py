#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2026 Emily_Yonatan.
#
# SPDX-License-Identifier: GPL-3.0-or-later
#


import numpy
from gnuradio import gr

class modulator(gr.sync_block):
    """
    docstring for block modulator
    """
    def __init__(self, t, fs=32000, message=""):
        gr.sync_block.__init__(self,
            name="modulator",
            in_sig=[],
            out_sig=[numpy.float32, ])
        self.message= message
        self.t= t
        self.fs= fs

        self.n= int(self.t * self.fs)
        self.samples= self.gen_samples()
        self.index = 0

    def enqueue_from_string(self):
        bytes_data= self.message.encode('utf-8')
        binary_string=  ''.join(f'{byte:08b}' for byte in bytes_data)
        return binary_string
    
    def gen_samples(self):
        binary_string= self.enqueue_from_string()
        samples= [-1.0]*self.n
        #print(samples)
        for bit in binary_string:
            if bit == '0':
                samples.extend([1.0]*self.n)
                samples.extend([-1.0]*2*self.n)
            elif bit== '1':
                samples.extend([1.0]*2*self.n)
                samples.extend([-1.0]*self.n)
        return samples
    
    def work(self, input_items, output_items):
        out = output_items[0] #first output
        length= len(out) #buffersize
        left= len(self.samples)- self.index
        count= min(length, left)
        out[:count]= self.samples[self.index :self.index+count]
        self.index= self.index+count
        if count<length:
            out[count:length]= [0.0]*(length-count)
            self.index= len(self.samples)
        return length