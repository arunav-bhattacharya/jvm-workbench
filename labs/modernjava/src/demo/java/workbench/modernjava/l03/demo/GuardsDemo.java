package workbench.modernjava.l03.demo;

/** Cases are tried from the top, and the first one that matches wins. Guards decide the order. */
public class GuardsDemo {

    enum Network { VISA, MASTERCARD, AMEX }

    sealed interface Charge permits CardCharge, TransferCharge {}

    record CardCharge(Network network, boolean corporate, long amountMinor) implements Charge {}

    record TransferCharge(boolean instant, long amountMinor) implements Charge {}

    static long fee(Charge c) {
        return switch (c) {
            case CardCharge(var net, var corp, var amt) when net == Network.AMEX -> amt * 350 / 10_000;   // 1
            case CardCharge(var net, var corp, var amt) when corp -> amt * 290 / 10_000;                  // 2
            case CardCharge(var net, var corp, var amt) -> amt * 30 / 10_000;                             // 3
            case TransferCharge(var instant, var amt) when instant -> 50;
            case TransferCharge t -> 20;
        };
    }

    public static void main(String[] args) {
        Charge[] charges = {
            new CardCharge(Network.AMEX, false, 10_000),
            new CardCharge(Network.AMEX, true, 10_000),
            new CardCharge(Network.VISA, true, 10_000),
            new CardCharge(Network.VISA, false, 10_000),
            new TransferCharge(true, 10_000),
        };
        for (Charge c : charges) {
            System.out.printf("%-62s fee %d%n", c, fee(c));
        }
    }
}
