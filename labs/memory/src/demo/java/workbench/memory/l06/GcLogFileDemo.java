package workbench.memory.l06;

import workbench.memory.Jvm;
import workbench.memory.l04.ServiceLoad;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.stream.Stream;

/**
 * Runs two seconds of service load in a child JVM that writes its GC log the way a production service
 * should: to rotating files, with timestamps. Then it does the three checks you do first on any GC log.
 */
public class GcLogFileDemo {
    public static void main(String[] args) throws IOException {
        if (args.length > 0) {
            ServiceLoad.run(2, 0.55);
            return;
        }
        Path dir = Files.createDirectories(Path.of("build", "gc-logs"));   // labs/memory/build/gc-logs under Gradle
        try (Stream<Path> old = Files.list(dir)) {
            for (Path f : old.toList()) if (f.getFileName().toString().startsWith("gc.log")) Files.delete(f);
        }
        String logging = "-Xlog:gc*:file=" + dir.resolve("gc.log") + ":time,uptime,level,tags:filecount=3,filesize=200k";
        Jvm.lines(List.of("-XX:+UseG1GC", "-Xmx256m", logging), GcLogFileDemo.class.getName(), "load");

        List<String> lines = new ArrayList<>();
        // rotated files (gc.log.0, gc.log.1, ...) hold the older lines; gc.log is the current one
        try (Stream<Path> files = Files.list(dir).sorted(Comparator.comparing((Path f) -> f.toString().endsWith("gc.log")).thenComparing(Path::toString))) {
            for (Path f : files.toList()) {
                System.out.printf("%-12s %,9d bytes%n", f.getFileName(), Files.size(f));
                lines.addAll(Files.readAllLines(f));
            }
        }
        // the three checks: full GCs, evacuation failures, and the heap left after young pauses
        System.out.println("Pause Full lines:          " + lines.stream().filter(l -> l.contains("Pause Full")).count());
        System.out.println("(Evacuation Failure) lines: " + lines.stream().filter(l -> l.contains("(Evacuation Failure)")).count());
        List<String> young = lines.stream().filter(l -> l.contains("[gc ") && l.contains("Pause Young") && l.endsWith("ms")).toList();
        if (!young.isEmpty()) {
            System.out.println("first young pause: " + young.get(0).substring(young.get(0).indexOf("GC(")));
            System.out.println("last young pause:  " + young.get(young.size() - 1).substring(young.get(young.size() - 1).indexOf("GC(")));
        }
        System.out.println("logs are in " + dir.toAbsolutePath());
    }
}
