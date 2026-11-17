package workbench.patterns.l10;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.NoSuchElementException;
import java.util.function.Function;

/** Walk the warehouse program's stock list lazily. Java has no generators, so the iterator's state is written by hand. */
public class PagingDemoJava {
    record StockPage(List<String> items, Integer next) {}

    static final Map<Integer, StockPage> PAGES = Map.of(
            0, new StockPage(List.of("rye bread", "jam"), 1),
            1, new StockPage(List.of(), 2),                         // an empty page in the middle
            2, new StockPage(List.of("tea"), null));

    static Iterator<String> stock(Function<Integer, StockPage> fetch) {
        return new Iterator<>() {
            private Iterator<String> current = Collections.emptyIterator();
            private Integer cursor = 0;                            // null = no more pages

            @Override public boolean hasNext() {
                while (!current.hasNext() && cursor != null) {     // while, not if: skip empty pages
                    StockPage page = fetch.apply(cursor);
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
        Function<Integer, StockPage> fetchPage = cursor -> {
            System.out.println("  warehouse: sending page " + cursor);
            return PAGES.get(cursor);
        };
        System.out.println("first two: " + take(stock(fetchPage), 2));
        System.out.println("all: " + take(stock(fetchPage), Integer.MAX_VALUE));
    }
}
