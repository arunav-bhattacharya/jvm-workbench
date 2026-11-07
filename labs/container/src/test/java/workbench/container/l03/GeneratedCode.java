package workbench.container.l03;

import javax.tools.DiagnosticCollector;
import javax.tools.JavaCompiler;
import javax.tools.JavaFileObject;
import javax.tools.StandardJavaFileManager;
import javax.tools.ToolProvider;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

/** The "build step" of these tests: compile generated source with javac, then load it in a fresh class loader. */
final class GeneratedCode {
    private GeneratedCode() {}

    /** Compiles {@code source} (class {@code className}) into {@code dir}/classes and returns that directory. */
    static Path compile(String className, String source, Path dir) {
        try {
            Path file = dir.resolve("src").resolve(className.replace('.', '/') + ".java");
            Files.createDirectories(file.getParent());
            Files.writeString(file, source);
            Path classes = Files.createDirectories(dir.resolve("classes"));
            JavaCompiler javac = ToolProvider.getSystemJavaCompiler();
            DiagnosticCollector<JavaFileObject> diagnostics = new DiagnosticCollector<>();
            try (StandardJavaFileManager files = javac.getStandardFileManager(diagnostics, null, StandardCharsets.UTF_8)) {
                List<String> options = List.of("--release", "21", "-proc:none",
                        "-classpath", System.getProperty("java.class.path"), "-d", classes.toString());
                boolean ok = javac.getTask(null, files, diagnostics, options, null, files.getJavaFileObjects(file)).call();
                if (!ok) {
                    StringBuilder listing = new StringBuilder();
                    String[] lines = source.split("\n", -1);
                    for (int i = 0; i < lines.length; i++) listing.append(String.format("%4d  %s%n", i + 1, lines[i]));
                    throw new AssertionError("the generated source does not compile:\n" + diagnostics.getDiagnostics() + "\n" + listing);
                }
            }
            return classes;
        } catch (IOException e) {
            throw new UncheckedIOException(e);
        }
    }

    /** A new instance of the compiled class, from a new class loader: fresh statics, so fresh singletons. */
    static Registry load(Path classes, String className) {
        try {
            URLClassLoader loader = new URLClassLoader(new URL[] {classes.toUri().toURL()}, GeneratedCode.class.getClassLoader());
            return (Registry) loader.loadClass(className).getConstructor().newInstance();
        } catch (IOException | ReflectiveOperationException e) {
            throw new AssertionError("could not load " + className, e);
        }
    }
}
