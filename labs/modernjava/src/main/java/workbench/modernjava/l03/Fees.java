package workbench.modernjava.l03;

/**
 * Acquiring fees for a payment, in minor units, rounded down.
 *
 * <p>The model below is given. Write {@link #fee} and {@link #label} as switches with record
 * patterns and guards, and no {@code default}.
 */
public final class Fees {
    private Fees() {}

    public enum Region { EEA, UK, US, OTHER }

    public enum Network { VISA, MASTERCARD, AMEX }

    public record Money(long minor, String currency) {}

    public sealed interface Method permits Card, BankTransfer, Wallet {}

    public record Card(Network network, boolean corporate) implements Method {}

    public record BankTransfer(boolean instant) implements Method {}

    public record Wallet(String provider) implements Method {}

    public record Charge(Money amount, Method method, Region region) {}

    /**
     * TODO 1: the fee for a charge. The rules, in priority order (the first rule that applies wins):
     * <ol>
     *   <li>any AMEX card: 350 basis points (3.5%)</li>
     *   <li>any other corporate card: 290 basis points</li>
     *   <li>a consumer card in the EEA or the UK: 30 basis points</li>
     *   <li>any other card: 150 basis points</li>
     *   <li>an instant bank transfer: a flat 50</li>
     *   <li>any other bank transfer: a flat 20</li>
     *   <li>a wallet payment under 1,000 minor units: 0</li>
     *   <li>any other wallet payment: 100 basis points</li>
     * </ol>
     * Use {@link #bps} for the percentages. A null charge throws {@link NullPointerException}.
     */
    public static long fee(Charge charge) {
        throw new UnsupportedOperationException("TODO: fee");
    }

    /**
     * TODO 2: a short label for the receipt.
     * <ul>
     *   <li>null: {@code "no method"}</li>
     *   <li>an AMEX card: {@code "AMEX"}, whether corporate or not</li>
     *   <li>another corporate card: the network and {@code " corporate"}, e.g. {@code "VISA corporate"}</li>
     *   <li>another card: the network, e.g. {@code "MASTERCARD"}</li>
     *   <li>a bank transfer: {@code "instant transfer"} or {@code "transfer"}</li>
     *   <li>a wallet: {@code "wallet "} and the provider, or {@code "wallet ?"} when the provider is null</li>
     * </ul>
     */
    public static String label(Method method) {
        throw new UnsupportedOperationException("TODO: label");
    }

    /** {@code minor * basisPoints / 10,000}, rounded down; throws ArithmeticException on overflow. */
    static long bps(long minor, int basisPoints) {
        return Math.multiplyExact(minor, basisPoints) / 10_000;
    }
}
