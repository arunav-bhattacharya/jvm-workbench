package workbench.events.l01.demo.values;

import java.lang.reflect.Field;
import java.math.BigDecimal;
import java.util.List;

public class ValuesDemoJava {
    record PaymentId(String value) {
        PaymentId {
            if (!value.matches("pay_[A-Za-z0-9]{4,24}")) throw new IllegalArgumentException("invalid payment id: '" + value + "'");
        }
        @Override public String toString() { return value; }
    }

    record Money(long minor) {
        Money {
            if (minor < 0) throw new IllegalArgumentException("amount must not be negative: " + minor);
        }
        @Override public String toString() { return BigDecimal.valueOf(minor, 2).toPlainString(); }
    }

    record PaymentCaptured(PaymentId paymentId, Money amount) {}

    /** The same event with raw types: nothing stops a caller from swapping the two longs. */
    record RawRefund(String paymentId, long amountMinor, long feeMinor) {}

    public static void main(String[] args) {
        System.out.println(new PaymentCaptured(new PaymentId("pay_7781"), new Money(1_999)));
        System.out.println(new RawRefund("pay_7781", 30, 500));    // amount and fee swapped: compiles, wrong money

        // Step 2: uncomment. The arguments are in the wrong order.
        // System.out.println(new PaymentCaptured(new Money(1_999), new PaymentId("pay_7781")));

        List<Runnable> attempts = List.of(() -> new PaymentId("7781"), () -> new Money(-500));
        for (Runnable attempt : attempts) {
            try {
                attempt.run();
            } catch (IllegalArgumentException e) {
                System.out.println("refused: " + e.getMessage());
            }
        }

        // What the JVM stores: each field points at a separate wrapper object on the heap
        for (Field f : PaymentCaptured.class.getDeclaredFields()) System.out.println("field " + f.getName() + ": " + f.getType().getName());
    }
}
