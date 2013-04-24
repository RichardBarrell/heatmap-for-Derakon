# This file is (c) 2013 Richard Barrell <rchrd@brrll.co.uk>, see LICENSE.txt
# (it's the ISC license, which is 2-clause BSD with simplified wording)

# gcc _cmap.c -o _cmap.so -fPIC -shared -O2 -std=c99 -Wall -Werror && python cmap.py

from ctypes import CDLL, c_uint32, c_int32, POINTER, ARRAY, c_int, c_size_t, pointer
import numpy
import numpy.ctypeslib


heatmap_ptr = numpy.ctypeslib.ndpointer(
    dtype=numpy.int32,
    ndim=2,
    flags=('C_CONTIGUOUS', 'ALIGNED', 'WRITEABLE'),
)

cmap = CDLL("./_cmap.so")
cmap.burnHeatMap.argtypes = (
    c_int32, c_int32, heatmap_ptr,
    c_size_t, POINTER(c_int32), POINTER(c_int32))
cmap.burnHeatMap.restype = c_int


def getHeatMap(gridMap, goals):

    # Explicitly copy gridMap into heatMap.
    heatMap = numpy.ndarray(
        gridMap.shape,
        dtype=numpy.int32,
        order='C')
    heatMap[:,:] = gridMap[:,:]

    # Copy the goals list into a format that's convenient for ctypes passing.
    goals_type = c_int32 * len(goals)
    goals_xs = goals_type()
    goals_ys = goals_type()
    for i, (x, y) in enumerate(goals):
        goals_xs[i] = x
        goals_ys[i] = y

    # Why does numpy put these in backwards?
    xMax = heatMap.shape[1]
    yMax = heatMap.shape[0]

    # I'm almost not sure that this isn't illegal.
    fail = cmap.burnHeatMap(xMax, yMax, heatMap, len(goals), goals_xs, goals_ys)
    if fail != 0:
        raise MemoryError("allocation error in _cmap on line %d." % fail)

    return heatMap


def timed_test(grid, goals):
    from time import time
    t0 = time()
    hm = getHeatMap(grid, goals)
    t1 = time()
    print "test took: %fs" % (t1 - t0)
    print "-" * 32
    print "input grid:"
    print "-" * 32
    print grid
    print "output heatmap:"
    print "-" * 32
    print hm
    print

def test_wide_open():
    grid = numpy.zeros((1024, 1024), dtype=numpy.int32)
    timed_test(grid, [(0, 0)])

def test_with_walls():
    grid = numpy.zeros((1024, 1024), dtype=numpy.int32)
    grid[:, 1] = -1
    grid[1023, 1] = 0
    grid[:, 1022] = -1
    grid[0, 1022] = 0
    timed_test(grid, [(0, 0)])

def test_with_maze():
    maze = [
        "+++++ + ",
        "+  +   +",
        "++ + ++ ",
        "+  + +  ",
        "  ++    ",
        " ++  +  ",
        "     ++ ",
        "+ ++++  ",
        " + ++++ ",
    ]
    grid = numpy.ndarray((len(maze[0]), len(maze)), dtype=numpy.int32)
    for y, line in enumerate(maze):
        for x, char in enumerate(line):
            grid[x, y] = -1 * int(char == "+")
    timed_test(grid, [(0, 0), (4, 1), (4, 1)])

if __name__ == "__main__":
    print "wide open field:"
    test_wide_open()
    print "put some walls in:"
    test_with_walls()
    print "how about a maze?:"
    test_with_maze()
