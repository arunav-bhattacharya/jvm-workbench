package workbench.functional.l05;

import java.util.Comparator;
import java.util.List;
import java.util.stream.IntStream;

/** The same scan with Java collections and streams. The first suspicious authorization is number 518. */
public class ScanCountJava {
    record Auth(long id, long amountCents) {}
    record Scored(Auth auth, int score) {}

    static final List<Auth> FEED = IntStream.range(0, 1_000_000)
            .mapToObj(i -> new Auth(i + 1L, i % 1_000 == 517 ? 2_500_000 : 1_000L + i % 90_000))
            .toList();

    static int scored = 0;
    static int pulled = 0;

    /** Stands for a call to the fraud model. Counts every call. */
    static int risk(Auth a) { scored++; return a.amountCents() > 2_000_000 ? 95 : 10; }

    static void report(String label, Auth found) {
        System.out.printf("%-22s scored %,9d  pulled %,9d  found id %s%n", label, scored, pulled, found == null ? null : found.id());
        scored = 0; pulled = 0;
    }

    public static void main(String[] args) {
        List<Scored> all = FEED.stream().map(a -> new Scored(a, risk(a))).toList();   // collect first, like a List chain
        report("Collect, then search", all.stream().filter(s -> s.score() >= 90).map(Scored::auth).findFirst().orElse(null));
        report("One Stream", FEED.stream().map(a -> new Scored(a, risk(a))).filter(s -> s.score() >= 90)
                .map(Scored::auth).findFirst().orElse(null));
        report("Stream + sorted", FEED.stream().peek(a -> pulled++).sorted(Comparator.comparingLong(Auth::id))
                .filter(a -> risk(a) >= 90).findFirst().orElse(null));
    }
}
