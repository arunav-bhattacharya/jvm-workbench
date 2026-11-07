package workbench.container.l01.demo;

import workbench.container.l01.Component;

import java.io.IOException;
import java.io.OutputStream;
import java.lang.management.ManagementFactory;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;
import java.util.stream.Stream;

/** Scans one package for @Component classes, first in a directory, then in two JAR files. */
public class ScanDemo {
    static final String PACKAGE = "workbench.container.l01.demo.app";
    static final boolean INITIALIZE = false;          // try true: what does Class.forName(name, true, loader) run?

    public static void main(String[] args) throws Exception {
        ClassLoader loader = ScanDemo.class.getClassLoader();
        String path = PACKAGE.replace('.', '/');
        long before = ManagementFactory.getClassLoadingMXBean().getTotalLoadedClassCount();
        for (URL root : Collections.list(loader.getResources(path))) {        // one URL per class path entry
            System.out.println("root: ..." + root.toString().substring(root.toString().indexOf("/build/")));
            List<String> components = new ArrayList<>();
            try (Stream<Path> files = Files.list(Path.of(root.toURI()))) {
                for (Path f : files.sorted().toList()) {
                    String file = f.getFileName().toString();
                    if (!file.endsWith(".class")) continue;
                    Class<?> c = Class.forName(PACKAGE + "." + file.replace(".class", ""), INITIALIZE, loader);
                    if (c.isAnnotationPresent(Component.class)) components.add(c.getSimpleName());
                }
            }
            System.out.println("components: " + components);
        }
        long after = ManagementFactory.getClassLoadingMXBean().getTotalLoadedClassCount();
        System.out.println("classes loaded during the scan: " + (after - before));

        // The same package packed into a JAR twice: with directory entries, and with files only.
        Path classes = Path.of(ScanDemo.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        Path dir = Files.createDirectories(classes.getParent().getParent().getParent().resolve("cap4"));   // container/build/cap4
        for (boolean withDirectories : new boolean[] {true, false}) {
            Path jar = pack(classes, path, dir.resolve(withDirectories ? "app-with-dirs.jar" : "app-files-only.jar"), withDirectories);
            try (URLClassLoader jarLoader = new URLClassLoader(new URL[] {jar.toUri().toURL()}, null)) {
                List<URL> roots = Collections.list(jarLoader.getResources(path));
                System.out.printf("%-18s getResources found %d root(s) %s%n", jar.getFileName(), roots.size(),
                        roots.isEmpty() ? "" : roots.get(0).getProtocol() + ":...!/" + path);
            }
        }
    }

    static Path pack(Path classes, String path, Path jar, boolean withDirectories) throws IOException {
        try (OutputStream file = Files.newOutputStream(jar); JarOutputStream out = new JarOutputStream(file)) {
            if (withDirectories) {                       // "workbench/", "workbench/container/", ... as entries of their own
                String prefix = "";
                for (String part : path.split("/")) {
                    prefix += part + "/";
                    out.putNextEntry(new JarEntry(prefix));
                    out.closeEntry();
                }
            }
            try (Stream<Path> files = Files.list(classes.resolve(path))) {
                for (Path f : files.sorted().toList()) {
                    out.putNextEntry(new JarEntry(path + "/" + f.getFileName()));
                    out.write(Files.readAllBytes(f));
                    out.closeEntry();
                }
            }
        }
        return jar;
    }
}
