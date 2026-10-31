package workbench.patterns.l04;

import java.util.HashSet;
import java.util.Set;

/** A facade over inventory, payments and notifications: one call, the right order, cleanup on failure. */
public class CheckoutFacadeDemo {
    interface Inventory { boolean reserve(String sku); void release(String sku); }
    interface Payments { String charge(long amountMinor, String token); }
    interface Notifier { void send(String to, String message); }

    record CheckoutFacade(Inventory inventory, Payments payments, Notifier notifier) {
        String checkout(String sku, long amountMinor, String token, String email) {
            if (!inventory.reserve(sku)) throw new IllegalStateException("out of stock: " + sku);   // 1. reserve
            String receipt;
            try {
                receipt = payments.charge(amountMinor, token);                                     // 2. charge
            } catch (RuntimeException e) {
                inventory.release(sku);                                                            // 3. undo the reservation
                throw e;
            }
            notifier.send(email, "paid " + receipt);                                               // 4. tell the customer
            return receipt;
        }
    }

    public static void main(String[] args) {
        Set<String> reserved = new HashSet<>();
        Inventory inventory = new Inventory() {
            public boolean reserve(String sku) { return reserved.add(sku); }
            public void release(String sku) { reserved.remove(sku); }
        };
        Payments payments = (amount, token) -> {
            if (token.equals("tok_declined")) throw new IllegalStateException("card declined");
            return "R-" + amount;
        };
        Notifier notifier = (to, message) -> System.out.println("  mail to " + to + ": " + message);

        CheckoutFacade facade = new CheckoutFacade(inventory, payments, notifier);
        System.out.println("receipt: " + facade.checkout("sku-1", 1_250, "tok_ok", "anna@example.com"));
        try {
            facade.checkout("sku-2", 990, "tok_declined", "anna@example.com");
        } catch (IllegalStateException e) {
            System.out.println("failed: " + e.getMessage() + "; still reserved: " + reserved);
        }
    }
}
