package workbench.modernjava.l03.demo;

/** Cases are tried from the top, and the first one that matches wins. Guards decide the order. */
public class GuardsDemo {

    enum Format { HARDBACK, PAPERBACK, LARGE_PRINT }

    sealed interface Item permits Book, Disc {}

    record Book(Format format, boolean newRelease) implements Item {}

    record Disc(boolean boxSet) implements Item {}

    static int loanDays(Item item) {
        return switch (item) {
            case Book(var format, var isNew) when format == Format.LARGE_PRINT -> 42;   // 1
            case Book(var format, var isNew) when isNew -> 7;                          // 2
            case Book(var format, var isNew) -> 21;                                    // 3
            case Disc(var boxSet) when boxSet -> 14;
            case Disc d -> 7;
        };
    }

    public static void main(String[] args) {
        Item[] items = {
            new Book(Format.LARGE_PRINT, false),
            new Book(Format.LARGE_PRINT, true),
            new Book(Format.HARDBACK, true),
            new Book(Format.PAPERBACK, false),
            new Disc(true),
        };
        for (Item i : items) {
            System.out.printf("%-42s %d days%n", i, loanDays(i));
        }
    }
}
