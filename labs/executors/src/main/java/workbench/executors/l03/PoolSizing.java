package workbench.executors.l03;

import java.time.Duration;

/**
 * The arithmetic behind pool sizes. Each method is one or two lines; the point is to know which
 * formula answers which question.
 */
public final class PoolSizing {
    private PoolSizing() {}

    /**
     * Goetz's formula for a pool whose tasks compute for {@code compute} and then wait for {@code wait}:
     * {@code cores * targetUtilization * (1 + wait / compute)}, rounded up, and never less than 1.
     * Example: 8 cores, 0.8 utilization, 180 ms waiting, 20 ms computing gives 64.
     */
    public static int ioBound(int cores, double targetUtilization, Duration wait, Duration compute) {
        throw new UnsupportedOperationException("TODO: N * U * (1 + W/C), rounded up, at least 1");
    }

    /**
     * Little's law: the average number of requests in the system, {@code L = arrival rate * latency}.
     * Example: 400 requests per second that each take 250 ms means 100 in flight.
     */
    public static double inFlight(double arrivalsPerSecond, Duration latency) {
        throw new UnsupportedOperationException("TODO: L = lambda * W");
    }

    /**
     * The most requests per second {@code threads} threads can finish when each request holds a
     * thread for {@code latency}. Example: 50 threads at 250 ms each top out at 200 per second.
     */
    public static double maxThroughput(int threads, Duration latency) {
        throw new UnsupportedOperationException("TODO: Little's law solved for lambda");
    }

    /**
     * Threads needed to carry this load, rounded up, but never more than {@code downstreamLimit}
     * (for example the size of the connection pool every request needs). At least 1.
     */
    public static int threadsFor(double arrivalsPerSecond, Duration latency, int downstreamLimit) {
        throw new UnsupportedOperationException("TODO: ceil(L), capped by the downstream limit");
    }
}
