package workbench.modernjava.l02.demo;

/** Three switches over one sealed type. Add a subtype and see which ones the compiler finds. */
public class DisputeSwitches {

    sealed interface Dispute permits Opened, EvidenceSent, Won, Lost {}

    record Opened(String caseId, long amountMinor) implements Dispute {}

    record EvidenceSent(String caseId) implements Dispute {}

    record Won(String caseId) implements Dispute {}

    record Lost(String caseId, long amountMinor) implements Dispute {}

    // Step 2: add Arbitration to the permits clause, then uncomment this record.
    // record Arbitration(String caseId, long feeMinor) implements Dispute {}

    static String label(Dispute d) {
        return switch (d) {                          // exhaustive, no default
            case Opened o -> "opened";
            case EvidenceSent e -> "evidence sent";
            case Won w -> "won";
            case Lost l -> "lost";
        };
    }

    static long ledgerImpact(Dispute d) {
        return switch (d) {                          // exhaustive, no default
            case Opened o -> -o.amountMinor();       // money held back while the case runs
            case EvidenceSent e -> 0;
            case Won w -> 0;
            case Lost l -> -l.amountMinor();
        };
    }

    static int slaDays(Dispute d) {
        return switch (d) {
            case Opened o -> 7;
            case EvidenceSent e -> 30;
            default -> 0;                            // "and anything else": the compiler stops checking
        };
    }

    public static void main(String[] args) {
        Dispute[] all = { new Opened("cb_1", 4_200), new EvidenceSent("cb_1"), new Won("cb_1"), new Lost("cb_2", 990) };
        for (Dispute d : all) {
            System.out.printf("%-14s impact %6d   sla %2d days%n", label(d), ledgerImpact(d), slaDays(d));
        }
    }
}
