package workbench.ledger.l01;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ThreadLocalRandom;
import java.util.function.Function;

public final class StressHarness {
    private StressHarness() {}

    public record Result(long applied, long refused) {
        public long total() {
            return applied + refused;
        }
    }

    public static Result run(int threads, int perThread, List<String> accounts, long maxCents,
                             Function<Transfer, Outcome> ledger) throws InterruptedException {
        CountDownLatch ready = new CountDownLatch(threads);
        CountDownLatch go = new CountDownLatch(1);
        long[] applied = new long[threads];   // one slot per thread, written once at the end
        long[] refused = new long[threads];
        List<Thread> workers = new ArrayList<>();
        for (int i = 0; i < threads; i++) {
            int me = i;
            Thread w = new Thread(() -> {
                ThreadLocalRandom rnd = ThreadLocalRandom.current();   // this thread's own generator
                ready.countDown();                                     // 1. at the start line
                try {
                    go.await();                                        //    wait for the gun
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    return;
                }
                long ok = 0, no = 0;                                   // 2. counted in locals: nothing shared
                for (int n = 0; n < perThread; n++) {
                    int a = rnd.nextInt(accounts.size());
                    int b = rnd.nextInt(accounts.size() - 1);
                    if (b >= a) b++;                                   //    a different account from a
                    long cents = 1 + rnd.nextLong(maxCents);           //    1 to maxCents
                    Transfer t = new Transfer("t" + me + "-" + n, accounts.get(a), accounts.get(b), cents);
                    if (ledger.apply(t) == Outcome.APPLIED) ok++; else no++;
                }
                applied[me] = ok;                                      // 3. published by join() below
                refused[me] = no;
            }, "stress-" + i);
            w.start();
            workers.add(w);
        }
        ready.await();                                                 // every thread is parked at the line
        go.countDown();                                                // release them together
        for (Thread w : workers) w.join();                             // 4. join: their writes are visible now
        long ok = 0, no = 0;
        for (int i = 0; i < threads; i++) {
            ok += applied[i];
            no += refused[i];
        }
        return new Result(ok, no);
    }
}
