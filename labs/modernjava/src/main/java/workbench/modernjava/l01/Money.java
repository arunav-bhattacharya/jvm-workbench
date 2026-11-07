package workbench.modernjava.l01;

/**
 * An amount in minor units (cents) and a three-letter currency code.
 *
 * <p>TODO 1: add a compact canonical constructor ({@code public Money { ... }}) that
 * <ul>
 *   <li>rejects a null currency with {@code Objects.requireNonNull(currency, "currency")},</li>
 *   <li>trims and upper-cases the currency, so {@code " eur "} becomes {@code "EUR"}
 *       (use {@code Locale.ROOT}),</li>
 *   <li>then rejects anything that is not exactly three letters A to Z with an
 *       {@link IllegalArgumentException},</li>
 *   <li>rejects a negative {@code minor} with an {@link IllegalArgumentException}.</li>
 * </ul>
 * Reassign the parameter ({@code currency = ...}). The compiler assigns the fields after your code runs.
 */
public record Money(long minor, String currency) {

    /**
     * TODO 2: adds two amounts in the same currency.
     * Different currencies: {@link IllegalArgumentException}. Overflow: {@link ArithmeticException}
     * (use {@code Math.addExact}).
     */
    public Money plus(Money other) {
        throw new UnsupportedOperationException("TODO: plus");
    }
}
