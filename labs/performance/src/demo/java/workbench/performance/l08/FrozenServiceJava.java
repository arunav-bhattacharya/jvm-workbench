package workbench.performance.l08;

import java.io.IOException;
import java.net.ServerSocket;
import java.net.Socket;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.ReentrantLock;

// A report service that is stuck in five different ways at once, so a thread dump has something to show.
// Run it, then take dumps from a second terminal while it waits.
public class FrozenServiceJava {
    private static final Object catalog = new Object();
    private static final ReentrantLock archiveLock = new ReentrantLock();
    private static volatile long sink;

    public static void main(String[] args) throws Exception {
        long seconds = args.length > 0 ? Long.parseLong(args[0]) : 120;
        // the "document store": the kernel accepts connections into the backlog, but nobody ever answers
        ServerSocket store = new ServerSocket(0);

        // 1. refreshes the catalog while holding its lock, and waits for an answer that never comes
        Thread.ofPlatform().name("catalog-refresh").start(() -> {
            synchronized (catalog) {
                try (Socket s = new Socket("localhost", store.getLocalPort())) {
                    s.getInputStream().read();
                } catch (IOException e) {
                    throw new RuntimeException(e);
                }
            }
        });
        Thread.sleep(200);
        // 2. four report workers that need the same lock
        ExecutorService reports = Executors.newFixedThreadPool(4, Thread.ofPlatform().name("report-worker-", 1).factory());
        for (int i = 0; i < 4; i++) reports.execute(FrozenServiceJava::writeReport);
        // 3. an idle pool with nothing to do
        ExecutorService exports = Executors.newFixedThreadPool(2, Thread.ofPlatform().name("export-worker-", 1).factory());
        for (int i = 0; i < 2; i++) exports.execute(() -> { });
        // 4. a hot loop
        Thread.ofPlatform().name("index-rebuild").start(FrozenServiceJava::rebuildIndex);
        // 5. a ReentrantLock held by a thread that sleeps, and a thread that waits for it
        Thread.ofPlatform().name("archive-writer").start(() -> {
            archiveLock.lock();
            try {
                Thread.sleep(600_000);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            } finally {
                archiveLock.unlock();
            }
        });
        Thread.sleep(100);
        Thread.ofPlatform().name("archive-reader").start(() -> {
            archiveLock.lock();
            archiveLock.unlock();
        });
        // 6. virtual threads: 10,000 waiting for a permit that never comes, 200 asleep
        Semaphore permits = new Semaphore(0);
        for (int i = 0; i < 10_000; i++) Thread.ofVirtual().name("vt-report").start(() -> {
            try { permits.acquire(); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });
        for (int i = 0; i < 200; i++) Thread.ofVirtual().name("vt-poll").start(() -> {
            try { Thread.sleep(600_000); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });

        System.out.println("PID " + ProcessHandle.current().pid() + ": frozen for " + seconds + " s. Take your dumps now.");
        // a daemon timer ends the demo; main returns, so it doesn't show up in the dumps
        Executors.newSingleThreadScheduledExecutor(Thread.ofPlatform().daemon().name("demo-timer").factory())
                .schedule(() -> System.exit(0), seconds, TimeUnit.SECONDS);
    }

    private static void writeReport() {
        synchronized (catalog) { sink++; }
    }

    private static void rebuildIndex() {
        long x = 1;
        while (true) {
            x = x * 6364136223846793005L + 1442695040888963407L;
            if (x == 42L) sink = x;
        }
    }
}
