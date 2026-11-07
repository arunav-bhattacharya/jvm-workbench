package workbench.performance.l04;

/**
 * Metrics for the authorization endpoint. Every request thread calls {@link #record} once per
 * request, so up to 200 threads write here at the same time. The numbers come out too low under load.
 *
 * <p>Your job: make the counts exact when many threads record at once, and keep writes cheap.
 * {@link #count()} and {@link #totalCents()} are read by a metrics scraper every few seconds.
 */
public final class RequestMetrics {
    private volatile long count;
    private volatile long totalCents;

    public void record(long amountCents) {
        count++;
        totalCents += amountCents;
    }

    public long count() { return count; }

    public long totalCents() { return totalCents; }
}
