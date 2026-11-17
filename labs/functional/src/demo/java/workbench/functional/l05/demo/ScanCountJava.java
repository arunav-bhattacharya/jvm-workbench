package workbench.functional.l05.demo;

import java.util.Comparator;
import java.util.List;
import java.util.stream.IntStream;

/** The same search with Java collections and streams. The first good match is recipe number 518. */
public class ScanCountJava {
    record RecipeCard(long id, int minutes) {}
    record Scored(RecipeCard recipe, int score) {}

    static final List<RecipeCard> BOOK = IntStream.range(0, 1_000_000)
            .mapToObj(i -> new RecipeCard(i + 1L, i % 1_000 == 517 ? 7 : 20 + i % 100))
            .toList();

    static int scored = 0;
    static int pulled = 0;

    /** Stands for a call to the matching service. Counts every call. */
    static int match(RecipeCard r) { scored++; return r.minutes() < 10 ? 95 : 10; }

    static void report(String label, RecipeCard found) {
        System.out.printf("%-22s scored %,9d  pulled %,9d  found id %s%n", label, scored, pulled, found == null ? null : found.id());
        scored = 0; pulled = 0;
    }

    public static void main(String[] args) {
        List<Scored> all = BOOK.stream().map(r -> new Scored(r, match(r))).toList();   // collect first, like a List chain
        report("Collect, then search", all.stream().filter(s -> s.score() >= 90).map(Scored::recipe).findFirst().orElse(null));
        report("One Stream", BOOK.stream().map(r -> new Scored(r, match(r))).filter(s -> s.score() >= 90)
                .map(Scored::recipe).findFirst().orElse(null));
        report("Stream + sorted", BOOK.stream().peek(r -> pulled++).sorted(Comparator.comparingLong(RecipeCard::id))
                .filter(r -> match(r) >= 90).findFirst().orElse(null));
    }
}
