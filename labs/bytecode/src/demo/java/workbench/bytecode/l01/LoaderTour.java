package workbench.bytecode.l01;

import java.lang.management.ManagementFactory;

/** Which loader defined which class, and the chain a class-loading request walks up. */
public class LoaderTour {
    public static void main(String[] args) {
        show(String.class);                  // java.base
        show(java.sql.Connection.class);     // java.sql, a platform module
        show(LoaderTour.class);              // this program, on the class path
        show(kotlin.Unit.class);             // the Kotlin standard library jar, also on the class path

        StringBuilder chain = new StringBuilder();
        for (ClassLoader l = LoaderTour.class.getClassLoader(); l != null; l = l.getParent()) {
            chain.append(l.getName()).append(" -> ");
        }
        System.out.println("delegation chain: " + chain + "bootstrap (null)");
        System.out.println("classes loaded so far: " + ManagementFactory.getClassLoadingMXBean().getLoadedClassCount());
    }

    static void show(Class<?> c) {
        ClassLoader l = c.getClassLoader();
        System.out.printf("%-34s loader=%-9s module=%s%n",
                c.getName(), l == null ? "bootstrap" : l.getName(), c.getModule().getName());
    }
}
