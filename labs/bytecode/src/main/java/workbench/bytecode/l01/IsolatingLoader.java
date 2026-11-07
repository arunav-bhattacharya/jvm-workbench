package workbench.bytecode.l01;

/**
 * A child-first class loader for plugins. Classes whose binary name starts with
 * {@code prefix} are defined by THIS loader from the bytes the parent can see.
 * Everything else (JDK classes, the host application) is delegated to the parent
 * as usual.
 *
 * <p>So two {@code IsolatingLoader}s over the same parent each get their own copy of a
 * plugin class: two {@code Class} objects, two sets of statics.
 */
public class IsolatingLoader extends ClassLoader {
    private final String prefix;

    public IsolatingLoader(String name, String prefix, ClassLoader parent) {
        super(name, parent);
        this.prefix = prefix;
    }

    /**
     * Child-first for names that start with {@code prefix}, parent-first for the rest.
     * Take {@code getClassLoadingLock(name)}, return a class this loader already defined
     * ({@code findLoadedClass}), and only then define a new one.
     */
    @Override
    protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
        throw new UnsupportedOperationException("TODO: child-first for the prefix, parent-first otherwise");
    }

    /**
     * Read {@code name}'s class file through the parent ({@code a/b/C.class}) and define it here.
     * Throw {@link ClassNotFoundException} if the parent has no such resource.
     */
    @Override
    protected Class<?> findClass(String name) throws ClassNotFoundException {
        throw new UnsupportedOperationException("TODO: read the bytes and call defineClass");
    }
}
