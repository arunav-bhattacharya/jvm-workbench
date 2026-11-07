package workbench.startup.l01.demo;

import java.nio.file.Path;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

/**
 * Starts a second JVM with -Xlog:class+load, runs a little start-up work in it, and counts
 * where each loaded class came from. Extra arguments are passed to that JVM as flags.
 */
public class ClassSourcesDemo {
    public static void main(String[] args) throws Exception {
        if (args.length > 0 && args[0].equals("--work")) {
            work();
            return;
        }
        List<String> cmd = new ArrayList<>();
        cmd.add(Path.of(System.getProperty("java.home"), "bin", "java").toString());
        cmd.addAll(List.of(args));                       // e.g. -Xshare:off
        cmd.addAll(List.of("-Xlog:class+load", "-cp", System.getProperty("java.class.path"),
                ClassSourcesDemo.class.getName(), "--work"));
        Process child = new ProcessBuilder(cmd).redirectErrorStream(true).start();
        Map<String, Integer> bySource = new TreeMap<>();
        try (var lines = child.inputReader().lines()) {
            lines.filter(l -> l.contains(" source: "))
                 .forEach(l -> bySource.merge(bucket(l), 1, Integer::sum));
        }
        child.waitFor();
        int total = bySource.values().stream().mapToInt(Integer::intValue).sum();
        System.out.printf("JDK %s, flags %s: %,d classes loaded%n", Runtime.version(), List.of(args), total);
        bySource.forEach((source, n) -> System.out.printf("%7d  %s%n", n, source));
    }

    /** Groups the "source:" field of a class+load line into a few buckets. */
    static String bucket(String line) {
        String source = line.substring(line.indexOf(" source: ") + 9);
        if (source.equals("shared objects file")) return "shared objects file (the CDS archive)";
        if (source.startsWith("jrt:/")) return "jrt:/ (the JDK's modules file, parsed now)";
        if (source.startsWith("file:")) return "file: (your classes and JARs)";
        return "other (hidden classes: lambdas, method handles)";
    }

    /** A small taste of what services do at start-up: config, regex, dates, streams, lambdas. */
    static void work() {
        Map<String, String> config = new TreeMap<>();
        Pattern line = Pattern.compile("(\\w+(?:\\.\\w+)*)\\s*=\\s*(.*)");
        for (String l : List.of("issuer.url = https://issuer.example", "pool.size = 20", "timeout.ms = 120")) {
            var m = line.matcher(l);
            if (m.matches()) config.put(m.group(1), m.group(2));
        }
        String today = LocalDate.of(2026, 1, 15).format(DateTimeFormatter.ISO_LOCAL_DATE);
        String summary = config.entrySet().stream()
                .map(e -> String.format("%s=%s", e.getKey(), e.getValue()))
                .collect(Collectors.joining(", "));
        if (summary.isEmpty() || today.isEmpty()) throw new AssertionError();
    }
}
