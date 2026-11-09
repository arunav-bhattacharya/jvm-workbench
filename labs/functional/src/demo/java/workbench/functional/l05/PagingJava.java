package workbench.functional.l05;

import java.util.List;
import java.util.stream.IntStream;
import java.util.stream.Stream;

/** The same paging source and retry schedule with Java streams (JDK 9+ for the three-argument iterate). */
public class PagingJava {
    record Settlement(String ref, long amountCents) {}

    /** Stands for one HTTP call to the acquirer: three pages of settlement records. */
    static List<Settlement> fetchPage(int page) {
        System.out.println("  fetching page " + page);
        return IntStream.range(0, 3).mapToObj(i -> new Settlement("S" + page + "-" + i, (page * 3 + i) * 1_000L)).toList();
    }

    public static void main(String[] args) {
        // 1. a paging source: a stream of page numbers, flattened into records
        Stream<Settlement> settlements = Stream.iterate(1, page -> page <= 3, page -> page + 1)
                .flatMap(page -> fetchPage(page).stream());
        System.out.println("first settlement over 65.00:");
        System.out.println("  " + settlements.filter(s -> s.amountCents() > 6_500).findFirst().orElseThrow());

        // 2. a retry schedule: seed, condition to continue, next value
        List<Long> backoff = Stream.iterate(100L, delay -> delay <= 1_600, delay -> delay * 2).toList();
        System.out.println("backoff: " + backoff);
    }
}
