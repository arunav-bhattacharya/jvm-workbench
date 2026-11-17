package workbench.performance.l04;

/**
 * Metrics for the report service. Every request thread calls {@link #record} once per report,
 * with the report's word count, so up to 200 threads write here at the same time. The numbers
 * come out too low under load.
 *
 * <p>Your job: make the counts exact when many threads record at once, and keep writes cheap.
 * {@link #count()} and {@link #totalWords()} are read by a monitoring program every few seconds.
 */
public final class RequestMetrics {
    private volatile long count;
    private volatile long totalWords;

    public void record(long words) {
        count++;
        totalWords += words;
    }

    public long count() { return count; }

    public long totalWords() { return totalWords; }
}
