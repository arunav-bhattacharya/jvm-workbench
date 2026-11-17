package workbench.patterns.l10;

import java.util.ArrayList;
import java.util.List;

/** A shelf that can hand out a photo of itself and later be put back exactly as in the photo. */
public class MementoDemo {
    static final class Shelf {
        private final List<String> items = new ArrayList<>();
        private String sign = "";

        void add(String item) { items.add(item); }
        void sign(String text) { sign = text; }
        @Override public String toString() { return items + " sign=" + sign; }

        // callers see an opaque Memento; only Shelf can read the Photo inside it
        interface Memento {}
        private record Photo(List<String> items, String sign) implements Memento {}

        Memento save() {
            return new Photo(List.copyOf(items), sign);           // copy: later changes must not leak in
        }

        void restore(Memento m) {
            Photo p = (Photo) m;
            items.clear();
            items.addAll(p.items());                              // copy back in: the photo stays as it was
            sign = p.sign();
        }
    }

    public static void main(String[] args) {
        Shelf shelf = new Shelf();
        shelf.add("rye bread");
        Shelf.Memento before = shelf.save();
        shelf.add("jam");
        shelf.sign("Autumn sale");
        System.out.println("changed:  " + shelf);
        shelf.restore(before);
        System.out.println("restored: " + shelf);
    }
}
