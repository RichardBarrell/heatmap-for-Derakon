/* This file is (c) 2013 Richard Barrell <rchrd@brrll.co.uk>, see LICENSE.txt */
/* (it's the ISC license, which is 2-clause BSD with simplified wording) */
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>

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
	size_t tail;
} queue;

static int queue_init(queue *q)
{
	q->pairs = malloc(sizeof(pair));
	if (q->pairs == NULL) {
		return -1;
	}
	q->size = 1;
	q->head = 0;
	q->tail = 0;
	return 0;
}

static void queue_free(queue *q) {
	free(q->pairs);
}

static size_t queue_used(queue *q) {
	size_t gap = q->tail - q->head;
	if (q->head > q->tail) { gap += q->size; }
	return gap;
}

static int queue_append(queue *q, pair p) {
	if ((queue_used(q)+1) == q->size) {
		size_t old_size = q->size;
		q->size = q->size * 2;
		q->pairs = realloc(q->pairs, q->size * sizeof(pair));
		if (q->pairs == NULL) {
			return -1;
		}
		if (q->tail < q->head) {
			memcpy(q->pairs + old_size, q->pairs, q->tail * sizeof(pair));
			q->tail = old_size + q->tail;
		}
	}
	if (q->tail == q->size) {
		q->tail = 0;
	}
	q->pairs[q->tail] = p;
	q->tail++;
	return 0;
}

static pair queue_popleft(queue *q) {
	size_t old_head = q->head;
	q->head = q->head + 1;
	if (q->head == q->size) {
		q->head = 0;
	}
	return q->pairs[old_head];
}

static int getbit(u8 *u, ii x, ii y, ii xMax) {
	ii pos = y*xMax + x;
	ii pos_byte = pos >> 3;
	ii pos_bit  = pos & 0x7;
	int val = (u[pos_byte] >> pos_bit) & 0x1;
	return val;
}

static void setbit(u8 *u, ii x, ii y, ii xMax) {
	ii pos = y*xMax + x;
	ii pos_byte = pos >> 3;
	ii pos_bit  = pos & 0x7;
	u8 bit = 1 << pos_bit;
	u[pos_byte] = (u[pos_byte] & ~bit) | bit;
}

int burnHeatMap(ii xMax, ii yMax,
		ii *heatMap,
		size_t goals_length, ii *goals_xs, ii *goals_ys)
{

#define IX(x, y) heatMap[(y)*xMax + (x)]

	int failing = 0;

	queue cell_todo;
	if (queue_init(&cell_todo) != 0) {
		failing = __LINE__ || -1;
		goto cleanup_none;
	}

	size_t used_sz = (xMax * yMax + 7) / 8;
	u8 *used = calloc(used_sz, 1);

	if (used == NULL) {
		failing = __LINE__ || -1;
		goto cleanup_queue;
	}

#define GETUSED(x, y) getbit(used, (x), (y), xMax)
#define SETUSED(x, y) setbit(used, (x), (y), xMax)
#define MAX(a,b) ((a)>(b)?(a):(b))
#define MIN(a,b) ((a)<(b)?(a):(b))

	for (ii y = 0; y < yMax; y++) {
		for (ii x = 0; x < xMax; x++) {
			if (IX(x, y) != 0) {
				SETUSED(x, y);
			}
			IX(x, y) = -1;
		}
	}

	for (size_t i = 0; i < goals_length; i++) {
		ii x = goals_xs[i], y = goals_ys[i];
		IX(x, y) = 0;
		SETUSED(x, y);
		pair xy = {x, y};
		if (queue_append(&cell_todo, xy) != 0) {
			failing = __LINE__ || -1;
			goto cleanup_queue_used;
		}
	}

	while (queue_used(&cell_todo) > 0) {
		pair xy = queue_popleft(&cell_todo);
		ii x = xy.x, y = xy.y;
		int32_t cost = IX(x, y);
		for (ii yi = MAX(0, y-1); yi < MIN(yMax, y+2); yi++) {
			for (ii xi = MAX(0, x-1); xi < MIN(xMax, x+2); xi++) {
				if (GETUSED(xi, yi)) {
					continue;
				}
				SETUSED(xi, yi);
				IX(xi, yi) = cost + 1;
				pair xiyi = {xi, yi};
				if (queue_append(&cell_todo, xiyi) != 0) {
					failing = __LINE__ || -1;
					goto cleanup_queue_used;
				}
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

 cleanup_queue_used:
	free(used);
 cleanup_queue:
	queue_free(&cell_todo);
 cleanup_none:
	return failing;
}

#ifdef TESTY
int main(int argc, char **argv) {
#define HI 16
#define WI 24
	int32_t *ra = calloc(sizeof(ra[0]), HI*WI);
	ii goal_x = 4;
	ii goal_y = 8;
	burnHeatMap(WI, HI, ra, 1, &goal_x, &goal_y);
	free(ra);
	return 0;
}
#endif
