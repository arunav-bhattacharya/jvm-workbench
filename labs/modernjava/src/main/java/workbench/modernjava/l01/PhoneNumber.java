package workbench.modernjava.l01;

/**
 * A member's phone number, so the library can send a text when a reserved book arrives.
 * Two phone numbers with the same digits are equal.
 *
 * <p>TODO 5: add a compact canonical constructor that rejects null, removes spaces
 * ({@code "0161 496 0123"} becomes {@code "01614960123"}), and then rejects anything
 * that is not 7 to 15 digits with an {@link IllegalArgumentException}.
 *
 * <p>TODO 6: the generated {@code toString} prints the whole number into every log line that
 * touches this record. Override {@code toString} to return {@code "PhoneNumber[****0123]"}
 * (four stars, then the last four digits). Leave the {@code digits()} accessor alone: the text
 * service needs the real number, and a masked accessor would break {@code equals}.
 */
public record PhoneNumber(String digits) {

    /** TODO 7: the last four digits, for screens that say "we'll text the number ending 0123". */
    public String last4() {
        throw new UnsupportedOperationException("TODO: last4");
    }
}
