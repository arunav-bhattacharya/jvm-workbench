package workbench.modernjava.l03;

public final class LoanRules {
    private LoanRules() {}

    public enum Format { HARDBACK, PAPERBACK, LARGE_PRINT }

    public enum Branch { CENTRAL, NORTH, BUS }

    public record Member(String id, int age) {}

    public sealed interface Item permits Book, Disc, Magazine {}

    public record Book(Format format, boolean newRelease) implements Item {}

    public record Disc(boolean boxSet) implements Item {}

    public record Magazine(String title) implements Item {}

    public record Loan(Member member, Item item, Branch branch) {}

    public static int loanDays(Loan loan) {
        // cases are tried top to bottom: the guards encode the priority order.
        // no "case null", so a null loan throws NullPointerException, which is what we want.
        return switch (loan) {
            case Loan(var m, Book(var format, var isNew), var b) when format == Format.LARGE_PRINT -> 42;
            case Loan(var m, Book(var format, var isNew), var b) when isNew -> 7;
            case Loan(var m, Book book, var b) when b == Branch.BUS -> 28;
            case Loan(var m, Book book, var b) -> 21;                          // unguarded: closes the book family
            case Loan(var m, Disc(var boxSet), var b) when boxSet -> 14;
            case Loan(var m, Disc disc, var b) -> 7;
            case Loan(Member(var id, int age), Magazine mag, var b) when age < 12 -> 14;
            case Loan(Member member, Magazine mag, var b) -> 7;                // a type pattern: covers every member
        };   // exhaustive with no default: Book, Disc and Magazine each end with an unguarded case
    }

    public static String label(Item item) {
        return switch (item) {
            case null -> "no item";                                     // without this, null throws NPE
            case Book(var format, var isNew) when format == Format.LARGE_PRINT -> "LARGE_PRINT";
            case Book(var format, var isNew) when isNew -> format + " new";
            case Book(var format, var isNew) -> format.name();
            case Disc(var boxSet) when boxSet -> "box set";
            case Disc d -> "disc";
            // the nested type pattern String t matches a null title too, so check for it first
            case Magazine(String t) when t == null -> "magazine ?";
            case Magazine(String t) -> "magazine " + t;
        };
    }
}
