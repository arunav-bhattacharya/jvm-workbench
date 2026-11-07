package workbench.bytecode.l01;

import java.io.IOException;
import java.io.InputStream;

public class IsolatingLoader extends ClassLoader {
    private final String prefix;

    public IsolatingLoader(String name, String prefix, ClassLoader parent) {
        super(name, parent);
        this.prefix = prefix;
    }

    @Override
    protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
        // the same lock the default loadClass takes, so two threads can't define the class twice
        synchronized (getClassLoadingLock(name)) {
            // 1. did this loader define it already? defining it again would throw LinkageError
            Class<?> c = findLoadedClass(name);
            // 2. plugin classes: child-first, define our own copy
            if (c == null && name.startsWith(prefix)) {
                c = findClass(name);
            }
            // 3. everything else: the normal parent-first delegation
            if (c == null) {
                return super.loadClass(name, resolve);
            }
            if (resolve) resolveClass(c);
            return c;
        }
    }

    @Override
    protected Class<?> findClass(String name) throws ClassNotFoundException {
        String path = name.replace('.', '/') + ".class";
        try (InputStream in = getParent().getResourceAsStream(path)) {
            if (in == null) throw new ClassNotFoundException(name);
            byte[] bytes = in.readAllBytes();
            // the class's defining loader is `this`: that is what makes it a different class
            return defineClass(name, bytes, 0, bytes.length);
        } catch (IOException e) {
            throw new ClassNotFoundException(name, e);
        }
    }
}
