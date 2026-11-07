package workbench.concurrency.l13;

import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.locks.ReentrantLock;

import jdk.jfr.Recording;
import jdk.jfr.consumer.RecordedEvent;
import jdk.jfr.consumer.RecordingFile;

/**
 * Records one second of lock contention with Java Flight Recorder, from inside the program,
 * then reads the recording back and summarizes it. The .jfr file is kept for the jfr tool.
 */
public class JfrContention {
    static final Object ledgerMonitor = new Object();
    static final ReentrantLock batchLock = new ReentrantLock();

    static void busy(long micros) {
        long end = System.nanoTime() + micros * 1_000;
        while (System.nanoTime() < end) Thread.onSpinWait();
    }

    public static void main(String[] args) throws Exception {
        Path file = Files.createTempFile("contention-", ".jfr");
        try (Recording rec = new Recording()) {
            rec.enable("jdk.JavaMonitorEnter").withThreshold(Duration.ofMillis(1));   // waited > 1 ms for a monitor
            rec.enable("jdk.ThreadPark").withThreshold(Duration.ofMillis(1));         // parked > 1 ms (j.u.c locks)
            rec.start();

            long end = System.nanoTime() + 1_000_000_000L;
            Thread[] ts = new Thread[6];
            for (int i = 0; i < ts.length; i++) {
                boolean useMonitor = i % 2 == 0;
                ts[i] = new Thread(() -> {
                    while (System.nanoTime() < end) {
                        if (useMonitor) {
                            synchronized (ledgerMonitor) { busy(3_000); }            // hold it 3 ms
                        } else {
                            batchLock.lock();
                            try { busy(3_000); } finally { batchLock.unlock(); }
                        }
                    }
                }, (useMonitor ? "ledger-" : "batch-") + i);
                ts[i].start();
            }
            for (Thread t : ts) t.join();
            rec.stop();
            rec.dump(file);
        }

        Map<String, long[]> byKind = new TreeMap<>();                  // count, total ms
        for (RecordedEvent e : RecordingFile.readAllEvents(file)) {
            String what = switch (e.getEventType().getName()) {
                case "jdk.JavaMonitorEnter" -> "JavaMonitorEnter on " + e.getClass("monitorClass").getName();
                case "jdk.ThreadPark" -> "ThreadPark on " + (e.getClass("parkedClass") == null ? "?" : e.getClass("parkedClass").getName());
                default -> e.getEventType().getName();
            };
            long[] agg = byKind.computeIfAbsent(what, k -> new long[2]);
            agg[0]++;
            agg[1] += e.getDuration().toMillis();
        }
        byKind.forEach((k, v) -> System.out.printf("%-70s %5d events, %6d ms waiting%n", k, v[0], v[1]));
        System.out.println("recording kept at " + file);
    }
}
