# OpenCL based solution for an MD5 hash challenge
---
## Goals
The base goal was to supersede the python script I wrote earlier with a faster solution, which was simply iterating through md5 hashes with the use of hashlib. It was too luck based, and inefficient.

The point is to find the lowest and highest hashes for a valid e-mail address. Since I had to own the e-mail that had the hash, I decided to use the + notation, which is in a static prefix, just like the suffix at the end after @.

e.g:

randmail342pqwoei+a1027f46335t2303@gmail.com - ffffffff4158848c1e49c66996165255

randmail342pqwoei+a1027f48194t2536@gmail.com - 00000004edcf0d0923772e1b1e183997

## Idea
- Giving the GPU an amount of python arrays to fill
- Generating candidates with the GPU
- Calculate the MD5 hashes simultaneously of multiple candidates per thread
- Sort those candidates on the GPU
- Pass the best of each thread back to the CPU (most zeros and most f-s)
- Sort this much lower amount of hashes with the CPU, and get the best of each.
- If its better than an earlier result, store the GPU computed hash, the CPU computed hash (to double check it's good), the length of the starting f-s or 0-s (for easier human readability), and the e-mail in a file.

## Results
With the earlier script that ran only on the CPU, I could calculate a billion hashes in **1 hour and 15 minutes**.

With this, I could calculate, validate, and check 1 billion hashes every **~2.5 seconds**.

## Prerequisites
You need an OpenCL platform for your machine, and a capable device of your platform.
You need python with the pyopencl package installed.

## Installation and running
### Installation
You only have to install the above mentioned prerequisites.

Get the platform you need. (e.g for an AMD GPU get AMDs, at the time of writing I had OCL_SDK_Light_AMD)

`pip install pyopencl`

### Configuration
The values in the script were tested on a Ryzen 2600 CPU, and a Vega 56 graphics card, and seemed like the top limit.
Modify `BATCH_SIZE` and `GPU_TRIES` accordingly. However, it is important to note, that `GPU_TRIES` have to be modified in the *md5.cl* file too! `GPU_TRIES` are only for statistical purposes in the python script. Try lower values first.

### Running
`py md5script.py`

## Additional notes
This project is pretty unoptimized, since I stopped working on it after it produced the results I wanted, which it actually did after running for a few minutes. (Finding 10 F-s and 0-s at the start of a hash)