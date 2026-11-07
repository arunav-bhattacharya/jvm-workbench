package workbench.memory.l05;

import com.sun.management.OperatingSystemMXBean;
import workbench.memory.Jvm;
import workbench.memory.l04.ServiceLoad;

import java.lang.management.ManagementFactory;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/** The same second of service load in a 512 MB heap under each collector, each in its own child JVM. */
public class CollectorCompareDemo {
    static final Pattern PAUSE = Pattern.compile("Pause .*?([\\d.]+)ms$");

    public static void main(String[] args) {
        if (args.length > 0) {                                        // child: do the work, report work and CPU
            int rounds = ServiceLoad.run(1, 0.30);
            var os = (OperatingSystemMXBean) ManagementFactory.getOperatingSystemMXBean();
            System.out.println("RESULT " + rounds + " " + os.getProcessCpuTime() / 1_000_000);
            return;
        }
        boolean oldZgc = Runtime.version().feature() < 23;
        List<List<String>> collectors = List.of(
                List.of("-XX:+UseSerialGC"), List.of("-XX:+UseParallelGC"), List.of("-XX:+UseG1GC"),
                oldZgc ? List.of("-XX:+UseZGC", "-XX:+ZGenerational") : List.of("-XX:+UseZGC"),
                List.of("-XX:+UseShenandoahGC"));
        System.out.printf("%-20s %7s %10s %12s %8s %8s%n", "collector", "pauses", "longest", "all pauses", "rounds", "CPU ms");
        for (List<String> gc : collectors) {
            List<String> flags = new ArrayList<>(gc);
            flags.addAll(List.of("-Xmx512m", "-Xlog:gc,gc+phases"));
            List<String> log = Jvm.lines(flags, CollectorCompareDemo.class.getName(), "load");
            String name = gc.get(0).replace("-XX:+", "");               // "-XX:+UseG1GC" -> "UseG1GC"
            String result = log.stream().filter(l -> l.startsWith("RESULT ")).findFirst().orElse(null);
            if (result == null) { System.out.printf("%-20s not in this JDK build%n", name); continue; }
            int pauses = 0;
            double longest = 0, total = 0;
            for (String line : log) {
                Matcher m = PAUSE.matcher(line);
                if (m.find()) { pauses++; double ms = Double.parseDouble(m.group(1)); total += ms; longest = Math.max(longest, ms); }
            }
            String[] r = result.split(" ");
            System.out.printf("%-20s %7d %8.2fms %10.1fms %8s %8s%n", name, pauses, longest, total, r[1], r[2]);
        }
    }
}
