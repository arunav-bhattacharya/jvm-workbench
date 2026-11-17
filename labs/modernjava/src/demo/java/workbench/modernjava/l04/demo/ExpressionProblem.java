package workbench.modernjava.l04.demo;

import java.util.List;

/** Data in records, operations in functions. Add an operation, then add a type, and compare the cost. */
public class ExpressionProblem {

    // what can happen on a member's account
    sealed interface Activity permits Borrowed, Returned, Renewed {}

    record Borrowed(String title, int days) implements Activity {}

    record Returned(String title) implements Activity {}

    record Renewed(String title, int extraDays) implements Activity {}

    // Step 3: add Lost to the permits clause, then uncomment this record.
    // record Lost(String title, int daysOverdue) implements Activity {}

    // operation 1: how the activity changes the number of books the member has out
    static int booksOutDelta(Activity a) {
        return switch (a) {
            case Borrowed b -> 1;
            case Returned r -> -1;
            case Renewed r -> 0;
        };
    }

    // operation 2: the line in the member's history
    static String historyLine(Activity a) {
        return switch (a) {
            case Borrowed(var title, var days) -> "borrowed " + title + " for " + days + " days";
            case Returned(var title) -> "returned " + title;
            case Renewed(var title, var extra) -> "renewed  " + title + " for " + extra + " more days";
        };
    }

    // Step 2: write operation 3 here, sendsReceipt(Activity), as one more switch.

    public static void main(String[] args) {
        List<Activity> week = List.of(new Borrowed("Dune", 21), new Borrowed("Emma", 21), new Returned("Dune"), new Renewed("Emma", 14));
        int booksOut = 0;
        for (Activity a : week) {
            booksOut += booksOutDelta(a);
            System.out.println(historyLine(a));
        }
        System.out.println("books out: " + booksOut);
    }
}
