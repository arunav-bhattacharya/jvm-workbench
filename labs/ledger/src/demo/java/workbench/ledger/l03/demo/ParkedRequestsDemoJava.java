package workbench.ledger.l03.demo;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.Semaphore;
import java.util.concurrent.ThreadFactory;

/**
 * 10,000 requests, one named virtual thread each, all stuck behind a fraud service that hangs.
 * Take a JSON thread dump while they are parked. Arg: seconds to stay parked (default 3).
 */
public class ParkedRequestsDemoJava {
    static final Semaphore fraudPermits = new Semaphore(20);       // the fraud bulkhead: 20 calls at once
    static final CountDownLatch fraudDown = new CountDownLatch(1); // the fraud service hangs until this opens

    static String handle(int id) throws InterruptedException {
        fraudPermits.acquire();                                    // 9,980 requests park here...
        try {
            fraudDown.await();                                     // ...and 20 park here, inside the "fraud call"
            return "request " + id + ": ok";
        } finally {
            fraudPermits.release();
        }
    }

    public static void main(String[] args) throws Exception {
        int seconds = args.length > 0 ? Integer.parseInt(args[0]) : 3;
        ThreadFactory named = Thread.ofVirtual().name("request-", 0).factory();   // request-0, request-1, ...
        long t0 = System.nanoTime();
        try (ExecutorService perRequest = Executors.newThreadPerTaskExecutor(named)) {
            List<Future<String>> replies = new ArrayList<>();
            for (int i = 0; i < 10_000; i++) {
                int id = i;
                replies.add(perRequest.submit(() -> handle(id)));
            }
            long pid = ProcessHandle.current().pid();
            System.out.printf("pid %d: 10,000 requests parked for %d s. In another terminal:%n", pid, seconds);
            System.out.printf("  jcmd %d Thread.dump_to_file -format=json /tmp/requests.json%n", pid);
            Thread.sleep(seconds * 1_000L);
            fraudDown.countDown();                                 // the fraud service comes back
            for (Future<String> f : replies) f.get();
        }
        System.out.printf("all 10,000 answered after %d ms%n", (System.nanoTime() - t0) / 1_000_000);
    }
}
