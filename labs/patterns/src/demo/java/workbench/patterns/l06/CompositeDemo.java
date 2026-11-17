package workbench.patterns.l06;

import java.util.ArrayList;
import java.util.List;

/** The Saturday breakfast box as a tree. Items and boxes share one sealed type, so one switch prices them all. */
public class CompositeDemo {
    sealed interface Goods permits Item, Box {}
    record Item(String name, long cents) implements Goods {}
    record Box(List<Goods> contents) implements Goods {
        Box { contents = List.copyOf(contents); }        // copy what we were given: the tree stays immutable
    }

    static long price(Goods g) {
        return switch (g) {                               // no default: a new node type breaks the build
            case Item i -> i.cents();
            case Box b -> b.contents().stream().mapToLong(CompositeDemo::price).sum();
        };
    }

    static String describe(Goods g) {
        return switch (g) {
            case Item i -> i.name() + " " + String.format("%d.%02d", i.cents() / 100, i.cents() % 100);
            case Box b -> "(" + String.join(" + ", b.contents().stream().map(CompositeDemo::describe).toList()) + ")";
        };
    }

    public static void main(String[] args) {
        List<Goods> extras = new ArrayList<>(List.of(new Item("tea", 450)));
        Goods breakfast = new Box(List.of(new Item("bread", 250), new Item("jam", 300), new Box(extras)));
        System.out.println("box: " + describe(breakfast));
        System.out.println("price: " + price(breakfast) + " cents");
        System.out.println("a box of two breakfast boxes: " + price(new Box(List.of(breakfast, breakfast))) + " cents");

        extras.add(new Item("champagne", 3_000));         // someone edits the list they passed in
        System.out.println("after editing the source list: " + describe(breakfast));
    }
}
