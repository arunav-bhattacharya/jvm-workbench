package workbench.modernjava.l03;

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

    public static long fee(Charge charge) {
        // cases are tried top to bottom: the guards encode the priority order.
        // no "case null", so a null charge throws NullPointerException, which is what we want.
        return switch (charge) {
            case Charge(Money(long m, var ccy), Card(var net, var corp), var r) when net == Network.AMEX -> bps(m, 350);
            case Charge(Money(long m, var ccy), Card(var net, var corp), var r) when corp -> bps(m, 290);
            case Charge(Money(long m, var ccy), Card c, var r) when r == Region.EEA || r == Region.UK -> bps(m, 30);
            case Charge(Money(long m, var ccy), Card c, var r) -> bps(m, 150);           // unguarded: closes the card family
            case Charge(var amount, BankTransfer(var instant), var r) when instant -> 50;
            case Charge(var amount, BankTransfer t, var r) -> 20;
            case Charge(Money(long m, var ccy), Wallet w, var r) when m < 1_000 -> 0;
            case Charge(Money(long m, var ccy), Wallet w, var r) -> bps(m, 100);
        };   // exhaustive with no default: Card, BankTransfer and Wallet each end with an unguarded case
    }

    public static String label(Method method) {
        return switch (method) {
            case null -> "no method";                                  // without this, null throws NPE
            case Card(var net, var corp) when net == Network.AMEX -> "AMEX";
            case Card(var net, var corp) when corp -> net + " corporate";
            case Card(var net, var corp) -> net.name();
            case BankTransfer(var instant) when instant -> "instant transfer";
            case BankTransfer t -> "transfer";
            // the nested type pattern String p matches a null provider too, so check for it first
            case Wallet(String p) when p == null -> "wallet ?";
            case Wallet(String p) -> "wallet " + p;
        };
    }

    static long bps(long minor, int basisPoints) {
        return Math.multiplyExact(minor, basisPoints) / 10_000;
    }
}
