package workbench.memory.l05;

import workbench.memory.Jvm;
import workbench.memory.l04.ServiceLoad;

import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Runs two seconds of service load under generational ZGC in a child JVM. Prints every line of the
 * first minor collection, then compares the real pauses with the collection times.
 */
public class ZgcDemo {
    static final Pattern PAUSE = Pattern.compile("Pause .*?([\\d.]+)ms$");
    static final Pattern CYCLE = Pattern.compile("GC\\((\\d+)\\) (Minor|Major) Collection \\(.*\\) .*->.* ([\\d.]+)s$");

    public static void main(String[] args) {
        if (args.length > 0) {
            ServiceLoad.run(2, 0.30);
            return;
        }
        List<String> flags = new ArrayList<>(List.of("-XX:+UseZGC", "-Xmx1g", "-Xlog:gc,gc+phases"));
        if (Runtime.version().feature() < 23) flags.add("-XX:+ZGenerational");     // generational is the default from 23
        List<String> log = Jvm.lines(flags, ZgcDemo.class.getName(), "load");

        String firstMinor = log.stream().filter(l -> l.contains("Minor Collection")).findFirst()
                .map(l -> l.substring(l.indexOf("GC("), l.indexOf(')', l.indexOf("GC(")) + 1)).orElse("none");
        log.stream().filter(l -> l.contains(firstMinor + " ")).forEach(l -> System.out.println(l.replaceAll("\\s+", " ")));

        int collections = 0, pauses = 0, stalls = 0;
        double longestPause = 0, totalPause = 0, totalCycle = 0;
        for (String line : log) {
            Matcher p = PAUSE.matcher(line), c = CYCLE.matcher(line);
            if (p.find()) { pauses++; double ms = Double.parseDouble(p.group(1)); totalPause += ms; longestPause = Math.max(longestPause, ms); }
            if (c.find()) { collections++; totalCycle += Double.parseDouble(c.group(3)); }
            if (line.contains("Allocation Stall (")) stalls++;
        }
        System.out.printf("%n%d collections took %.3f s in all, running alongside the application%n", collections, totalCycle);
        System.out.printf("%d stop-the-world pauses took %.3f ms in all; the longest was %.3f ms%n", pauses, totalPause, longestPause);
        System.out.println("allocation stalls: " + stalls);
    }
}
