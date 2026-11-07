package workbench.modernjava.l01;

/**
 * A card number (PAN). Two card numbers with the same digits are equal.
 *
 * <p>TODO 5: add a compact canonical constructor that rejects null, removes spaces
 * ({@code "4111 1111 1111 1111"} becomes {@code "4111111111111111"}), and then rejects anything
 * that is not 12 to 19 digits with an {@link IllegalArgumentException}.
 *
 * <p>TODO 6: the generated {@code toString} prints the whole number into every log line that
 * touches this record. Override {@code toString} to return {@code "CardNumber[****1111]"}
 * (four stars, then the last four digits). Leave the {@code digits()} accessor alone: other
 * code needs the real number, and a masked accessor would break {@code equals}.
 */
public record CardNumber(String digits) {

    /** TODO 7: the last four digits. */
    public String last4() {
        throw new UnsupportedOperationException("TODO: last4");
    }
}
