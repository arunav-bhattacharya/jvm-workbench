package workbench.patterns.l10;

import java.util.List;

/** The same breakfast box priced with a classic Visitor and with a sealed switch, then checked by an inspector. */
public class VisitorVsSwitch {
    interface GoodsVisitor<R> { R visitItem(Item i); R visitFresh(Fresh f); R visitBox(Box b); }

    sealed interface Goods permits Item, Fresh, Box { <R> R accept(GoodsVisitor<R> v); }
    record Item(String name, long cents) implements Goods {
        public <R> R accept(GoodsVisitor<R> v) { return v.visitItem(this); }
    }
    record Fresh(String name, long cents, int daysLeft) implements Goods {
        public <R> R accept(GoodsVisitor<R> v) { return v.visitFresh(this); }
    }
    record Box(List<Goods> contents) implements Goods {
        public <R> R accept(GoodsVisitor<R> v) { return v.visitBox(this); }
    }

    // operation 1, visitor style: one class per operation, one method per kind of goods
    static final class Price implements GoodsVisitor<Long> {
        public Long visitItem(Item i) { return i.cents(); }
        public Long visitFresh(Fresh f) { return f.daysLeft() == 0 ? f.cents() / 2 : f.cents(); }
        public Long visitBox(Box b) {
            long sum = 0;
            for (Goods g : b.contents()) sum += g.accept(this);
            return sum;
        }
    }

    // operation 1 again, data style: no accept needed, no visitor interface
    static long price(Goods g) {
        return switch (g) {
            case Item(var name, var cents) -> cents;
            case Fresh(var name, var cents, var days) when days == 0 -> cents / 2;   // last day: half price
            case Fresh(var name, var cents, var days) -> cents;
            case Box(var contents) -> contents.stream().mapToLong(VisitorVsSwitch::price).sum();
        };
    }

    // operation 2, the inspector: just one more function, with a different check for each kind
    static List<String> inspect(Goods g) {
        return switch (g) {
            case Item i -> i.cents() > 0 ? List.of() : List.of(i.name() + ": no price label");
            case Fresh f -> f.daysLeft() > 0 ? List.of() : List.of(f.name() + ": last day");
            case Box b -> b.contents().stream().flatMap(x -> inspect(x).stream()).toList();
        };
    }

    public static void main(String[] args) {
        Goods breakfast = new Box(List.of(new Fresh("rye bread", 250, 2), new Item("jam", 300),
                new Box(List.of(new Item("tea", 450), new Fresh("milk", 120, 0)))));
        System.out.println("breakfast box: " + breakfast.accept(new Price()) + " cents (visitor) = "
                + price(breakfast) + " cents (switch)");
        System.out.println("inspector found: " + inspect(breakfast));
    }
}
