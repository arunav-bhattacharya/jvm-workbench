package workbench.modernjava.l01.demo;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Equality, hashCode and toString are only as deep as the components. */
public class ShallowDemo {

    // a crate of books on its way to a branch library
    record Crate(String branch, List<String> titles) {}

    record SafeCrate(String branch, List<String> titles) {
        SafeCrate { titles = List.copyOf(titles); }               // unmodifiable copy
    }

    record Masked(String phone) {
        @Override
        public String phone() { return "****" + phone.substring(phone.length() - 4); }
    }

    record Rating(double stars) {}

    public static void main(String[] args) {
        List<String> titles = new ArrayList<>(List.of("Dune", "Emma"));
        Crate crate = new Crate("NORTH", titles);
        Set<Crate> sent = new HashSet<>(Set.of(crate));
        int before = crate.hashCode();

        titles.add("Ulysses");                                    // someone reuses their list

        System.out.println("crate now:          " + crate);
        System.out.println("hashCode changed:   " + (before != crate.hashCode()));
        System.out.println("sent.contains:      " + sent.contains(crate));

        List<String> titles2 = new ArrayList<>(List.of("Dune", "Emma"));
        SafeCrate safe = new SafeCrate("SOUTH", titles2);
        titles2.add("Ulysses");
        System.out.println("safe crate:         " + safe);

        Masked m = new Masked("01614960123");
        System.out.println("accessor:           " + m.phone());
        System.out.println("toString:           " + m);
        System.out.println("copy equals orig:   " + new Masked(m.phone()).equals(m));

        System.out.println("NaN record equals:  " + new Rating(Double.NaN).equals(new Rating(Double.NaN))
                + "  (but NaN == NaN is " + (Double.NaN == Double.NaN) + ")");
        System.out.println("0.0 vs -0.0 equals: " + new Rating(0.0).equals(new Rating(-0.0))
                + " (but 0.0 == -0.0 is " + (0.0 == -0.0) + ")");
    }
}
