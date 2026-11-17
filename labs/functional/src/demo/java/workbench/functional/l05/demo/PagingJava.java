package workbench.functional.l05.demo;

import java.util.List;
import java.util.stream.IntStream;
import java.util.stream.Stream;

/** The same paging source and serving buttons with Java streams (JDK 9+ for the three-argument iterate). */
public class PagingJava {
    record SearchResult(String title, int minutes) {}

    /** Stands for one web request to the recipe site: three results per page. */
    static List<SearchResult> fetchPage(int page) {
        System.out.println("  fetching page " + page);
        return IntStream.range(0, 3).mapToObj(i -> new SearchResult("R" + page + "-" + i, 60 - (page * 3 + i) * 5)).toList();
    }

    public static void main(String[] args) {
        // 1. a paging source: a stream of page numbers, flattened into results
        Stream<SearchResult> results = Stream.iterate(1, page -> page <= 3, page -> page + 1)
                .flatMap(page -> fetchPage(page).stream());
        System.out.println("first recipe under 30 minutes:");
        System.out.println("  " + results.filter(r -> r.minutes() < 30).findFirst().orElseThrow());

        // 2. the serving buttons: seed, condition to continue, next value
        List<Integer> servings = Stream.iterate(1, n -> n <= 16, n -> n * 2).toList();
        System.out.println("servings: " + servings);
    }
}
