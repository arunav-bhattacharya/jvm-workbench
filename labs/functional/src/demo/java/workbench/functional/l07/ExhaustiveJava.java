package workbench.functional.l07;

import java.util.List;

/** The same closed set of failures with Java 21 sealed interfaces, records and an exhaustive switch. */
public class ExhaustiveJava {
    sealed interface AuthFailure {}
    record InvalidAmount(long amountMinor) implements AuthFailure {}
    record CardExpired() implements AuthFailure {}
    record InsufficientFunds(long shortByMinor) implements AuthFailure {}
    // Uncomment the next line and run again.
    // record FraudSuspected(int score) implements AuthFailure {}

    sealed interface AuthResult {}
    record Approved(String code) implements AuthResult {}
    record Refused(AuthFailure reason) implements AuthResult {}

    static AuthResult authorizeCard(long amountMinor, long balanceMinor, int expiryYear) {
        if (amountMinor <= 0) return new Refused(new InvalidAmount(amountMinor));
        if (expiryYear < 2026) return new Refused(new CardExpired());
        if (amountMinor > balanceMinor) return new Refused(new InsufficientFunds(amountMinor - balanceMinor));
        return new Approved("A-" + amountMinor % 997);
    }

    /** The one place that knows HTTP: an exhaustive switch with no default branch. */
    static int httpStatus(AuthFailure failure) {
        return switch (failure) {
            case InvalidAmount a -> 400;
            case CardExpired c -> 402;
            case InsufficientFunds i -> 402;
        };
    }

    public static void main(String[] args) {
        List<long[]> attempts = List.of(new long[] {4_250, 10_000, 2028}, new long[] {-5, 10_000, 2028},
                new long[] {4_250, 10_000, 2024}, new long[] {14_250, 10_000, 2028});
        for (long[] a : attempts) {
            String line = switch (authorizeCard(a[0], a[1], (int) a[2])) {
                case Approved ok -> "200 approved " + ok.code();
                case Refused r -> httpStatus(r.reason()) + " " + r.reason();
            };
            System.out.println(line);
        }
    }
}
