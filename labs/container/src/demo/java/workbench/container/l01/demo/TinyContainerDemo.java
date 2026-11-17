package workbench.container.l01.demo;

import java.lang.reflect.Constructor;

/** The smallest container that works: read a constructor, build its parameters first, then call it. */
public class TinyContainerDemo {
    public static class SeatingPlan {
        public SeatingPlan() { System.out.println("  new SeatingPlan"); }
    }

    public static class PriceList {
        public PriceList(SeatingPlan plan) { System.out.println("  new PriceList"); }
    }

    public static class SeatFinder {
        public SeatFinder(SeatingPlan plan) { System.out.println("  new SeatFinder"); }
    }

    public static class BoxOffice {
        public BoxOffice(PriceList prices, SeatFinder finder) { System.out.println("  new BoxOffice"); }
    }

    static Object build(Class<?> type) throws ReflectiveOperationException {
        Constructor<?> constructor = type.getConstructors()[0];          // 1. the recipe is the constructor
        Class<?>[] needs = constructor.getParameterTypes();
        Object[] args = new Object[needs.length];
        for (int i = 0; i < needs.length; i++) args[i] = build(needs[i]); // 2. build what it needs first
        return constructor.newInstance(args);                            // 3. then the object itself
    }

    public static void main(String[] args) throws Exception {
        System.out.println("by hand:");
        SeatingPlan plan = new SeatingPlan();
        new BoxOffice(new PriceList(plan), new SeatFinder(plan));

        System.out.println("by reflection:");
        build(BoxOffice.class);
    }
}
