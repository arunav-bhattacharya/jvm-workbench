// JDK 22 or later: the Foreign Function and Memory API is final since JDK 22 (JEP 454). Written for JDK 25.
// Not part of the Gradle build, because the labs compile for JDK 21, where this API is a preview. From labs/:
//     java -XX:NativeMemoryTracking=summary memory/jdk25/ArenaDemo.java
//     java -XX:MaxDirectMemorySize=16m memory/jdk25/ArenaDemo.java

import java.lang.foreign.Arena;
import java.lang.foreign.MemorySegment;
import java.lang.foreign.ValueLayout;
import java.lang.management.BufferPoolMXBean;
import java.lang.management.ManagementFactory;
import javax.management.ObjectName;

public class ArenaDemo {
    public static void main(String[] args) throws Exception {
        MemorySegment escaped;
        try (Arena arena = Arena.ofConfined()) {                          // 1. one owner thread, closed by try-with-resources
            MemorySegment block = arena.allocate(32L * 1024 * 1024);       // 2. 32 MiB outside the heap
            for (long i = 0; i < block.byteSize() / Long.BYTES; i++) {
                block.setAtIndex(ValueLayout.JAVA_LONG, i, i * 100);       //    4 million longs, and no objects
            }
            System.out.println("entry 1,000 holds " + block.getAtIndex(ValueLayout.JAVA_LONG, 1_000));
            System.out.println("inside the arena:  " + nativeOther());
            escaped = block;
        }                                                                 // 3. freed here, not by the GC
        System.out.println("after close():     " + nativeOther());
        try {
            escaped.getAtIndex(ValueLayout.JAVA_LONG, 0);                 // 4. use after free is an exception, not a crash
        } catch (IllegalStateException e) {
            System.out.println("reading after close() throws: " + e.getMessage());
        }

        MemorySegment auto = Arena.ofAuto().allocate(32L * 1024 * 1024);  // 5. freed only after the GC finds it unreachable,
        System.out.printf("an automatic arena: %d MiB counted as direct memory%n",   //    so it counts with direct buffers
                directBytes() >> 20);
        System.out.println("segment " + auto.byteSize());
    }

    // Native Memory Tracking's "Other" row, where arena memory shows up (the same as jcmd <pid> VM.native_memory summary)
    static String nativeOther() throws Exception {
        String summary = (String) ManagementFactory.getPlatformMBeanServer().invoke(
                new ObjectName("com.sun.management:type=DiagnosticCommand"), "vmNativeMemory",
                new Object[] {new String[] {"summary", "scale=MB"}}, new String[] {String[].class.getName()});
        if (!summary.contains("Total")) return "(start java with -XX:NativeMemoryTracking=summary to see it)";
        return summary.lines().filter(l -> l.contains(" Other (")).map(l -> l.replaceFirst("^-?\\s*", "")).findFirst()
                .orElse("Other: under 1 MB, so NMT leaves it out");
    }

    // what the JDK counts against -XX:MaxDirectMemorySize: direct ByteBuffers and automatic arenas
    static long directBytes() {
        return ManagementFactory.getPlatformMXBeans(BufferPoolMXBean.class).stream()
                .filter(p -> p.getName().equals("direct"))
                .mapToLong(BufferPoolMXBean::getMemoryUsed).sum();
    }
}
