package workbench.generics.l11.demo;

import java.util.List;

/** Java twin of StoreroomDemo.kt. Java's interfaces are invariant, so the reader writes ? extends. */
public class StoreroomDemoJava {

    interface DisplayCase<T> { List<T> findAll(); }

    static void printAll(DisplayCase<? extends Item<?>> display) {   // every use must say ? extends
        for (Item<?> item : display.findAll()) System.out.println("  item " + item.getId());
    }

    public static void main(String[] args) {
        DisplayCase<Supplier> suppliers = () -> List.of(new Supplier(2, "Hill Farm"), new Supplier(7, "Orchard Lane"));
        DisplayCase<Crate> crates = () -> List.of(new Crate("c-1", 12_000));
        System.out.println("suppliers:");
        printAll(suppliers);
        System.out.println("crates:");
        printAll(crates);

        // Wrong move. Uncomment, predict the error, then run.
        // DisplayCase<Item<?>> strict = suppliers;
    }
}
