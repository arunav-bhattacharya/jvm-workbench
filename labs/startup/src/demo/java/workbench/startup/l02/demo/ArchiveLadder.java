package workbench.startup.l02.demo;

import java.io.IOException;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;
import java.util.function.Predicate;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;
import java.util.regex.Pattern;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * Packs this demo package into build/boot02/app.jar, then starts it under each class-sharing
 * setup: no sharing, the default CDS archive, a dynamic AppCDS archive, and on JDK 25+ the
 * AOT cache. For each it prints classes loaded, classes from an archive, and the median wall
 * time of 3 runs. Timings are noisy; the class counts are the part to trust.
 */
public class ArchiveLadder {
    public static void main(String[] args) throws Exception {
        if (args.length > 0 && args[0].equals("--work")) {
            Work.run();
            return;
        }
        Path classes = Path.of(ArchiveLadder.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        Path dir = classes.getParent().getParent().getParent().resolve("boot02");   // startup/build/boot02
        Files.createDirectories(dir);
        Path jar = packJar(classes, dir.resolve("app.jar"));                        // CDS wants JARs, not directories
        List<String> app = List.of("-cp", jar.toString(), ArchiveLadder.class.getName(), "--work");
        System.out.printf("JDK %s, app %s%n", Runtime.version(), jar);
        System.out.printf("%-20s %8s %13s %10s%n", "setup", "loaded", "from archive", "wall ms");

        row("no sharing", List.of("-Xshare:off"), app);
        row("default CDS", List.of(), app);

        Path jsa = dir.resolve("app.jsa");                     // 1. training run: archive written at exit
        Files.deleteIfExists(jsa);
        run(List.of("-XX:ArchiveClassesAtExit=" + jsa), app);
        row("AppCDS (dynamic)", List.of("-XX:SharedArchiveFile=" + jsa), app);

        if (Runtime.version().feature() >= 25) {
            Path aot = dir.resolve("app.aot");                 // 2. JEP 514: train and assemble in one command
            Files.deleteIfExists(aot);
            run(List.of("-XX:AOTCacheOutput=" + aot), app);
            row("AOT cache", List.of("-XX:AOTCache=" + aot), app);
            System.out.printf("archive sizes: app.jsa %,d bytes, app.aot %,d bytes%n", Files.size(jsa), Files.size(aot));
        } else {
            System.out.printf("archive size: app.jsa %,d bytes. Run on JDK 25+ to add the AOT cache row.%n", Files.size(jsa));
        }
    }

    /** One line of the table: one logged run for the class counts, three quiet runs for the time. */
    static void row(String name, List<String> flags, List<String> app) throws Exception {
        List<String> logged = new ArrayList<>(flags);
        logged.add("-Xlog:class+load");
        List<String> lines = run(logged, app);
        long loaded = lines.stream().filter(l -> l.contains(" source: ")).count();
        long shared = lines.stream().filter(l -> l.endsWith("source: shared objects file")).count();
        long[] ms = new long[3];
        for (int i = 0; i < ms.length; i++) {
            long t0 = System.nanoTime();
            run(flags, app);
            ms[i] = (System.nanoTime() - t0) / 1_000_000;
        }
        java.util.Arrays.sort(ms);
        System.out.printf("%-20s %8d %13d %10d%n", name, loaded, shared, ms[1]);
    }

    /** Runs a child JVM with these flags and returns its output lines. */
    static List<String> run(List<String> flags, List<String> app) throws Exception {
        List<String> cmd = new ArrayList<>();
        cmd.add(Path.of(System.getProperty("java.home"), "bin", "java").toString());
        cmd.addAll(flags);
        cmd.addAll(app);
        Process p = new ProcessBuilder(cmd).redirectErrorStream(true).start();
        List<String> out = p.inputReader().lines().toList();
        if (p.waitFor() != 0) throw new IllegalStateException("child failed: " + cmd + "\n" + String.join("\n", out));
        return out;
    }

    /** Puts every class file of this package into a JAR. */
    static Path packJar(Path classes, Path jar) throws IOException {
        Path pkg = classes.resolve("workbench/startup/l02/demo");
        try (OutputStream file = Files.newOutputStream(jar);
             JarOutputStream out = new JarOutputStream(file);
             Stream<Path> files = Files.list(pkg)) {
            for (Path f : files.filter(f -> f.toString().endsWith(".class")).sorted().toList()) {
                out.putNextEntry(new JarEntry(classes.relativize(f).toString().replace('\\', '/')));
                out.write(Files.readAllBytes(f));
                out.closeEntry();
            }
        }
        return jar;
    }

    /** The "service" being started: a few classes, lambdas, a stream, regex, java.time and formatting. */
    static final class Work {
        record Payment(String id, long amountMinor, String currency) { }

        enum Status { AUTHORIZED, DECLINED }

        static void run() {
            Pattern line = Pattern.compile("(\\w+);(\\d+);([A-Z]{3})");
            List<Payment> payments = Stream.of("p1;1250;EUR", "p2;990;EUR", "p3;150000;USD", "p4;20;GBP")
                    .map(line::matcher)
                    .filter(m -> m.matches())
                    .map(m -> new Payment(m.group(1), Long.parseLong(m.group(2)), m.group(3)))
                    .toList();
            Predicate<Payment> withinLimit = p -> p.amountMinor() <= 100_000;
            Map<Status, List<String>> byStatus = payments.stream().collect(Collectors.groupingBy(
                    p -> withinLimit.test(p) ? Status.AUTHORIZED : Status.DECLINED,
                    TreeMap::new, Collectors.mapping(Payment::id, Collectors.toList())));
            String report = String.format("%s %s", LocalDate.of(2026, 3, 2), byStatus);
            if (report.isEmpty()) throw new AssertionError();
        }
    }
}
