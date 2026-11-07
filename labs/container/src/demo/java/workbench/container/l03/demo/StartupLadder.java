package workbench.container.l03.demo;

import workbench.container.l03.Container;
import workbench.container.l03.Interception;
import workbench.container.l03.RegistryGenerator;
import workbench.container.l03.demo.app.DemoApp;

import javax.tools.ToolProvider;
import java.io.IOException;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;
import java.util.stream.Collectors;
import java.util.stream.Stream;

/**
 * Starts the demo app in fresh JVMs: wired by the reflective container, then by a registry generated
 * "at build time" (here, at the start of this demo), each with and without a dynamic AppCDS archive.
 * Class counts come from -Xlog:class+load and barely change between runs; times change a lot.
 */
public class StartupLadder {
    public static void main(String[] args) throws Exception {
        if (args.length > 0 && args[0].equals("--reflective")) {          // the child JVM's entry point
            long t0 = System.nanoTime();
            String result = DemoApp.run(new Container(DemoApp.COMPONENTS));
            System.out.println(String.format("ready: %s in %.0f ms", result, (System.nanoTime() - t0) / 1e6));
            return;
        }
        Path demo = location(StartupLadder.class);                       // build/classes/java/demo
        Path out = Files.createDirectories(demo.getParent().getParent().getParent().resolve("cap4"));   // container/build/cap4
        Path jar = buildApp(demo, out);
        List<String> classPath = new ArrayList<>(List.of(jar.toString()));
        for (String entry : System.getProperty("java.class.path").split(java.io.File.pathSeparator)) {
            String name = Path.of(entry).getFileName().toString();
            if (name.startsWith("byte-buddy-") || name.startsWith("kotlin-stdlib-")) classPath.add(entry);
        }
        String cp = String.join(java.io.File.pathSeparator, classPath);
        Files.writeString(out.resolve("classpath.txt"), cp);             // for the AppCDS and AOT cache commands
        System.out.printf("JDK %s, app and class path in %s%n", Runtime.version(), out);
        System.out.printf("%-26s %7s %9s %9s %9s %8s%n", "setup", "loaded", "archived", "run-time", "ready ms", "wall ms");
        String reflective = StartupLadder.class.getName();
        String generated = "workbench.container.l03.demo.gen.GeneratedStart";
        row("reflective + Byte Buddy", List.of(), cp, reflective, "--reflective");
        row("generated registry", List.of(), cp, generated);
        for (String[] setup : new String[][] {{"reflective", reflective, "--reflective"}, {"generated", generated, ""}}) {
            Path jsa = out.resolve(setup[0] + ".jsa");                    // training run: the archive is written at exit
            Files.deleteIfExists(jsa);
            run(List.of("-XX:ArchiveClassesAtExit=" + jsa), cp, setup[1], setup[2]);
            row(setup[0] + ", AppCDS", List.of("-XX:SharedArchiveFile=" + jsa), cp, setup[1], setup[2]);
        }
    }

    /** One logged run for the class counts, then one quiet run for the times. */
    static void row(String name, List<String> flags, String cp, String main, String... args) throws Exception {
        List<String> logged = new ArrayList<>(flags);
        logged.add("-Xlog:class+load");
        List<String> lines = run(logged, cp, main, args);
        List<String> sources = lines.stream().filter(l -> l.contains(" source: "))
                .map(l -> l.substring(l.indexOf(" source: ") + 9)).toList();
        long archived = sources.stream().filter(s -> s.startsWith("shared objects file")).count();   // "(top)": AppCDS
        long proxies = sources.stream().filter(s -> s.equals("__dynamic_proxy__")).count();
        long fromBytes = sources.stream().filter(s -> s.equals("__JVM_DefineClass__")).count();
        long hidden = sources.stream().filter(s -> !s.startsWith("jrt:") && !s.startsWith("file:")
                && !s.startsWith("shared") && !s.startsWith("__dynamic") && !s.equals("__JVM_DefineClass__")).count();
        long byteBuddyJar = sources.stream().filter(s -> s.contains("byte-buddy-")).count();
        long t0 = System.nanoTime();
        String ready = run(flags, cp, main, args).stream().filter(l -> l.startsWith("ready: ")).findFirst().orElseThrow();
        long wall = (System.nanoTime() - t0) / 1_000_000;
        System.out.printf("%-26s %7d %9d %9d %9s %8d%n", name, sources.size(), archived, proxies + fromBytes + hidden,
                ready.replaceAll(".* in (\\S+) ms", "$1"), wall);
        System.out.printf("    parsed from byte-buddy.jar %d, JDK proxies %d, defined from bytes %d, hidden %d%n",
                byteBuddyJar, proxies, fromBytes, hidden);
    }

    static List<String> run(List<String> flags, String cp, String main, String... args) throws Exception {
        List<String> cmd = new ArrayList<>();
        cmd.add(Path.of(System.getProperty("java.home"), "bin", "java").toString());
        cmd.addAll(flags);
        cmd.addAll(List.of("-cp", cp, main));
        Arrays.stream(args).filter(a -> !a.isEmpty()).forEach(cmd::add);
        Process p = new ProcessBuilder(cmd).redirectErrorStream(true).start();
        List<String> output = p.inputReader().lines().toList();
        if (p.waitFor() != 0) throw new IllegalStateException("child failed: " + cmd + "\n" + String.join("\n", output));
        return output;
    }

    /** The "build": generate the registry, compile it with javac, and pack everything into one JAR (CDS wants JARs). */
    static Path buildApp(Path demo, Path out) throws Exception {
        Path src = Files.createDirectories(out.resolve("gen-src/workbench/container/l03/demo/gen"));
        Files.writeString(src.resolve("AppRegistry.java"),
                RegistryGenerator.generate("workbench.container.l03.demo.gen", "AppRegistry", DemoApp.COMPONENTS));
        Files.writeString(src.resolve("GeneratedStart.java"), """
                package workbench.container.l03.demo.gen;

                public final class GeneratedStart {
                    public static void main(String[] args) {
                        long t0 = System.nanoTime();
                        String result = workbench.container.l03.demo.app.DemoApp.run(new AppRegistry());
                        System.out.println(String.format("ready: %s in %.0f ms", result, (System.nanoTime() - t0) / 1e6));
                    }
                }
                """);
        Path genClasses = Files.createDirectories(out.resolve("gen-classes"));
        int status = ToolProvider.getSystemJavaCompiler().run(null, null, null, "--release", "21", "-proc:none", "-nowarn",
                "-cp", System.getProperty("java.class.path"), "-d", genClasses.toString(),
                src.resolve("AppRegistry.java").toString(), src.resolve("GeneratedStart.java").toString());
        if (status != 0) throw new IllegalStateException("javac failed on the generated registry");
        Path jar = out.resolve("app.jar");
        try (OutputStream file = Files.newOutputStream(jar); JarOutputStream zip = new JarOutputStream(file)) {
            add(zip, demo, "workbench/container/l03/demo");                       // the demo app and this class
            add(zip, location(Container.class), "workbench/container/l03");        // the container, Java half
            add(zip, location(Interception.class), "workbench/container/l03");     // the container, Kotlin half
            add(zip, genClasses, "workbench/container/l03/demo/gen");              // what the generator wrote
        }
        return jar;
    }

    static void add(JarOutputStream zip, Path root, String pkg) throws IOException {
        try (Stream<Path> files = Files.walk(root.resolve(pkg))) {
            for (Path f : files.filter(f -> f.toString().endsWith(".class")).sorted().collect(Collectors.toList())) {
                String name = root.relativize(f).toString().replace('\\', '/');
                if (pkg.equals("workbench/container/l03") && name.substring(pkg.length() + 1).contains("/")) continue;   // no subpackages
                zip.putNextEntry(new JarEntry(name));
                zip.write(Files.readAllBytes(f));
                zip.closeEntry();
            }
        }
    }

    static Path location(Class<?> c) throws Exception {
        return Path.of(c.getProtectionDomain().getCodeSource().getLocation().toURI());
    }
}
