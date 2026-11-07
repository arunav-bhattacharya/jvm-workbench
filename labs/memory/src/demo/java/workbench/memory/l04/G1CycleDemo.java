package workbench.memory.l04;

import workbench.memory.Jvm;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Runs the service load for 3 seconds in a child JVM with a tight 256 MB G1 heap, then counts each
 * kind of GC event and prints the first line of each kind.
 */
public class G1CycleDemo {
    // "GC(12) Pause Young (Mixed) (G1 Evacuation Pause) ..." -> "Pause Young (Mixed)"
    static final Pattern KIND = Pattern.compile("GC\\(\\d+\\) ((?:Pause \\w+(?: \\((?:Normal|Concurrent Start|Prepare Mixed|Mixed)\\))?)|Concurrent \\w+ Cycle)");

    public static void main(String[] args) {
        if (args.length > 0) {
            ServiceLoad.run(3, 0.60);
            return;
        }
        List<String> log = Jvm.lines(List.of("-XX:+UseG1GC", "-Xmx256m", "-Xlog:gc"), G1CycleDemo.class.getName(), "load");
        Map<String, Integer> counts = new TreeMap<>();
        Map<String, String> firstLine = new LinkedHashMap<>();         // in the order they first happened
        int evacuationFailures = 0;
        for (String line : log) {
            Matcher m = KIND.matcher(line);
            if (!m.find() || line.endsWith("Cycle")) continue;     // skip the "cycle started" half of a pair
            counts.merge(m.group(1), 1, Integer::sum);
            firstLine.putIfAbsent(m.group(1), line);
            if (line.contains("(Evacuation Failure)")) evacuationFailures++;
        }
        counts.forEach((kind, n) -> System.out.printf("%4d x %s%n", n, kind));
        System.out.println(evacuationFailures + " pauses had an evacuation failure");
        System.out.println();
        firstLine.values().forEach(System.out::println);
    }
}
