package workbench.modernjava.l04.demo;

import java.util.List;

/** Data in records, operations in functions. Add an operation, then add a type, and compare the cost. */
public class ExpressionProblem {

    sealed interface LedgerEntry permits Charge, Refund, Fee {}

    record Charge(String paymentId, long amountMinor) implements LedgerEntry {}

    record Refund(String paymentId, long amountMinor) implements LedgerEntry {}

    record Fee(String reason, long amountMinor) implements LedgerEntry {}

    // Step 3: add Chargeback to the permits clause, then uncomment this record.
    // record Chargeback(String paymentId, long amountMinor, String caseId) implements LedgerEntry {}

    // operation 1: how the entry moves the merchant's balance
    static long balanceDelta(LedgerEntry e) {
        return switch (e) {
            case Charge c -> c.amountMinor();
            case Refund r -> -r.amountMinor();
            case Fee f -> -f.amountMinor();
        };
    }

    // operation 2: the line on the merchant's statement
    static String statementLine(LedgerEntry e) {
        return switch (e) {
            case Charge(var id, var amt) -> "payment " + id + "  +" + amt;
            case Refund(var id, var amt) -> "refund  " + id + "  -" + amt;
            case Fee(var reason, var amt) -> "fee     " + reason + "  -" + amt;
        };
    }

    // Step 2: write operation 3 here, isCustomerFacing(LedgerEntry), as one more switch.

    public static void main(String[] args) {
        List<LedgerEntry> day = List.of(new Charge("pay_1", 10_000), new Fee("scheme fee", 35), new Refund("pay_1", 2_500));
        long balance = 0;
        for (LedgerEntry e : day) {
            balance += balanceDelta(e);
            System.out.println(statementLine(e));
        }
        System.out.println("balance " + balance);
    }
}
