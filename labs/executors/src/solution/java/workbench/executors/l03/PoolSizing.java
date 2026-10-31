package workbench.executors.l03;

import java.time.Duration;

public final class PoolSizing {
    private PoolSizing() {}

    private static double seconds(Duration d) {
        return d.toNanos() / 1e9;
    }

    // round up, but forgive floating-point noise: 64.00000000000001 must stay 64
    private static int ceil(double x) {
        return (int) Math.ceil(x - 1e-9);
    }

    public static int ioBound(int cores, double targetUtilization, Duration wait, Duration compute) {
        double ratio = seconds(wait) / seconds(compute);             // W / C
        return Math.max(1, ceil(cores * targetUtilization * (1 + ratio)));
    }

    public static double inFlight(double arrivalsPerSecond, Duration latency) {
        return arrivalsPerSecond * seconds(latency);                 // L = lambda * W
    }

    public static double maxThroughput(int threads, Duration latency) {
        return threads / seconds(latency);                           // lambda = L / W
    }

    public static int threadsFor(double arrivalsPerSecond, Duration latency, int downstreamLimit) {
        int needed = Math.max(1, ceil(inFlight(arrivalsPerSecond, latency)));
        return Math.min(needed, downstreamLimit);                    // more threads would only wait for the resource
    }
}
