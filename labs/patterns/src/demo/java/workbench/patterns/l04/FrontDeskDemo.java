package workbench.patterns.l04;

import java.util.HashSet;
import java.util.Set;

/** A facade over stock, vans and messages: one call, the right order, cleanup on failure. */
public class FrontDeskDemo {
    interface Stock { boolean reserve(String product); void release(String product); }
    interface Vans { String book(String product, String address); }
    interface Notifier { void send(String to, String message); }

    record FrontDesk(Stock stock, Vans vans, Notifier notifier) {
        String order(String product, String address, String email) {
            if (!stock.reserve(product)) throw new IllegalStateException("out of stock: " + product);   // 1. reserve
            String booking;
            try {
                booking = vans.book(product, address);                                               // 2. book a van
            } catch (RuntimeException e) {
                stock.release(product);                                                              // 3. undo the reservation
                throw e;
            }
            notifier.send(email, "on its way, booking " + booking);                                  // 4. tell the customer
            return booking;
        }
    }

    public static void main(String[] args) {
        Set<String> reserved = new HashSet<>();
        Stock stock = new Stock() {
            public boolean reserve(String product) { return reserved.add(product); }
            public void release(String product) { reserved.remove(product); }
        };
        Vans vans = (product, address) -> {
            if (address.contains("Island")) throw new IllegalStateException("no van goes to " + address);
            return "V-" + product;
        };
        Notifier notifier = (to, message) -> System.out.println("  mail to " + to + ": " + message);

        FrontDesk desk = new FrontDesk(stock, vans, notifier);
        System.out.println("booking: " + desk.order("flour", "12 Mill Lane", "anna@example.com"));
        try {
            desk.order("sugar", "Gull Island", "ben@example.com");
        } catch (IllegalStateException e) {
            System.out.println("failed: " + e.getMessage() + "; still reserved: " + reserved);
        }
    }
}
