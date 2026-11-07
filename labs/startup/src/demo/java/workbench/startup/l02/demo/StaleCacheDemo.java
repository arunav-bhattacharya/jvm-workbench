package workbench.startup.l02.demo;

import javax.tools.JavaCompiler;
import javax.tools.ToolProvider;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;

/**
 * Builds hello.jar printing "version ONE", trains a cache on it, rebuilds the JAR to print
 * "version TWO", and runs the new JAR with the old cache. On JDK 25+ the cache is an AOT cache;
 * on older JDKs it is a dynamic CDS archive. Needs a JDK (it compiles Java source).
 */
public class StaleCacheDemo {
    public static void main(String[] args) throws Exception {
        Path classes = Path.of(StaleCacheDemo.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        Path dir = classes.getParent().getParent().getParent().resolve("boot02-stale");
        Files.createDirectories(dir);
        Path jar = dir.resolve("hello.jar");
        boolean aot = Runtime.version().feature() >= 25;
        Path cache = dir.resolve(aot ? "hello.aot" : "hello.jsa");
        Files.deleteIfExists(cache);

        // 1. build version ONE and train a cache on it
        build(dir, jar, "version ONE");
        run(List.of(aot ? "-XX:AOTCacheOutput=" + cache : "-XX:ArchiveClassesAtExit=" + cache), jar);

        // 2. rebuild the JAR, as a new commit would, but keep the old cache
        build(dir, jar, "version TWO, rebuilt");

        // 3. production: new JAR, old cache
        String flag = aot ? "-XX:AOTCache=" + cache : "-XX:SharedArchiveFile=" + cache;
        System.out.printf("JDK %s: java %s -cp hello.jar stale.Hello%n", Runtime.version(), flag.replace(dir + "/", ""));
        for (String line : run(List.of(flag, "-Xlog:class+load"), jar)) {
            if (line.contains("stale.Hello source:") || line.startsWith("version") || line.contains("[warning]")
                    || line.contains("[error")) {
                System.out.println("  " + line.replace("file:" + dir + "/", "file:").replace(dir + "/", ""));
            }
        }
    }

    /** Compiles a one-class program that prints {@code message} and packs it into {@code jar}. */
    static void build(Path dir, Path jar, String message) throws Exception {
        Path src = dir.resolve("src/stale/Hello.java");
        Files.createDirectories(src.getParent());
        Files.writeString(src, "package stale;\npublic class Hello {\n    public static void main(String[] a) {\n"
                + "        System.out.println(\"" + message + "\");\n    }\n}\n");
        Path out = dir.resolve("classes");
        JavaCompiler javac = ToolProvider.getSystemJavaCompiler();
        if (javac == null) throw new IllegalStateException("run this on a JDK, not a JRE");
        if (javac.run(null, null, null, "-d", out.toString(), src.toString()) != 0) throw new IllegalStateException("javac failed");
        Files.deleteIfExists(jar);
        try (OutputStream file = Files.newOutputStream(jar); JarOutputStream j = new JarOutputStream(file)) {
            j.putNextEntry(new JarEntry("stale/Hello.class"));
            j.write(Files.readAllBytes(out.resolve("stale/Hello.class")));
            j.closeEntry();
        }
    }

    static List<String> run(List<String> flags, Path jar) throws Exception {
        List<String> cmd = new ArrayList<>();
        cmd.add(Path.of(System.getProperty("java.home"), "bin", "java").toString());
        cmd.addAll(flags);
        cmd.addAll(List.of("-cp", jar.toString(), "stale.Hello"));
        Process p = new ProcessBuilder(cmd).redirectErrorStream(true).start();
        List<String> out = p.inputReader().lines().toList();
        p.waitFor();
        return out;
    }
}
