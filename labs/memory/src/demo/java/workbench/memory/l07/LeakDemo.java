package workbench.memory.l07;

import com.sun.management.HotSpotDiagnosticMXBean;
import workbench.memory.Jvm;

import javax.management.ObjectName;
import java.lang.management.ManagementFactory;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/**
 * A service with an unbounded idempotency cache, run twice in child JVMs: once to print a class
 * histogram and write a heap dump, once with -Xmx64m until it runs out of memory.
 */
public class LeakDemo {
    record CachedResponse(String requestId, long amountMinor, byte[] receipt) {}

    static final Map<String, CachedResponse> IDEMPOTENCY_CACHE = new ConcurrentHashMap<>();   // never evicted

    static void handle(String requestId) {
        IDEMPOTENCY_CACHE.computeIfAbsent(requestId, id -> new CachedResponse(id, 1_999, new byte[2_048]));
    }

    public static void main(String[] args) throws Exception {
        Path dumps = Files.createDirectories(Path.of("build", "heapdumps"));     // labs/memory/build/heapdumps
        if (args.length == 0) {
            System.out.println("== 20,000 requests, then a class histogram and a heap dump");
            Jvm.run(List.of("-Xmx256m"), LeakDemo.class.getName(), "histogram");
            Files.deleteIfExists(dumps.resolve("oom.hprof"));
            System.out.println("== -Xmx64m -XX:+HeapDumpOnOutOfMemoryError, requests until the heap is full");
            Jvm.lines(List.of("-Xmx64m", "-XX:+HeapDumpOnOutOfMemoryError", "-XX:HeapDumpPath=" + dumps.resolve("oom.hprof")),
                    LeakDemo.class.getName(), "forever").stream()
                    .filter(line -> !line.startsWith("\tat ")).forEach(System.out::println);
            return;
        }
        if (args[0].equals("forever")) {
            while (true) handle(UUID.randomUUID().toString());
        }
        for (int i = 0; i < 20_000; i++) handle(UUID.randomUUID().toString());
        String histogram = (String) ManagementFactory.getPlatformMBeanServer().invoke(
                new ObjectName("com.sun.management:type=DiagnosticCommand"), "gcClassHistogram",
                new Object[] {null}, new String[] {String[].class.getName()});
        histogram.lines().limit(7).forEach(System.out::println);                 // the header and the top five classes
        Path dump = dumps.resolve("leak.hprof");
        Files.deleteIfExists(dump);
        ManagementFactory.getPlatformMXBean(HotSpotDiagnosticMXBean.class).dumpHeap(dump.toString(), true);   // live objects only
        System.out.printf("heap dump: %s, %,d bytes%n", dump.toAbsolutePath(), Files.size(dump));
    }
}
