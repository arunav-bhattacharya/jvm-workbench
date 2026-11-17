package workbench.performance.l04;

// HotSpot lays out superclass fields before subclass fields, so a chain of classes puts the
// padding exactly where we want it. Fields of one class may be reordered; the chain may not.
abstract class ParsedCounter {
    volatile long parsed;
}

abstract class PadAfterParsed extends ParsedCounter {
    long p1, p2, p3, p4, p5, p6, p7, p8;          // 64 bytes between parsed and written
}

abstract class WrittenCounter extends PadAfterParsed {
    volatile long written;
}

abstract class PadAfterWritten extends WrittenCounter {
    long q1, q2, q3, q4, q5, q6, q7, q8;          // and 64 bytes after written, away from the next object
}

public final class StageCounters extends PadAfterWritten {
    public void addParsed() { parsed++; }         // one writer per field: ++ on a volatile is safe here

    public void addWritten() { written++; }

    public long parsed() { return parsed; }

    public long written() { return written; }
}
