"""
Main script of the whole project
"""
import time
import os
import hashlib
import random
import string
import numpy as np
import pyopencl as cl

"""
Initializing
"""

random.seed(time.time())

# Machine specific options. If you don't know what they do, run without these first.
os.environ['PYOPENCL_COMPILER_OUTPUT'] = '1'
os.environ['PYOPENCL_CTX'] = '0'

# How many batches are we sending per cycle [these numbers worked best on my Vega 56, they vary by machine]
BATCH_SIZE = 65536

# This is a hardcoded number in md5.cl! We only need it here for statistics. Change BOTH if necessary.
GPU_TRIES = 8192

countDoneHashes_all = 0
timeSinceStart = 0

# Choose a sufficiently small and big number to start off as a record, inverse of the ones we are trying to find
currentRecord_b = "0" * 32
currentRecord_s = "f" * 32

print("Running with", BATCH_SIZE, "batches and", GPU_TRIES, "GPU tries per cycle")

"""
Initializing OpenCL and creating buffers
"""

ctx = cl.create_some_context()
queue = cl.CommandQueue(ctx)
with open("md5.cl", "r") as f:
    data = f.read()
prg = cl.Program(ctx, data).build()

baseHashArray_s = [[0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF]] * BATCH_SIZE
baseHashArray_b = [[0x00000000, 0x00000000, 0x00000000, 0x00000000]] * BATCH_SIZE

# In this project converting to big-endian is preferable on the GPU for more understandable calculations
# Since we are handling the endianness on the other side, we can freely use uint32 instead of >u4 here
hashArray_s = np.array(baseHashArray_s, dtype='uint32')
hashArray_b = np.array(baseHashArray_b, dtype='uint32')
hashArray_s_default = np.array(baseHashArray_s, dtype='uint32')
hashArray_b_default = np.array(baseHashArray_b, dtype='uint32')
bufferHash_s = cl.Buffer(ctx, cl.mem_flags.WRITE_ONLY, hashArray_s.nbytes)
bufferHash_b = cl.Buffer(ctx, cl.mem_flags.WRITE_ONLY, hashArray_b.nbytes)

baseArray_s = [[0] * 55] * BATCH_SIZE
baseArray_b = [[0] * 55] * BATCH_SIZE
baseText_s = np.empty_like(baseArray_s, dtype="string_")
baseText_b = np.empty_like(baseArray_b, dtype="string_")
bufferText_s = cl.Buffer(ctx, cl.mem_flags.WRITE_ONLY, baseText_s.nbytes)
bufferText_b = cl.Buffer(ctx, cl.mem_flags.WRITE_ONLY, baseText_b.nbytes)

preid = np.array([random.choice(string.ascii_lowercase + string.digits), random.choice(string.ascii_lowercase + string.digits), random.choice(string.ascii_lowercase + string.digits), random.choice(string.ascii_lowercase + string.digits), random.choice(string.ascii_lowercase + string.digits),random.choice(string.ascii_lowercase + string.digits), random.choice(string.ascii_lowercase + string.digits),random.choice(string.ascii_lowercase + string.digits), random.choice(string.ascii_lowercase + string.digits), random.choice(string.ascii_lowercase + string.digits), random.choice(string.ascii_lowercase + string.digits),random.choice(string.ascii_lowercase + string.digits)], dtype="string_")
preid_buff = cl.Buffer(ctx, cl.mem_flags.READ_ONLY, preid.nbytes)

for iteration in range(20160304):
    preid = np.array([random.choice(string.ascii_lowercase + string.digits), random.choice(string.ascii_lowercase + string.digits), random.choice(string.ascii_lowercase + string.digits), random.choice(string.ascii_lowercase + string.digits), random.choice(string.ascii_lowercase + string.digits),random.choice(string.ascii_lowercase + string.digits), random.choice(string.ascii_lowercase + string.digits),random.choice(string.ascii_lowercase + string.digits), random.choice(string.ascii_lowercase + string.digits), random.choice(string.ascii_lowercase + string.digits), random.choice(string.ascii_lowercase + string.digits),random.choice(string.ascii_lowercase + string.digits)], dtype="string_")
    startTime = time.time()

    baseText_s = np.empty_like(baseArray_s, dtype="string_")
    baseText_b = np.empty_like(baseArray_b, dtype="string_")

    # Initialize data (e.g. send the random pre-id string, null the buffers)
    cl.enqueue_copy(queue, preid_buff, preid)
    cl.enqueue_copy(queue, bufferHash_s, hashArray_s_default)
    cl.enqueue_copy(queue, bufferHash_b, hashArray_b_default)
    cl.enqueue_copy(queue, bufferText_s, baseText_s)
    cl.enqueue_copy(queue, bufferText_b, baseText_b)

    # Passing the data to the kernel, then running the program
    prg.calc(queue, (BATCH_SIZE,), None, preid_buff, bufferHash_s, bufferHash_b, bufferText_s, bufferText_b)

    # Get the necessary output from the GPU
    cl.enqueue_copy(queue, hashArray_s, bufferHash_s)
    cl.enqueue_copy(queue, baseText_s, bufferText_s)
    cl.enqueue_copy(queue, hashArray_b, bufferHash_b)
    cl.enqueue_copy(queue, baseText_b, bufferText_b)

    # Sort the smallest outputs from the GPU threads here, from the LSBs to MSBs in an ascending order, then choose the first element.
    baseText_s = baseText_s[np.lexsort((hashArray_s[:,3], hashArray_s[:,2], hashArray_s[:,1], hashArray_s[:,0]))]
    hashArray_s = hashArray_s[np.lexsort((hashArray_s[:,3], hashArray_s[:,2], hashArray_s[:,1], hashArray_s[:,0]))]
    returnHash_s = (''.join((hex(block)[2:]).zfill(8) for block in hashArray_s[0]))

    # Same, just in descending order with the biggest outputs.
    baseText_b = baseText_b[np.lexsort((-hashArray_b[:,3], -hashArray_b[:,2], -hashArray_b[:,1], -hashArray_b[:,0]))]
    hashArray_b = hashArray_b[np.lexsort((-hashArray_b[:,3], -hashArray_b[:,2], -hashArray_b[:,1], -hashArray_b[:,0]))]
    returnHash_b = (''.join((hex(block)[2:]).zfill(8) for block in hashArray_b[0]))

    # Count lengths of the repeating characters at the start. Just for statistics.
    length_s = 1
    while returnHash_s[length_s-1] == returnHash_s[length_s]:
        length_s += 1

    length_b = 1
    while returnHash_b[length_b-1] == returnHash_b[length_b]:
        length_b += 1

    # If the records are the default, read them from the file.
    try:
        if currentRecord_b == "0" * 32:
            with open("result_f.txt", "r") as f: currentRecord_b = f.readline()

        if currentRecord_s == "f" * 32:
            with open("result_0.txt", "r") as f: currentRecord_s = f.readline()
    except IOError:
        print("No past record found. Using default values. Lots of new records will pop up at the start.")

    # If we found a better candidate, cool, save it!
    if returnHash_b > currentRecord_b:
        print("Cycle ", iteration, ": New record found with ",str(length_b)," f-s.", sep="")
        currentRecord_b = returnHash_b
        messageToHash = b"".join(baseText_b[0]).decode("utf-8")
        with open("result_f.txt", "w") as f: f.writelines([returnHash_b, '\n', hashlib.md5(messageToHash.encode()).hexdigest(),'\n',str(length_b), '\n', messageToHash])
        with open("results.txt", "a") as f: f.writelines([returnHash_b, ' - ', messageToHash, '\n'])

    if returnHash_s < currentRecord_s:
        print("Cycle ", iteration, ": New record found with ",str(length_s)," zeros.", sep="")
        currentRecord_s = returnHash_s
        messageToHash = b"".join(baseText_s[0]).decode("utf-8")
        with open("result_0.txt", "w") as f: f.writelines([returnHash_s, '\n', hashlib.md5(messageToHash.encode()).hexdigest(),'\n', str(length_s), '\n', messageToHash])
        with open("results.txt", "a") as f: f.writelines([returnHash_s, ' - ', messageToHash, '\n'])
    
    doneTime = round(time.time() - startTime, 5)

    countDoneHashes_cycle = round((BATCH_SIZE * GPU_TRIES) / doneTime)
    countDoneHashes_all += countDoneHashes_cycle
    timeSinceStart += doneTime

    # Statistics every 5 iterations.
    if iteration % 5 == 0:
        print("Cycle ", str(iteration), ": [cycle time: ", doneTime , "s][speed: ", "{:,}".format(countDoneHashes_cycle).replace(",", " "), " hash/s][checked: ", "{:,}".format(countDoneHashes_all).replace(","," "), " hashes][runtime: ", round(timeSinceStart), "s]", sep="")
