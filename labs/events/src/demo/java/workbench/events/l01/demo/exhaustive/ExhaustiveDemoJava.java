package workbench.events.l01.demo.exhaustive;

import java.util.List;

public class ExhaustiveDemoJava {
    sealed interface PaymentEvent permits PaymentAuthorized, PaymentDeclined, MoneyMovement {
        String paymentId();
    }
    record PaymentAuthorized(String paymentId, long cents) implements PaymentEvent {}
    record PaymentDeclined(String paymentId, String reason) implements PaymentEvent {}

    sealed interface MoneyMovement extends PaymentEvent permits PaymentCaptured, PaymentRefunded {
        long cents();
    }
    record PaymentCaptured(String paymentId, long cents) implements MoneyMovement {}
    record PaymentRefunded(String paymentId, long cents) implements MoneyMovement {}

    // Step 2: uncomment this line, add PaymentDisputed to the permits list above, and run again.
    // record PaymentDisputed(String paymentId, long cents) implements PaymentEvent {}

    /** One case per leaf, no default: checked by javac. */
    static String summary(PaymentEvent e) {
        return switch (e) {
            case PaymentAuthorized a -> a.paymentId() + " authorized " + a.cents();
            case PaymentDeclined d -> d.paymentId() + " declined: " + d.reason();
            case PaymentCaptured c -> c.paymentId() + " captured " + c.cents();
            case PaymentRefunded r -> r.paymentId() + " refunded " + r.cents();
        };
    }

    /** One case covers the whole sealed middle level, and the check still holds. */
    static boolean movesMoney(PaymentEvent e) {
        return switch (e) {
            case MoneyMovement m -> true;
            case PaymentAuthorized a -> false;
            case PaymentDeclined d -> false;
        };
    }

    /** A default branch: compiles today, and after every change anyone ever makes. */
    static String label(PaymentEvent e) {
        return switch (e) {
            case PaymentCaptured c -> "capture";
            case PaymentRefunded r -> "refund";
            default -> "other";
        };
    }

    public static void main(String[] args) {
        List<PaymentEvent> events = List.of(
                new PaymentAuthorized("pay_7781", 1_999),
                new PaymentCaptured("pay_7781", 1_999),
                new PaymentRefunded("pay_7781", 500),
                new PaymentDeclined("pay_7782", "CARD_EXPIRED"));
        for (PaymentEvent e : events) {
            System.out.printf("%-34s moves money: %-5s label: %s%n", summary(e), movesMoney(e), label(e));
        }
    }
}
