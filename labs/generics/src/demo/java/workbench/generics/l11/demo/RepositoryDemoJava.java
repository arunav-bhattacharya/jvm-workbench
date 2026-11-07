package workbench.generics.l11.demo;

import java.util.List;

/** Java twin of RepositoryDemo.kt. Java's interfaces are invariant, so the reader writes ? extends. */
public class RepositoryDemoJava {

    interface ReadRepository<T> { List<T> findAll(); }

    static void printAll(ReadRepository<? extends Entity<?>> repo) {   // every use must say ? extends
        for (Entity<?> e : repo.findAll()) System.out.println("  entity " + e.getId());
    }

    public static void main(String[] args) {
        ReadRepository<Merchant> merchants = () -> List.of(new Merchant(2, "Bakery"), new Merchant(7, "Kiosk"));
        ReadRepository<Settlement> settlements = () -> List.of(new Settlement("s-1", 1_200));
        System.out.println("merchants:");
        printAll(merchants);
        System.out.println("settlements:");
        printAll(settlements);

        // Wrong move. Uncomment, predict the error, then run.
        // ReadRepository<Entity<?>> strict = merchants;
    }
}
