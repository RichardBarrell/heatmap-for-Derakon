/* This file is (c) 2013 Richard Barrell <rchrd@brrll.co.uk>, see LICENSE.txt */
/* (it's the ISC license, which is 2-clause BSD with simplified wording) */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <limits.h>

typedef int32_t ii;
typedef uint8_t u8;
typedef struct {
	ii x;
	ii y;
} pair;
typedef struct {
	pair *pairs;
	size_t size;
	size_t head;
	size_t used;
} queue;

static int queue_init(queue *q)
{
	q->pairs = malloc(sizeof(pair));
	if (q->pairs == NULL) {
		return -1;
	}
	q->size = 1;
	q->head = 0;
	q->used = 0;
	return 0;
}

static void queue_free(queue *q) {
	free(q->pairs);
}

static size_t queue_used(queue *q) {
	return q->used;
}

static int queue_append(queue *q, pair p) {
	/* Enforces (q->used < q->size). */
	if (q->used == q->size) {
		size_t old_size = q->size;
		q->size = q->size << 1;
		q->pairs = realloc(q->pairs, q->size * sizeof(pair));
		if (q->pairs == NULL) {
			return -1;
		}

		/* Copy elements that are at the tail of the queue
		   behind the head up so that they will be
		   contiguously following q->head. */

		/* Example, resizing from 4 elements to 8 elements.
		   In this diagram "?" represents an unused slot and
		   a number n represents the nth element in the queue.

		   Before realloc (full):
		   [ 2, 3, 0, 1, ]

		   After realloc (free slots, in wrong place):
		   [ 2, 3, 0, 1, ?, ?, ?, ? ]

		   After memcpy (everything now where it belongs):
		   [ ?, ?, 0, 1, 2, 3, ?, ? ]
		    (s)   (e)   (d)

		    We copy elements from (s) to (e) to the location (d).
		*/
		if (q->head > 0) {
			pair *dest = q->pairs + old_size;
			memcpy(dest, q->pairs, q->head * sizeof(pair));
		}
	}
	/* Wrap around at q->size. This works because q->size is always a
	 * power of two. This is ~8% quicker than (% q->size) on my CPU. */
	size_t new_pos = (q->head + q->used) & (q->size-1);
	q->pairs[new_pos] = p;
	q->used++;
	return 0;
}

static pair queue_popleft(queue *q) {
	size_t old_head = q->head;
	q->head++;
	q->used--;
	/* q->head needs to wrap around. */
	if (q->head == q->size) {
		q->head = 0;
	}
	return q->pairs[old_head];
}

int burnHeatMap(ii xMax, ii yMax,
		ii *heatMap,
		size_t goals_length, ii *goals_xs, ii *goals_ys)
{

/* FAIL_LINE is defined like this just in case something plays silly */
/* games with line pragmas and somehow causes __LINE__ to end up being 0. */
#define FAIL_LINE ((__LINE__ != 0) ? __LINE__ : -1)
#define IX(x, y) heatMap[(y)*xMax + (x)]

	int failing = 0;

	if ((xMax == 0) || (yMax == 0)) {
		/* Empty map, nothing to do. */
		failing = 0;
		goto cleanup_none;
	}

	if ((xMax < 0) || (yMax < 0)) {
		/* Invalid, negative size. */
		failing = FAIL_LINE;
		goto cleanup_none;
	}

	if (xMax > ((INT32_MAX - 1) / yMax)) {
		/* Can't index more than INT32_MAX pixels without overflow. */
		/* Won't bother to index with size_ts instead of int32_ts. */
		/* Also, use INT32_MAX as a sentinel for unvisited squares. */
		failing = FAIL_LINE;
		goto cleanup_none;
	}

	queue cell_todo;
	if (queue_init(&cell_todo) != 0) {
		failing = FAIL_LINE;
		goto cleanup_none;
	}

	/* set up the walls */
	for (ii y = 0; y < yMax; y++) {
		for (ii x = 0; x < xMax; x++) {
			IX(x, y) = (IX(x, y) == 0) ? INT32_MAX : -1;
		}
	}

	/* enqueue all the goals, blowing holes in any walls covering goals */
	for (size_t i = 0; i < goals_length; i++) {
		ii x = goals_xs[i], y = goals_ys[i];
		if (IX(x, y) == 0) {
			continue;
		}
		IX(x, y) = 0;
		pair xy = {x, y};
		if (queue_append(&cell_todo, xy) != 0) {
			failing = FAIL_LINE;
			goto cleanup_queue;
		}
	}

#define MAX(a,b) ((a)>(b)?(a):(b))
#define MIN(a,b) ((a)<(b)?(a):(b))

	while (queue_used(&cell_todo) > 0) {
		pair xy = queue_popleft(&cell_todo);
		ii x = xy.x, y = xy.y;
		ii cost = IX(x, y) + 1;
		for (ii yi = MAX(0, y-1); yi < MIN(yMax, y+2); yi++) {
			for (ii xi = MAX(0, x-1); xi < MIN(xMax, x+2); xi++) {
				if (IX(xi, yi) <= cost) {
					continue;
				}
				IX(xi, yi) = cost;
				pair xiyi = {xi, yi};
				if (queue_append(&cell_todo, xiyi) != 0) {
					failing = FAIL_LINE;
					goto cleanup_queue;
				}
			}
		}
	}

	/* set unreached squares to -1 */
	for (ii y = 0; y < yMax; y++) {
		for (ii x = 0; x < xMax; x++) {
			if (IX(x, y) == INT32_MAX) {
				IX(x, y) = -1;
			}
		}
	}

#ifdef TESTY
	for (ii yi = 0; yi<yMax; yi++) {
		putchar((yi>0) ? ' ' : '[');
		putchar('[');
		for (ii xi = 0; xi<xMax; xi++) {
			if (xi>0) {
				putchar(' ');
			}
			printf("%2d", IX(xi, yi));
		}
		putchar(']');
		if (yi==yMax-1) {
			putchar(']');
		}
		putchar('\n');
	}
#endif

 cleanup_queue:
	queue_free(&cell_todo);
 cleanup_none:
	return failing;
}

#ifdef TESTY
int main(int argc, char **argv) {
#define HI 16
#define WI 24
	ii *ra = calloc(sizeof(ra[0]), HI*WI);
	ii goal_x = 4;
	ii goal_y = 8;
	burnHeatMap(WI, HI, ra, 1, &goal_x, &goal_y);
	free(ra);
	return 0;
}
#endif
