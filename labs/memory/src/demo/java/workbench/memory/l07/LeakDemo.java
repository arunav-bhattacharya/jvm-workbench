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
 * A thumbnail service whose cache never forgets, run twice in child JVMs: once to print a class
 * histogram, write a heap dump and measure what the cache keeps alive, once with -Xmx64m until it
 * runs out of memory.
 */
public class LeakDemo {
    record CachedThumbnail(String uploadId, long createdAtMillis, String format, byte[] pixels) {}

    static final List<String> FORMATS = List.of("image/jpeg", "image/png");                 // another GC root
    static final Map<String, CachedThumbnail> THUMBNAILS = new ConcurrentHashMap<>();         // never evicted

    static void handle(String uploadId) {
        THUMBNAILS.computeIfAbsent(uploadId, id -> new CachedThumbnail(id, System.currentTimeMillis(), FORMATS.get(0), new byte[2_048]));
    }

    static String histogram() throws Exception {                               // the same as: jcmd <pid> GC.class_histogram
        return (String) ManagementFactory.getPlatformMBeanServer().invoke(
                new ObjectName("com.sun.management:type=DiagnosticCommand"), "gcClassHistogram",
                new Object[] {null}, new String[] {String[].class.getName()});
    }

    static long liveBytes() throws Exception {                                 // the histogram's last line: Total <objects> <bytes>
        String[] total = histogram().strip().lines().reduce((a, b) -> b).orElseThrow().trim().split("\\s+");
        return Long.parseLong(total[2]);
    }

    public static void main(String[] args) throws Exception {
        Path dumps = Files.createDirectories(Path.of("build", "heapdumps"));     // labs/memory/build/heapdumps
        if (args.length == 0) {
            System.out.println("== 20,000 uploads, then a class histogram and a heap dump");
            Jvm.run(List.of("-Xmx256m"), LeakDemo.class.getName(), "histogram");
            Files.deleteIfExists(dumps.resolve("oom.hprof"));
            System.out.println("== -Xmx64m -XX:+HeapDumpOnOutOfMemoryError, uploads until the heap is full");
            Jvm.lines(List.of("-Xmx64m", "-XX:+HeapDumpOnOutOfMemoryError", "-XX:HeapDumpPath=" + dumps.resolve("oom.hprof")),
                    LeakDemo.class.getName(), "forever").stream()
                    .filter(line -> !line.startsWith("\tat ")).forEach(System.out::println);
            return;
        }
        if (args[0].equals("forever")) {
            while (true) handle(UUID.randomUUID().toString());
        }
        for (int i = 0; i < 20_000; i++) handle(UUID.randomUUID().toString());
        histogram().lines().limit(7).forEach(System.out::println);               // the header and the top five classes
        Path dump = dumps.resolve("leak.hprof");
        Files.deleteIfExists(dump);
        ManagementFactory.getPlatformMXBean(HotSpotDiagnosticMXBean.class).dumpHeap(dump.toString(), true);   // live objects only
        System.out.printf("heap dump: %s, %,d bytes%n", dump.toAbsolutePath(), Files.size(dump));
        long withCache = liveBytes();
        THUMBNAILS.clear();                                                      // drop every note the cache holds
        long without = liveBytes();
        System.out.printf("live heap %,d bytes with the cache full, %,d after clear(): it kept %,d bytes alive%n",
                withCache, without, withCache - without);
    }
}
