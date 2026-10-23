// SPDX-License-Identifier: BSD-3-Clause
// Measure Linux-to-remote-core RPMsg echo round trips with ti-rpmsg-char.
// Build on the board (one line):
//   gcc -O2 -Iinclude rpmsg_echo_latency.c -o rpmsg_echo_latency
//       -L/opt/ti/edgeai/lib -lti_rpmsg_char -Wl,-rpath,/opt/ti/edgeai/lib
#include <errno.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include <ti_rpmsg_char.h>

#define MAX_MSG 496
#define TIMEOUT_MS 1000

static long long ns_between(const struct timespec *a, const struct timespec *b)
{
	return (b->tv_sec - a->tv_sec) * 1000000000LL + (b->tv_nsec - a->tv_nsec);
}

static int cmp_ll(const void *a, const void *b)
{
	long long x = *(const long long *)a, y = *(const long long *)b;
	return (x > y) - (x < y);
}

int main(int argc, char **argv)
{
	int rproc = argc > 1 ? atoi(argv[1]) : R5F_MCU0_0;
	int count = argc > 2 ? atoi(argv[2]) : 1000;
	int port = argc > 3 ? atoi(argv[3]) : 14;
	char name[32], tx[MAX_MSG], rx[MAX_MSG];
	long long *rtt;
	int i, ret = 1;

	if (count <= 0 || !(rtt = calloc(count, sizeof(*rtt))))
		return 2;
	if (rpmsg_char_init(NULL)) {
		fprintf(stderr, "rpmsg_char_init failed\n");
		return 2;
	}
	snprintf(name, sizeof(name), "rt-latency-%d", getpid());
	rpmsg_char_dev_t *dev = rpmsg_char_open(rproc, NULL, RPMSG_ADDR_ANY, port, name, 0);
	if (!dev) {
		fprintf(stderr, "cannot open rproc %d port %d\n", rproc, port);
		goto out;
	}
	printf("rproc %d, remote port %d, local port %d, %d messages\n",
	       rproc, port, dev->endpt, count);

	for (i = 0; i < count; i++) {
		struct timespec t0, t1;
		struct pollfd pfd = { .fd = dev->fd, .events = POLLIN };
		int len = snprintf(tx, sizeof(tx), "mo62a-rt %d", i);
		ssize_t n;

		clock_gettime(CLOCK_MONOTONIC, &t0);
		if (write(dev->fd, tx, len) != len) {
			fprintf(stderr, "write %d failed: %s\n", i, strerror(errno));
			goto close;
		}
		if (poll(&pfd, 1, TIMEOUT_MS) != 1) {
			fprintf(stderr, "no reply to message %d within %d ms\n", i, TIMEOUT_MS);
			goto close;
		}
		n = read(dev->fd, rx, sizeof(rx));
		clock_gettime(CLOCK_MONOTONIC, &t1);
		if (n != len || memcmp(tx, rx, len)) {
			fprintf(stderr, "reply %d does not match the request\n", i);
			goto close;
		}
		rtt[i] = ns_between(&t0, &t1);
	}

	qsort(rtt, count, sizeof(*rtt), cmp_ll);
	long long sum = 0;
	for (i = 0; i < count; i++)
		sum += rtt[i];
	printf("round trip us: min %.1f median %.1f avg %.1f p99 %.1f max %.1f\n",
	       rtt[0] / 1e3, rtt[count / 2] / 1e3, sum / 1e3 / count,
	       rtt[(count * 99) / 100 - (count >= 100 ? 1 : 0)] / 1e3, rtt[count - 1] / 1e3);
	printf("RESULT: PASS %d/%d replies matched\n", count, count);
	ret = 0;
close:
	if (ret)
		printf("RESULT: FAIL\n");
	rpmsg_char_close(dev);
out:
	rpmsg_char_exit();
	free(rtt);
	return ret;
}
