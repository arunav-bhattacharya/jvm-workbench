package workbench.ledger.l01.demo;

import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.LongAdder;

/** An importer parses 100,000 lines and hands each one to a pool. Pass "record" to use an immutable value. */
public class ReusedTransferDemo {
    // the mutable row a parser fills in for each line, then reuses for the next line
    static final class TransferRow {
        String id;
        long cents;
    }

    record Transfer(String id, long cents) {}       // immutable: one new value per line

    public static void main(String[] args) throws InterruptedException {
        boolean immutable = args.length > 0 && args[0].equals("record");
        ExecutorService pool = Executors.newFixedThreadPool(4);
        LongAdder appliedCents = new LongAdder();
        Set<String> appliedLines = ConcurrentHashMap.newKeySet();
        AtomicInteger mixed = new AtomicInteger();
        long fileCents = 0;
        TransferRow row = new TransferRow();
        for (int line = 0; line < 100_000; line++) {
            long cents = 100 + line % 900;
            fileCents += cents;
            if (immutable) {
                Transfer t = new Transfer("line-" + line, cents);
                pool.execute(() -> applyLine(t.id(), t.cents(), appliedCents, appliedLines, mixed));
            } else {
                row.id = "line-" + line;                 // overwrite the shared row...
                row.cents = cents;
                pool.execute(() -> applyLine(row.id, row.cents, appliedCents, appliedLines, mixed));   // ...read it later
            }
        }
        pool.shutdown();
        pool.awaitTermination(30, TimeUnit.SECONDS);
        System.out.printf("file: 100,000 lines, %,d cents%n", fileCents);
        System.out.printf("applied: %,d different lines, %,d cents, %,d rows mixing two lines%n",
                appliedLines.size(), appliedCents.sum(), mixed.get());
    }

    // stands in for ledger.apply: records what the worker saw
    static void applyLine(String id, long cents, LongAdder appliedCents, Set<String> lines, AtomicInteger mixed) {
        appliedCents.add(cents);
        lines.add(id);
        int line = Integer.parseInt(id.substring("line-".length()));
        if (cents != 100 + line % 900) mixed.incrementAndGet();   // the id and the amount came from different lines
    }
}
