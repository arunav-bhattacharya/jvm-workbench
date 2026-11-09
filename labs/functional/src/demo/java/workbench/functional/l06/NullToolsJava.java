package workbench.functional.l06;

import java.util.List;
import java.util.Objects;
import java.util.Optional;

/** The same null handling with Optional and Objects. Note which exception each check throws. */
public class NullToolsJava {
    record CardOnFile(String token, String country) {}
    record RefundLine(String paymentId, Long amountMinor, String reason) {}

    static String tokenFor(CardOnFile card) {
        Optional<String> token = Optional.ofNullable(card).map(CardOnFile::token);
        if (token.isEmpty()) return "declined: no card token";
        return "charge with " + token.get().substring(0, 4) + "...";
    }

    public static void main(String[] args) {
        System.out.println(tokenFor(new CardOnFile("tok_4242424242", "NL")));
        System.out.println(tokenFor(new CardOnFile(null, "NL")));
        System.out.println(tokenFor(null));

        // Optional.filter is the closest thing to takeIf
        long amount = 1_999L;
        System.out.println("filter positive: " + Optional.of(amount).filter(a -> a > 0).orElse(null)
                + ", filter over 5,000: " + Optional.of(amount).filter(a -> a > 5_000).orElse(null));

        // Objects.requireNonNull throws NullPointerException; Kotlin's requireNotNull throws IllegalArgumentException
        RefundLine line = new RefundLine("p9", null, "duplicate");
        try {
            Objects.requireNonNull(line.amountMinor(), "refund " + line.paymentId() + " has no amount");
        } catch (NullPointerException e) {
            System.out.println("requireNonNull: " + e.getClass().getSimpleName() + ": " + e.getMessage());
        }

        // mapNotNull: map, then drop the nulls
        List<RefundLine> lines = List.of(line, new RefundLine("p10", 500L, null), new RefundLine("p11", 1_200L, "fraud"));
        System.out.println("reasons: " + lines.stream().map(RefundLine::reason).filter(Objects::nonNull).toList());
    }
}
