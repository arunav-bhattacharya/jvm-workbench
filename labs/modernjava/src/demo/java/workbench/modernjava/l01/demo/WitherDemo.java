package workbench.modernjava.l01.demo;

import java.util.ArrayList;
import java.util.List;

/** Java has no copy(): you write withers by hand, and each one calls the canonical constructor. */
public class WitherDemo {

    record Loan(String memberId, int days, List<String> titles) {
        Loan {
            if (days <= 0) throw new IllegalArgumentException("days must be positive: " + days);
            titles = List.copyOf(titles);
        }

        Loan withDays(int newDays) { return new Loan(memberId, newDays, titles); }
        Loan withTitle(String extra) {
            var more = new ArrayList<>(titles);
            more.add(extra);
            return new Loan(memberId, days, more);
        }
    }

    public static void main(String[] args) {
        Loan first = new Loan("M-1042", 21, List.of("Dune"));
        Loan renewed = first.withDays(35).withTitle("Emma");

        System.out.println("original: " + first);
        System.out.println("changed:  " + renewed);
        System.out.println("same titles list object: " + (first.titles() == first.withDays(14).titles()));
        try {
            first.withDays(-1);
        } catch (IllegalArgumentException e) {
            System.out.println("wither ran the checks: " + e.getMessage());
        }
    }
}
