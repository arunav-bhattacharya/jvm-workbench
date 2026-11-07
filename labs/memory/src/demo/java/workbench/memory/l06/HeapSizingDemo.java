package workbench.memory.l06;

import com.sun.management.HotSpotDiagnosticMXBean;
import workbench.memory.Jvm;

import java.lang.management.ManagementFactory;
import java.util.List;

/**
 * Shows the max heap the JVM picks for a memory limit, with and without -XX:MaxRAMPercentage.
 * -XX:MaxRAM stands in for a container limit here; it is deprecated in JDK 26 and gone in JDK 27.
 */
public class HeapSizingDemo {
    public static void main(String[] args) {
        if (args.length > 0) {
            var hotspot = ManagementFactory.getPlatformMXBean(HotSpotDiagnosticMXBean.class);
            long max = Long.parseLong(hotspot.getVMOption("MaxHeapSize").getValue());
            System.out.printf("max heap %,6d MB%n", max >> 20);
            return;
        }
        if (Runtime.version().feature() >= 27) {
            System.out.println("JDK 27 removed -XX:MaxRAM. Try this inside a container with a memory limit instead.");
            return;
        }
        for (String limit : List.of("1g", "2g", "4g")) {
            for (String percent : List.of("", "-XX:MaxRAMPercentage=75")) {
                List<String> flags = percent.isEmpty() ? List.of("-XX:MaxRAM=" + limit) : List.of("-XX:MaxRAM=" + limit, percent);
                String result = Jvm.lines(flags, HeapSizingDemo.class.getName(), "child").stream()
                        .filter(l -> l.startsWith("max heap")).findFirst().orElse("(no answer)");
                System.out.printf("limit %s %-26s -> %s%n", limit, percent.isEmpty() ? "(defaults: 25%)" : percent, result);
            }
        }
    }
}
