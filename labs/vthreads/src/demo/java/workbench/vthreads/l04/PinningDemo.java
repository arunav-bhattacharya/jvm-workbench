package workbench.vthreads.l04;

import jdk.jfr.Recording;
import jdk.jfr.consumer.RecordedEvent;
import jdk.jfr.consumer.RecordingFile;

import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.locks.ReentrantLock;

/**
 * One carrier thread, a ticker virtual thread that wants to tick every 50 ms, and three virtual
 * threads that each block for 100 ms in a different way. A pinned virtual thread blocks the only
 * carrier, so the ticker misses its ticks. JFR counts the pins.
 *
 * <p>Args: sync, lock or init to run one scenario (default: all three).
 */
public class PinningDemo {
    static final Object MONITOR = new Object();
    static final ReentrantLock LOCK = new ReentrantLock();

    // a class whose static initializer blocks, like one that loads config over the network
    static class SlowRatesTable {
        static final boolean READY;
        static {
            sleep(200);
            READY = true;
        }
    }

    public static void main(String[] args) throws Exception {
        System.setProperty("jdk.virtualThreadScheduler.parallelism", "1");   // one carrier makes pins easy to see
        System.out.println("JDK " + Runtime.version() + ", 1 carrier thread");
        String only = args.length > 0 ? args[0] : "all";
        if (only.equals("all") || only.equals("sync"))
            run("synchronized + sleep", () -> { synchronized (MONITOR) { sleep(100); } });
        if (only.equals("all") || only.equals("lock"))
            run("ReentrantLock + sleep", () -> { LOCK.lock(); try { sleep(100); } finally { LOCK.unlock(); } });
        if (only.equals("all") || only.equals("init"))
            run("class init that sleeps", () -> { boolean ready = SlowRatesTable.READY; });
    }

    static void run(String label, Runnable blocker) throws Exception {
        Path file = Files.createTempFile("pinning", ".jfr");
        try (Recording rec = new Recording()) {
            rec.enable("jdk.VirtualThreadPinned").withThreshold(Duration.ofMillis(20));
            rec.start();

            List<Long> ticks = new ArrayList<>();
            Thread ticker = Thread.ofVirtual().start(() -> {
                for (int i = 0; i < 8; i++) {
                    ticks.add(System.nanoTime());
                    sleep(50);
                }
            });
            sleep(10);
            List<Thread> workers = new ArrayList<>();
            for (int i = 0; i < 3; i++) workers.add(Thread.ofVirtual().start(blocker));
            for (Thread w : workers) w.join();
            ticker.join();

            rec.stop();
            rec.dump(file);
            long maxGap = 0;
            for (int i = 1; i < ticks.size(); i++) maxGap = Math.max(maxGap, (ticks.get(i) - ticks.get(i - 1)) / 1_000_000);
            List<RecordedEvent> pins = RecordingFile.readAllEvents(file).stream()
                    .filter(e -> e.getEventType().getName().equals("jdk.VirtualThreadPinned"))   // other recordings may add events
                    .toList();
            System.out.printf("%-24s longest gap between ticks: %3d ms   pinned events: %d%n", label, maxGap, pins.size());
            if (!pins.isEmpty() && pins.get(0).hasField("pinnedReason")) {     // the reason field exists from JDK 24
                System.out.println("    reason: " + pins.get(0).getString("pinnedReason"));
            }
        } finally {
            Files.deleteIfExists(file);
        }
    }

    static void sleep(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
