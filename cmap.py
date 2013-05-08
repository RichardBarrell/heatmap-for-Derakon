# This file is (c) 2013 Richard Barrell <rchrd@brrll.co.uk>, see LICENSE.txt
# (it's the ISC license, which is 2-clause BSD with simplified wording)

# gcc _cmap.c -o _cmap.so -fPIC -shared -O2 -std=c99 -Wall -Werror && \
#   python cmap.py

from ctypes import CDLL, c_int32, POINTER, c_int, c_size_t
import numpy
import numpy.ctypeslib
import numpy.random


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


class HeatmapFailure(Exception):
    """ The C heatmap module threw a whoopsie.
        Probably because of a malloc() failure.
    """


def getHeatMap(gridMap, goals):

    # Explicitly copy gridMap into heatMap.
    heatMap = numpy.ndarray(
        gridMap.shape,
        dtype=numpy.int32,
        order='C')
    heatMap[:, :] = gridMap[:, :]

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

    # Python will spill this into an arbitrary-precision integer,
    # where C would just overflow the int32_t. The same check is
    # replicated in the C code too, but this exception is friendlier!
    # The limit of INT32_MAX squares comes from two places:
    #   1. the C code indexes squares using int32_ts. In theory that could
    #      use uint32_ts or size_ts instead, but there's little point because:
    #   2. the maximum cost that you can get on a grid is bounded by the
    #      number of squares on it; the restriction to at-most-INT32_MAX
    #      squares means that the costs will definitely fit into the int32_ts
    #      used in the ndarray.
    # Oh and we don't use unsigned numbers in the costs array because we want
    # to have negative numbers to signal impassable & unreachable squares.
    if (xMax * yMax) > 0x7fffffff:
        raise ValueError("grid has more than INT32_MAX squares. :(")

    # I'm almost not sure that this isn't illegal.
    err = cmap.burnHeatMap(xMax, yMax, heatMap, len(goals), goals_xs, goals_ys)
    if err != 0:
        # This will have come about as a result of a malloc NULL or
        # (input validation failurewhich this Python code should have
        # caught or avoided causing in the first place.)  burnHeatMap
        # promises to free everything it's allocated before giving up
        # and returning a nonzero value.
        raise HeatmapFailure("error in _cmap on line %d." % err)

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
    return hm


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
    timed_test(grid, [(1, 1), (4, 1), (4, 1)])


def test_huge_maze():
    wide = 1 << 12
    numpy.random.seed(2718283)
    rnds = numpy.random.random_integers(-1, 0, size=(wide, wide))
    grid = numpy.array(rnds, dtype=numpy.int32, order='C')
    out = timed_test(grid, [(1, 1), (wide - 40, 56)])
    print numpy.amax(out)
    # from matplotlib import pyplot
    # pyplot.imshow(out, interpolation="nearest")
    # pyplot.show()

if __name__ == "__main__":
    print "wide open field:"
    test_wide_open()
    print "put some walls in:"
    test_with_walls()
    print "how about a maze?:"
    test_with_maze()
    print "how about a huge field with pot-holes?:"
    test_huge_maze()
