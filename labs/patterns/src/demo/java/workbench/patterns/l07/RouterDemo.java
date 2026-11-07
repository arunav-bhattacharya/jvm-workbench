package workbench.patterns.l07;

import java.util.EnumMap;
import java.util.Map;

/** The same fee rules as a map of strategies and as a switch. Add a payment method and watch which one tells you. */
public class RouterDemo {
    enum PayMethod { CARD, SEPA, WALLET }
    record Pay(PayMethod method, long amountMinor) {}
    interface FeeStrategy { long fee(Pay p); }

    // open set: one lambda per method, in a map that config or plug-ins could fill
    static final Map<PayMethod, FeeStrategy> STRATEGIES = new EnumMap<>(Map.of(
            PayMethod.CARD, p -> 30 + p.amountMinor() * 290 / 10_000,
            PayMethod.SEPA, p -> 25,
            PayMethod.WALLET, p -> p.amountMinor() * 150 / 10_000));

    // closed set: one switch, checked by the compiler
    static long feeSwitch(Pay p) {
        return switch (p.method()) {
            case CARD -> 30 + p.amountMinor() * 290 / 10_000;
            case SEPA -> 25;
            case WALLET -> p.amountMinor() * 150 / 10_000;
        };
    }

    public static void main(String[] args) {
        for (PayMethod m : PayMethod.values()) {
            Pay p = new Pay(m, 10_000);
            System.out.printf("%-7s switch=%d", m, feeSwitch(p));
            System.out.printf("  map=%d%n", STRATEGIES.get(m).fee(p));
        }
    }
}
