# gcc _cmap.c -o _cmap.so -fPIC -shared -O2 -std=c99 -Wall -Werror && python cmap.py

from ctypes import CDLL, c_uint32, c_int32, POINTER, ARRAY, c_int, c_size_t, pointer
import numpy


cmap = CDLL("./_cmap.so")
cmap.burnHeatMap.argtypes = (
    c_int32, c_int32, POINTER(c_int32),
    c_size_t, POINTER(c_int32), POINTER(c_int32))
cmap.burnHeatMap.restype = c_int


def getHeatMap(gridMap, goals):
    # Explicitly copy gridMap to a shape appropriate for C.
    heatMap = gridMap.reshape(gridMap.shape, order="C")[:,:]

    # Copy the goals list into a format that's convenient for ctypes passing.
    goals_type = c_int32 * len(goals)
    goals_xs = goals_type()
    goals_ys = goals_type()
    for i, (x, y) in enumerate(goals):
        goals_xs[i] = x
        goals_ys[i] = y

    xMax = heatMap.shape[0]
    yMax = heatMap.shape[1]
    # I'm almost not sure that this isn't illegal.
    ptr = heatMap.ctypes.data_as(POINTER(c_int32))

    fail = cmap.burnHeatMap(yMax, xMax, ptr, len(goals), goals_xs, goals_ys)
    if fail != 0:
        raise MemoryError("allocation error in _cmap on line %d." % fail)

    return heatMap


def test():
    from time import time
    empty_grid = numpy.ones((1024, 1024), dtype=numpy.int32) * 0
    t0 = time()
    hm = getHeatMap(empty_grid, [(0,0)])
    t1 = time()
    print hm
    print t1 - t0

if __name__ == "__main__":
    test()
