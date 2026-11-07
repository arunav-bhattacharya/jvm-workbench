package workbench.startup.l01;

import java.io.IOException;
import java.io.InputStream;
import java.lang.reflect.InvocationTargetException;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

/**
 * A class loader that defines the lab's classes itself, so every test gets a class that has
 * never been initialized. (A class is initialized once per loader, so a test that reused the
 * normal loader would see whatever an earlier test already triggered.)
 *
 * <p>It is child-first for {@code workbench.startup.l01.*} and parent-first for everything
 * else. {@link InitLog} is shared with the parent on purpose, so the test can read it.
 * Lesson 2's lab asks you to write a loader like this yourself.
 */
final class FreshLoader extends ClassLoader {
    private static final String PACKAGE = "workbench.startup.l01.";
    private final List<String> defined = new CopyOnWriteArrayList<>();

    FreshLoader() {
        super("fresh-l01", FreshLoader.class.getClassLoader());
    }

    @Override
    protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
        if (!name.startsWith(PACKAGE) || name.equals(InitLog.class.getName())) {
            return super.loadClass(name, resolve);
        }
        synchronized (getClassLoadingLock(name)) {
            Class<?> c = findLoadedClass(name);
            if (c == null) {
                try (InputStream in = getParent().getResourceAsStream(name.replace('.', '/') + ".class")) {
                    if (in == null) {
                        throw new ClassNotFoundException(name);
                    }
                    byte[] bytes = in.readAllBytes();
                    c = defineClass(name, bytes, 0, bytes.length);
                    defined.add(name);
                } catch (IOException e) {
                    throw new ClassNotFoundException(name, e);
                }
            }
            if (resolve) {
                resolveClass(c);
            }
            return c;
        }
    }

    /** Names of the lab classes this loader has defined, in the order it defined them. */
    List<String> defined() {
        return List.copyOf(defined);
    }

    /** Calls a public static method that takes only String arguments, on this loader's copy of the class. */
    Object call(String className, String method, String... args) throws Exception {
        Class<?> c = Class.forName(className, false, this);
        Class<?>[] types = new Class<?>[args.length];
        java.util.Arrays.fill(types, String.class);
        try {
            return c.getMethod(method, types).invoke(null, (Object[]) args);
        } catch (InvocationTargetException e) {
            if (e.getCause() instanceof Exception cause) {
                throw cause;
            }
            throw e;
        }
    }
}
