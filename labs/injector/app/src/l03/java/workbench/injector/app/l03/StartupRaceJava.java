package workbench.injector.app.l03;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.function.ToLongFunction;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * The Java twin of StartupRace: the same cold starts, with WiringProbeJava in each fresh JVM.
 *   ./gradlew :injector:app:demo -Pmain=workbench.injector.app.l03.StartupRaceJava
 */
public class StartupRaceJava {

    record Run(long createUs, long firstUs, long secondUs, long wallMs, long classes, long proxyClasses, long annotationClasses) {}

    public static void main(String[] args) throws Exception {
        int runs = args.length > 0 ? Integer.parseInt(args[0]) : 7;
        Map<String, List<Run>> results = new LinkedHashMap<>();
        for (String way : List.of("generated", "reflection")) results.put(way, new ArrayList<>());
        for (int i = 0; i < runs; i++) {
            for (String way : results.keySet()) results.get(way).add(probe(way));
        }
        System.out.println(runs + " cold starts each, medians (a busy machine: compare the two rows, not the numbers with yours)");
        System.out.printf("%-11s %9s %11s %12s %9s %8s %14s %12s%n",
                "", "create", "first get", "second get", "JVM run", "classes", "proxy classes", "annotations");
        for (var entry : results.entrySet()) {
            List<Run> r = entry.getValue();
            System.out.printf("%-11s %6.2f ms %8.2f ms %9.3f ms %6d ms %8d %14d %12d%n", entry.getKey(),
                    median(r, Run::createUs) / 1000.0, median(r, Run::firstUs) / 1000.0,
                    median(r, Run::secondUs) / 1000.0, median(r, Run::wallMs),
                    median(r, Run::classes), median(r, Run::proxyClasses), median(r, Run::annotationClasses));
        }
        Files.deleteIfExists(Path.of("build/startup-race"));
    }

    static Run probe(String way) throws IOException, InterruptedException {
        Path dir = Files.createDirectories(Path.of("build/startup-race"));
        Path log = dir.resolve(way + "-java.log");
        Files.deleteIfExists(log);
        String java = ProcessHandle.current().info().command().orElse("java");
        ProcessBuilder builder = new ProcessBuilder(java, "-Xlog:class+load:file=" + log,
                "-cp", System.getProperty("java.class.path"), "workbench.injector.app.l03.WiringProbeJava", way)
                .redirectErrorStream(true);
        builder.environment().remove("JAVA_TOOL_OPTIONS");      // keep the child JVM plain
        long started = System.nanoTime();
        Process process = builder.start();
        String output = new String(process.getInputStream().readAllBytes());
        process.waitFor();
        long wallMs = (System.nanoTime() - started) / 1_000_000;
        String line = output.lines().filter(l -> l.startsWith("probe ")).findFirst().orElseThrow();
        List<String> loaded = Files.readAllLines(log).stream().filter(l -> l.contains("[class,load]"))
                .map(l -> l.substring(l.indexOf("[class,load] ") + 13)).toList();
        Files.delete(log);
        return new Run(field(line, "create"), field(line, "first"), field(line, "second"), wallMs, loaded.size(),
                loaded.stream().filter(c -> c.startsWith("jdk.proxy")).count(),
                loaded.stream().filter(c -> c.startsWith("workbench.injector.annotations.")).count());
    }

    static long field(String line, String name) {
        Matcher m = Pattern.compile(name + "=(\\d+)").matcher(line);
        if (!m.find()) throw new IllegalStateException(line);
        return Long.parseLong(m.group(1));
    }

    static long median(List<Run> runs, ToLongFunction<Run> f) {
        return runs.stream().mapToLong(f).sorted().toArray()[runs.size() / 2];
    }
}
