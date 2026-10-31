package workbench.patterns.l02;

import java.util.function.Supplier;

/** A factory method over a sealed family, and the same factory passed around as a function. */
public class GatewayFactory {
    enum Provider { ADYEN, STRIPE, FAKE }

    sealed interface PaymentGateway permits AdyenGateway, StripeGateway, FakeGateway {
        String charge(long amountMinor, String token);

        // the static factory: an exhaustive switch over the enum, with no default branch
        static PaymentGateway of(Provider p) {
            return switch (p) {
                case ADYEN -> new AdyenGateway();
                case STRIPE -> new StripeGateway();
                case FAKE -> new FakeGateway();
            };
        }
    }

    record AdyenGateway() implements PaymentGateway {
        public String charge(long amountMinor, String token) { return "adyen:" + token + ":" + amountMinor; }
    }
    record StripeGateway() implements PaymentGateway {
        public String charge(long amountMinor, String token) { return "stripe:" + token + ":" + amountMinor; }
    }
    record FakeGateway() implements PaymentGateway {
        public String charge(long amountMinor, String token) { return "fake:ok"; }
    }

    // the modern "factory method": the caller hands in how to make the product
    record Checkout(Supplier<? extends PaymentGateway> gateways) {
        String pay(long amountMinor, String token) { return gateways.get().charge(amountMinor, token); }
    }

    public static void main(String[] args) {
        for (Provider p : Provider.values()) {
            System.out.println(p + " -> " + PaymentGateway.of(p).charge(1_250, "tok_42"));
        }
        System.out.println("test checkout -> " + new Checkout(FakeGateway::new).pay(1_250, "tok_42"));
    }
}
