package workbench.modernjava.l01;

/**
 * Where a book lives in the library: a three-letter section code and a shelf number,
 * printed on the spine label as {@code FIC 12}.
 *
 * <p>TODO 1: add a compact canonical constructor ({@code public Shelfmark { ... }}) that
 * <ul>
 *   <li>rejects a null section with {@code Objects.requireNonNull(section, "section")},</li>
 *   <li>trims and upper-cases the section, so {@code " fic "} becomes {@code "FIC"}
 *       (use {@code Locale.ROOT}),</li>
 *   <li>then rejects anything that is not exactly three letters A to Z with an
 *       {@link IllegalArgumentException},</li>
 *   <li>rejects a shelf number outside 1 to 999 with an {@link IllegalArgumentException}.</li>
 * </ul>
 * Reassign the parameter ({@code section = ...}). The compiler assigns the fields after your code runs.
 */
public record Shelfmark(String section, int shelf) {

    /**
     * TODO 2: the shelfmark one shelf further along, in the same section.
     * Shelf 999 has no next shelf: {@link IllegalArgumentException}. Let the constructor say so.
     */
    public Shelfmark next() {
        throw new UnsupportedOperationException("TODO: next");
    }
}
