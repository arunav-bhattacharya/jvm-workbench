package workbench.modernjava.l03;

/**
 * How long a member may keep an item, and the label printed on the loan slip.
 *
 * <p>The model below is given. Write {@link #loanDays} and {@link #label} as switches with record
 * patterns and guards, and no {@code default}.
 */
public final class LoanRules {
    private LoanRules() {}

    public enum Format { HARDBACK, PAPERBACK, LARGE_PRINT }

    public enum Branch { CENTRAL, NORTH, BUS }       // BUS: the library bus, which comes back every four weeks

    public record Member(String id, int age) {}

    public sealed interface Item permits Book, Disc, Magazine {}

    public record Book(Format format, boolean newRelease) implements Item {}

    public record Disc(boolean boxSet) implements Item {}

    public record Magazine(String title) implements Item {}

    public record Loan(Member member, Item item, Branch branch) {}

    /**
     * TODO 1: the loan period in days. The rules, in priority order (the first rule that applies wins):
     * <ol>
     *   <li>any large-print book: 42</li>
     *   <li>any other new-release book: 7</li>
     *   <li>any other book borrowed from the library bus: 28</li>
     *   <li>any other book: 21</li>
     *   <li>a box-set disc: 14</li>
     *   <li>any other disc: 7</li>
     *   <li>a magazine borrowed by a child (a member under 12): 14</li>
     *   <li>any other magazine: 7</li>
     * </ol>
     * A null loan throws {@link NullPointerException}.
     */
    public static int loanDays(Loan loan) {
        throw new UnsupportedOperationException("TODO: loanDays");
    }

    /**
     * TODO 2: a short label for the loan slip.
     * <ul>
     *   <li>null: {@code "no item"}</li>
     *   <li>a large-print book: {@code "LARGE_PRINT"}, whether it is a new release or not</li>
     *   <li>another new-release book: the format and {@code " new"}, e.g. {@code "HARDBACK new"}</li>
     *   <li>another book: the format, e.g. {@code "PAPERBACK"}</li>
     *   <li>a disc: {@code "box set"} or {@code "disc"}</li>
     *   <li>a magazine: {@code "magazine "} and the title, or {@code "magazine ?"} when the title is null</li>
     * </ul>
     */
    public static String label(Item item) {
        throw new UnsupportedOperationException("TODO: label");
    }
}
