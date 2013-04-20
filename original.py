# import statprof
import numpy
from time import time


## Generate a "heat map" that represents how far away each cell in the provided
# map is from any of the goal cells. The heat map can be used to allow entities
# to move towards those goal cells by simply examining their neighbors and 
# moving to the one with the shortest remaining distance.
# \param gridMap A Numpy array where 0 represents "open" and any 
#         other value represents "closed"
# \param goals A list (set, etc.) of (x, y) tuples representing the goal
#        tiles. 
def getHeatMap(gridMap, goals):
    # A Numpy array of integers where each value is 
    # the distance the corresponding cell in gridMap is from any goal tile.
    # Start with all non-goal tiles at -1 and all goal tiles at 0.
    heatMap = numpy.ones(gridMap.shape, dtype = numpy.int32) * -1
    for x, y in goals:
        heatMap[(x, y)] = 0

    xVals, yVals = numpy.where(gridMap != 0)
    # Maps cells we've seen to their costs. Add unreachable cells here so we
    # never try to reach them.
    cellToCost = dict([((xVals[i], yVals[i]), -1) for i in xrange(len(xVals))])
    # Queue of cells waiting to be scanned.
    cellQueue = []
    # Max values to feed into xrange when getting neighbors.
    maxX = gridMap.shape[0]
    maxY = gridMap.shape[1]
    for x, y in goals:
        cellToCost[(x, y)] = 0
        for xi in xrange(max(0, x - 1), min(maxX, x + 2)):
            for yi in xrange(max(0, y - 1), min(maxY, y + 2)):
                if (xi, yi) not in cellToCost and gridMap[xi, yi] == 0: 
                    cellToCost[(xi, yi)] = 1
                    heatMap[(xi, yi)] = 1
                    cellQueue.append((xi, yi))

    # Pop a cell, examine its neighbors, and add any not-yet-processed
    # neighbors to the queue. This is a simple breadth-first search.
    while cellQueue:
        pos = cellQueue.pop(0)
        cost = cellToCost[pos]
        # Find all neighbors for whom we have a new route.
        for xi in xrange(max(0, pos[0] - 1), min(maxX, pos[0] + 2)):
            for yi in xrange(max(0, pos[1] - 1), min(maxY, pos[1] + 2)):
                if (xi, yi) not in cellToCost:
                    cellToCost[(xi, yi)] = cost + 1
                    heatMap[(xi, yi)] = cost + 1
                    cellQueue.append((xi, yi))
    return heatMap

def test():
    # statprof.start()
    from time import time
    empty_grid = numpy.ones((1024, 1024), dtype=numpy.int32) * 0
    t0 = time()
    hm = getHeatMap(empty_grid, [(0,0)])
    t1 = time()
    print hm
    print t1 - t0
    # statprof.stop()
    # statprof.display()

stuff = "HI"

if __name__ == "__main__":
    test()
