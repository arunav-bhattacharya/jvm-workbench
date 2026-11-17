package workbench.modernjava.l03.demo;

/** The same sorting three ways: an instanceof chain, an early return, and a pattern switch. */
public class PatternBasics {

    sealed interface Item permits Book, Disc, Magazine {}

    record Book(String title, String author) implements Item {}

    record Disc(String title, int minutes) implements Item {}

    record Magazine(String title, int issue) implements Item {}

    // an if-chain: javac never checks that it covers every Item
    static String viaChain(Item i) {
        if (i instanceof Book b) return "book " + b.title() + " by " + b.author();
        else if (i instanceof Disc d) return "disc " + d.title() + ", " + d.minutes() + " min";
        else if (i instanceof Magazine m) return "magazine " + m.title() + " #" + m.issue();
        else throw new IllegalStateException("unreachable?");
    }

    // a pattern switch: javac checks that every Item is covered
    static String viaSwitch(Item i) {
        return switch (i) {
            case Book b -> "book " + b.title() + " by " + b.author();
            case Disc d -> "disc " + d.title() + ", " + d.minutes() + " min";
            case Magazine m -> "magazine " + m.title() + " #" + m.issue();
        };
    }

    // flow scoping: after the negated test returns, b is in scope for the rest of the method
    static String author(Object o) {
        if (!(o instanceof Book b)) return "not a book";
        return "by " + b.author();
    }

    public static void main(String[] args) {
        Item[] returns = { new Book("Emma", "Jane Austen"), new Disc("Paddington", 95), new Magazine("Garden Monthly", 214) };
        for (Item i : returns) {
            System.out.println(viaChain(i) + "  |  " + viaSwitch(i));
        }
        System.out.println(author(returns[0]) + ", " + author("Emma"));
    }
}
