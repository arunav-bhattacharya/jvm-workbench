package workbench.performance.l07;

import jdk.jfr.consumer.RecordedEvent;
import jdk.jfr.consumer.RecordedFrame;
import jdk.jfr.consumer.RecordingFile;

import java.lang.management.GarbageCollectorMXBean;
import java.lang.management.ManagementFactory;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.ToLongFunction;

/**
 * Runs one fee variant (slow, hoisted or noregex) on 4 threads for 3 seconds in a second JVM with
 * -Xmx256m and a JFR recording, prints latency percentiles and GC counts, then reads the recording
 * and prints allocation by source line in this package.  Usage: -Pargs=slow (or hoisted, noregex).
 */
public class FeeInvestigation {
    public static void main(String[] args) throws Exception {
        String mode = args.length > 0 ? args[0] : "slow";
        if (args.length > 1 && args[1].equals("child")) { load(mode); return; }
        Path file = Path.of("build", "fees-" + mode + ".jfr").toAbsolutePath();
        String java = ProcessHandle.current().info().command().orElse("java");
        Process p = new ProcessBuilder(java, "-Xmx256m", "-Xlog:jfr+startup=warning",
                "-XX:StartFlightRecording:filename=" + file + ",settings=profile",
                "-cp", System.getProperty("java.class.path"), FeeInvestigation.class.getName(), mode, "child")
                .inheritIO().start();
        p.waitFor();
        allocationByLine(file);
    }

    // the load: 4 threads, each timing every call into a fixed histogram (no allocation of its own)
    static void load(String mode) throws Exception {
        ToLongFunction<FeeVariants.Payment> fee = switch (mode) {
            case "slow" -> FeeVariants::feeSlow;
            case "hoisted" -> FeeVariants::feeHoisted;
            default -> FeeVariants::feeNoRegex;
        };
        FeeVariants.Payment[] ps = FeeVariants.payments(4_096);
        long end = System.nanoTime() + 3_000_000_000L;
        long[][] hist = new long[4][];
        List<Thread> threads = new ArrayList<>();
        for (int t = 0; t < 4; t++) {
            int id = t;
            Thread th = new Thread(() -> {
                long[] h = new long[20_001];        // 100 ns buckets up to 1 ms, then 100 us buckets up to 1 s
                long sink = 0;
                for (int i = id; System.nanoTime() < end; i++) {
                    long t0 = System.nanoTime();
                    sink += fee.applyAsLong(ps[i & 4095]);
                    long d = System.nanoTime() - t0;
                    h[d < 1_000_000 ? (int) (d / 100) : (int) Math.min(20_000, 10_000 + (d - 1_000_000) / 100_000)]++;
                }
                hist[id] = h;
                if (sink == 42) System.out.println();
            });
            th.start();
            threads.add(th);
        }
        for (Thread th : threads) th.join();
        long[] h = new long[20_001];
        for (long[] x : hist) for (int k = 0; k < h.length; k++) h[k] += x[k];
        long total = 0;
        for (long n : h) total += n;
        long gcs = 0, gcMs = 0;
        for (GarbageCollectorMXBean gc : ManagementFactory.getGarbageCollectorMXBeans()) {
            gcs += gc.getCollectionCount();
            gcMs += gc.getCollectionTime();
        }
        System.out.printf("%s: %,d calls/s  p50 %s  p99 %s  p99.9 %s  p99.99 %s  GCs %d (%d ms)%n", mode, total / 3,
                pct(h, total, 0.5), pct(h, total, 0.99), pct(h, total, 0.999), pct(h, total, 0.9999), gcs, gcMs);
    }

    static String pct(long[] h, long total, double q) {
        long target = (long) Math.ceil(total * q), acc = 0;
        for (int k = 0; k < h.length; k++) {
            acc += h[k];
            if (acc >= target) return k < 10_000 ? "<" + (k + 1) * 100 + "ns" : "<" + ((k - 10_000 + 1) * 100 + 1_000) + "us";
        }
        return "?";
    }

    // what `jfr view allocation-by-site` can't tell you: the line in YOUR code each sample came from
    static void allocationByLine(Path file) throws Exception {
        Map<String, Long> weight = new HashMap<>();
        long total = 0;
        for (RecordedEvent e : RecordingFile.readAllEvents(file)) {
            if (!e.getEventType().getName().equals("jdk.ObjectAllocationSample") || e.getStackTrace() == null) continue;
            for (RecordedFrame f : e.getStackTrace().getFrames()) {
                if (f.getMethod().getType().getName().startsWith("workbench.performance.l07.FeeVariants")) {
                    weight.merge(f.getMethod().getName() + " line " + f.getLineNumber(), e.getLong("weight"), Long::sum);
                    total += e.getLong("weight");
                    break;                          // the first frame in our code is the one to change
                }
            }
        }
        long sum = total;
        System.out.println("allocation by line in FeeVariants.java (from " + file.getFileName() + "):");
        weight.entrySet().stream().sorted(Map.Entry.<String, Long>comparingByValue().reversed()).limit(5)
              .forEach(en -> System.out.printf("  %5.1f%%  %s%n", 100.0 * en.getValue() / sum, en.getKey()));
    }
}
