package workbench.vthreads.l01;

import java.time.Duration;

public final class LittlesLaw {
    private LittlesLaw() {}

    public static double inFlight(double perSecond, Duration latency) {
        // L = lambda x W, with W in seconds
        return perSecond * seconds(latency);
    }

    public static double maxThroughput(int threads, Duration latency) {
        // each thread finishes 1 / W requests per second, so the pool finishes threads / W
        return threads / seconds(latency);
    }

    private static double seconds(Duration d) {
        return d.toNanos() / 1_000_000_000.0;
    }
}
