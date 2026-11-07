package workbench.kotlin.l03.demo;

import java.lang.reflect.Field;

/**
 * Java twin of PropertyDelegateDemo.kt. Java sees getStatus and setStatus, ordinary methods,
 * and can't tell that a delegate sits behind them.
 */
public class PropertyDelegateDemoJava {

    // the hand-written Java shape: a field holding a helper object, and accessors that call it
    static final class Box<T> {
        private T value;
        Box(T value) { this.value = value; }
        T get() { return value; }
        void set(String name, T value) {
            System.out.println("  " + name + ": " + this.value + " -> " + value);
            this.value = value;
        }
    }

    static final class OrderJava {
        private final Box<String> status = new Box<>("NEW");
        String getStatus() { return status.get(); }
        void setStatus(String s) { status.set("status", s); }
    }

    public static void main(String[] args) {
        Order order = new Order();                 // the Kotlin class
        order.setStatus("AUTHORIZED");             // goes through status$delegate.setValue
        order.setAmountMinor(4_250L);
        System.out.println("status = " + order.getStatus() + ", amountMinor = " + order.getAmountMinor());

        OrderJava hand = new OrderJava();
        hand.setStatus("AUTHORIZED");

        System.out.println("fields of the Kotlin Order, seen by reflection:");
        for (Field f : Order.class.getDeclaredFields()) {
            System.out.println("  " + f.getType().getSimpleName() + " " + f.getName());
        }
    }
}
