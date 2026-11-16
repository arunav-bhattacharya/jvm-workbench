// Java equivalent of TransparencyTrap.kt: a hand-written push "flow" has no inspector, so the
// try/catch around the call swallows the ledger's failure and carries on with the next posting.
package workbench.flows.l02;

import java.util.ArrayList;
import java.util.List;
import java.util.function.BiConsumer;

public class TransparencyTrapJava {
    static class LedgerException extends RuntimeException {
        LedgerException(String message) { super(message); }
    }

    record Posting(String id, long cents) {}

    static final List<Posting> BATCH = List.of(new Posting("pay-1", 4250), new Posting("pay-2", -990), new Posting("pay-3", 12000));

    static void postings(BiConsumer<String, Long> ledgerWriter) {
        for (Posting p : BATCH) {
            try {
                ledgerWriter.accept(p.id(), p.cents());
            } catch (RuntimeException e) {
                System.out.println("WARN posting " + p.id() + " failed, skipping it: " + e.getMessage());
            }
        }
    }

    public static void main(String[] args) {
        List<String> posted = new ArrayList<>();
        postings((id, cents) -> {
            if (cents < 0) throw new LedgerException("negative amount " + cents + " for " + id);
            posted.add(id);
        });
        System.out.println("postings returned normally. posted=" + posted);
    }
}
