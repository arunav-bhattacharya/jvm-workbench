package workbench.performance.l04;

/**
 * Two counters for the report service. One thread parses documents and only touches
 * {@code parsed}; another writes the reports and only touches {@code written}. Each counter
 * has one writer, so there is no race. But both fields sit on the same cache line, so the two
 * cores keep taking the line away from each other.
 *
 * <p>Your job: keep the fields named {@code parsed} and {@code written}, keep them {@code volatile long},
 * and lay the class out so they are at least 64 bytes apart. The test reads the real offsets with JOL.
 */
public final class StageCounters {
    private volatile long parsed;
    private volatile long written;

    /** Called only by the parsing thread. */
    public void addParsed() { parsed++; }

    /** Called only by the writing thread. */
    public void addWritten() { written++; }

    public long parsed() { return parsed; }

    public long written() { return written; }
}
