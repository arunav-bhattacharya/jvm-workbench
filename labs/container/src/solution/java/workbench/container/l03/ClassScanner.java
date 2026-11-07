package workbench.container.l03;

import java.io.IOException;
import java.net.JarURLConnection;
import java.net.URISyntaxException;
import java.net.URL;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.Enumeration;
import java.util.List;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;
import java.util.stream.Stream;

/**
 * Finds the classes annotated {@link Component} in one package by asking a class loader for the
 * package's directory on every class path entry. Given complete: read it, you don't need to change it.
 */
public final class ClassScanner {
    private ClassScanner() {}

    /** Every {@code @Component} class directly in {@code packageName}, sorted by name. Runs no static initializer. */
    public static List<Class<?>> scan(ClassLoader loader, String packageName) {
        String path = packageName.replace('.', '/');
        List<Class<?>> found = new ArrayList<>();
        try {
            Enumeration<URL> roots = loader.getResources(path);           // one URL per class path entry with this package
            while (roots.hasMoreElements()) {
                for (String name : classNamesIn(roots.nextElement(), path)) {
                    Class<?> c = Class.forName(name, false, loader);     // load and link, but don't run <clinit>
                    if (c.isAnnotationPresent(Component.class)) found.add(c);
                }
            }
        } catch (IOException | URISyntaxException | ClassNotFoundException e) {
            throw new ContainerException("could not scan " + packageName, e);
        }
        found.sort(Comparator.comparing(Class::getName));
        return List.copyOf(found);
    }

    private static List<String> classNamesIn(URL root, String path) throws IOException, URISyntaxException {
        List<String> names = new ArrayList<>();
        switch (root.getProtocol()) {
            case "file" -> {                                              // a directory, such as build/classes/java/main/...
                try (Stream<Path> files = Files.list(Path.of(root.toURI()))) {
                    files.map(f -> f.getFileName().toString())
                            .filter(ClassScanner::isClassFile)
                            .forEach(f -> names.add(path.replace('/', '.') + "." + f.substring(0, f.length() - 6)));
                }
            }
            case "jar" -> {                                               // jar:file:/srv/app.jar!/workbench/...
                JarURLConnection connection = (JarURLConnection) root.openConnection();
                connection.setUseCaches(false);
                try (JarFile jar = connection.getJarFile()) {
                    jar.stream().map(JarEntry::getName)
                            .filter(n -> n.startsWith(path + "/") && n.indexOf('/', path.length() + 1) < 0)
                            .filter(n -> isClassFile(n.substring(path.length() + 1)))
                            .forEach(n -> names.add(n.substring(0, n.length() - 6).replace('/', '.')));
                }
            }
            default -> throw new ContainerException("can't scan " + root);
        }
        return names;
    }

    private static boolean isClassFile(String fileName) {
        return fileName.endsWith(".class") && !fileName.equals("module-info.class") && !fileName.equals("package-info.class");
    }
}
