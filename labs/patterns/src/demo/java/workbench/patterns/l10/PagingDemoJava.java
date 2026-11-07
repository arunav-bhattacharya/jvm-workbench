package workbench.patterns.l10;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;
import java.util.function.Function;

/** Walk a cursor-paginated refunds API lazily. Java has no generators, so the iterator's state is written by hand. */
public class PagingDemoJava {
    record RefundPage(List<String> items, Integer next) {}

    static final Map<Integer, RefundPage> PAGES = Map.of(
            0, new RefundPage(List.of("rf_1", "rf_2"), 1),
            1, new RefundPage(List.of(), 2),                       // an empty page in the middle
            2, new RefundPage(List.of("rf_3"), null));

    static Iterator<String> refunds(Function<Integer, RefundPage> fetch) {
        return new Iterator<>() {
            private Iterator<String> current = Collections.emptyIterator();
            private Integer cursor = 0;                            // null = no more pages

            @Override public boolean hasNext() {
                while (!current.hasNext() && cursor != null) {     // while, not if: skip empty pages
                    RefundPage page = fetch.apply(cursor);
                    current = page.items().iterator();
                    cursor = page.next();
                }
                return current.hasNext();
            }

            @Override public String next() {
                if (!hasNext()) throw new NoSuchElementException();
                return current.next();
            }
        };
    }

    static List<String> take(Iterator<String> it, int n) {
        List<String> out = new ArrayList<>();
        while (out.size() < n && it.hasNext()) out.add(it.next());
        return out;
    }

    public static void main(String[] args) {
        Function<Integer, RefundPage> fetchPage = cursor -> {
            System.out.println("  GET /refunds?cursor=" + cursor);
            return PAGES.get(cursor);
        };
        System.out.println("first two: " + take(refunds(fetchPage), 2));
        System.out.println("all: " + take(refunds(fetchPage), Integer.MAX_VALUE));
    }
}
