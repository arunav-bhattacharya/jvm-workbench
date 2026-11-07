package workbench.patterns.l10;

import java.util.ArrayList;
import java.util.List;

/** A cart that can hand out a snapshot of itself and later put it back. */
public class MementoDemo {
    static final class Cart {
        private final List<String> items = new ArrayList<>();
        private String coupon = "";

        void add(String item) { items.add(item); }
        void coupon(String code) { coupon = code; }
        @Override public String toString() { return items + " coupon=" + coupon; }

        // callers see an opaque Memento; only Cart can read the State inside it
        interface Memento {}
        private record State(List<String> items, String coupon) implements Memento {}

        Memento save() {
            return new State(List.copyOf(items), coupon);         // copy: later edits must not leak in
        }

        void restore(Memento m) {
            State s = (State) m;
            items.clear();
            items.addAll(s.items());                              // copy back in: the memento stays as it was
            coupon = s.coupon();
        }
    }

    public static void main(String[] args) {
        Cart cart = new Cart();
        cart.add("sku-1");
        Cart.Memento before = cart.save();
        cart.add("sku-2");
        cart.coupon("AUTUMN10");
        System.out.println("edited:   " + cart);
        cart.restore(before);
        System.out.println("restored: " + cart);
    }
}
