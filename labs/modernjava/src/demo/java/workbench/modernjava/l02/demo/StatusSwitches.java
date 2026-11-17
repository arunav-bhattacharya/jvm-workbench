package workbench.modernjava.l02.demo;

/** Three switches over one sealed type. Add a subtype and see which ones the compiler finds. */
public class StatusSwitches {

    // where one copy of a book is right now
    sealed interface CopyStatus permits OnShelf, OnLoan, OnHold, Missing {}

    record OnShelf(String shelfmark) implements CopyStatus {}

    record OnLoan(String memberId, int daysLeft) implements CopyStatus {}

    record OnHold(String memberId) implements CopyStatus {}

    record Missing(int daysMissing) implements CopyStatus {}

    // Step 2: add InRepair to the permits clause, then uncomment this record.
    // record InRepair(int daysLeft) implements CopyStatus {}

    static String label(CopyStatus s) {
        return switch (s) {                          // exhaustive, no default
            case OnShelf shelf -> "on shelf";
            case OnLoan loan -> "on loan";
            case OnHold hold -> "on hold";
            case Missing missing -> "missing";
        };
    }

    static boolean canLendToday(CopyStatus s) {
        return switch (s) {                          // exhaustive, no default
            case OnShelf shelf -> true;
            case OnLoan loan -> false;
            case OnHold hold -> false;
            case Missing missing -> false;
        };
    }

    static int reminderDays(CopyStatus s) {
        return switch (s) {
            case OnLoan loan -> loan.daysLeft();     // remind the member before it's due
            case OnHold hold -> 3;                   // the member has three days to collect it
            default -> 0;                            // "and anything else": the compiler stops checking
        };
    }

    public static void main(String[] args) {
        CopyStatus[] copies = { new OnShelf("FIC 12"), new OnLoan("M-1042", 9), new OnHold("M-2210"), new Missing(40) };
        for (CopyStatus s : copies) {
            System.out.printf("%-9s lend today: %-5s  reminder in %d days%n", label(s), canLendToday(s), reminderDays(s));
        }
    }
}
