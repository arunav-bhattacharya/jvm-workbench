package workbench.bytecode.l01;

import java.io.IOException;
import java.io.InputStream;

/** The same class file defined by two loaders: two classes, two sets of statics. */
public class TwoLoadersDemo {
    public static class Counter {
        public static int hits;
        public int hit() { return ++hits; }
    }

    /** Defines Counter itself (child-first); asks the parent for everything else. */
    static class ChildFirst extends ClassLoader {
        ChildFirst(String name) { super(name, TwoLoadersDemo.class.getClassLoader()); }

        @Override
        protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
            if (!name.equals(Counter.class.getName())) return super.loadClass(name, resolve);
            synchronized (getClassLoadingLock(name)) {
                Class<?> c = findLoadedClass(name);
                if (c != null) return c;
                try (InputStream in = getParent().getResourceAsStream(name.replace('.', '/') + ".class")) {
                    byte[] bytes = in.readAllBytes();
                    return defineClass(name, bytes, 0, bytes.length);
                } catch (IOException e) {
                    throw new ClassNotFoundException(name, e);
                }
            }
        }
    }

    public static void main(String[] args) throws Exception {
        String name = Counter.class.getName();
        Class<?> c1 = new ChildFirst("plugin-1").loadClass(name);
        Class<?> c2 = new ChildFirst("plugin-2").loadClass(name);
        System.out.println("same name: " + c1.getName().equals(c2.getName()));
        System.out.println("c1 == c2: " + (c1 == c2) + ", c1 == Counter.class: " + (c1 == Counter.class));

        Object fromPlugin1 = c1.getDeclaredConstructor().newInstance();
        c1.getMethod("hit").invoke(fromPlugin1);
        c1.getMethod("hit").invoke(fromPlugin1);
        System.out.printf("hits: plugin-1=%s, plugin-2=%s, app=%s%n",
                c1.getField("hits").get(null), c2.getField("hits").get(null), Counter.hits);

        try {
            Counter c = (Counter) fromPlugin1;   // checkcast against the app loader's Counter
        } catch (ClassCastException e) {
            System.out.println(e.getMessage());
        }
    }
}
