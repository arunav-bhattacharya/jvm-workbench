package workbench.container.l03.demo;

import workbench.container.l03.Container;
import workbench.container.l03.SettlementService;
import workbench.container.l03.demo.app.CardIssuerClient;
import workbench.container.l03.demo.app.DemoApp;

import java.lang.ref.WeakReference;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

/**
 * Runs the reflective container, then looks inside this JVM with jcmd: a class histogram and a heap
 * dump. Then it drops the container and checks what the garbage collector could take away.
 * Run with -Pargs=wait to stop before each step and run jcmd yourself.
 */
public class RunningContainer {
    public static void main(String[] args) throws Exception {
        boolean wait = args.length > 0 && args[0].equals("wait");
        long pid = ProcessHandle.current().pid();
        Path classes = Path.of(RunningContainer.class.getProtectionDomain().getCodeSource().getLocation().toURI());
        Path dump = Files.createDirectories(classes.getParent().getParent().getParent().resolve("heapdumps")).resolve("container.hprof");
        Files.deleteIfExists(dump);                                      // jcmd refuses to overwrite a dump

        Container container = new Container(DemoApp.COMPONENTS);
        System.out.println("app: " + DemoApp.run(container));
        WeakReference<ClassLoader> generatedLoader =
                new WeakReference<>(container.get(SettlementService.class).getClass().getClassLoader());
        String proxyClass = container.get(CardIssuerClient.class).getClass().getName();

        if (wait) {
            System.out.printf("pid %d. In a second terminal, from labs/:%n", pid);
            System.out.printf("  jcmd %d GC.class_histogram | grep -E 'workbench|Proxy|ByteBuddy|ByteArray'%n", pid);
            System.out.printf("  jcmd %d GC.heap_dump %s%n", pid, dump);
            System.out.println("Then press Enter to drop the container.");
            System.in.read();
        } else {
            histogram(pid, proxyClass);
            jcmd(pid, "GC.heap_dump", dump.toString()).forEach(line -> System.out.println("heap dump: " + line));
        }

        container = null;                                                // the only reference to the container
        for (int i = 0; i < 10 && generatedLoader.get() != null; i++) {
            System.gc();                                                 // a request; repeat until the loader is gone
            Thread.sleep(50);
        }
        System.out.println("after dropping the container:");
        System.out.println("  Byte Buddy's class loader collected: " + (generatedLoader.get() == null));
        System.out.println("  " + proxyClass + " still loaded: " + stillLoaded(proxyClass));
        if (wait) {
            System.out.printf("Run the histogram again, then press Enter to exit.%n");
            System.in.read();
        } else {
            histogram(pid, proxyClass);
        }
    }

    /** The container's own lines of the histogram, then the proxy classes with live instances, grouped. */
    static void histogram(long pid, String ourProxy) throws Exception {
        List<String> lines = jcmd(pid, "GC.class_histogram");
        System.out.println(lines.get(1));                                // the column headings
        lines.stream().filter(l -> l.matches(".*(\\.Container|SingletonCell|InterceptingHandler|SubclassBridge"
                + "|\\$ByteBuddy\\$\\w+|ByteArrayClassLoader|app\\.PaymentService)( \\(.*)?$")
                || l.contains(" " + ourProxy + " ")).forEach(System.out::println);
        int annotations = 0, byteBuddy = 0, others = 0, ours = 0, instances = 0;
        for (String line : lines) {
            String[] f = line.trim().split("\\s+");
            if (f.length < 4 || !f[3].contains("$Proxy")) continue;      // num, #instances, #bytes, class name
            instances += Integer.parseInt(f[1]);
            if (f[3].equals(ourProxy)) ours += Integer.parseInt(f[1]);
            else if (isAnnotation(f[3])) annotations++;
            else if (f[3].startsWith("net.bytebuddy.")) byteBuddy++;
            else others++;
        }
        System.out.printf("  %d proxy instances: %d annotation proxy classes, %d in Byte Buddy's packages, %d other, %d of ours%n",
                instances, annotations, byteBuddy, others, ours);
    }

    static boolean isAnnotation(String proxyClass) {
        try {
            return java.lang.annotation.Annotation.class.isAssignableFrom(
                    Class.forName(proxyClass, false, RunningContainer.class.getClassLoader()));
        } catch (ClassNotFoundException | LinkageError e) {
            return false;
        }
    }

    static boolean stillLoaded(String name) {
        try {
            Class.forName(name, false, RunningContainer.class.getClassLoader());   // asks the loader, defines nothing
            return true;
        } catch (ClassNotFoundException e) {
            return false;
        }
    }

    static List<String> jcmd(long pid, String... command) throws Exception {
        List<String> cmd = new ArrayList<>(List.of(Path.of(System.getProperty("java.home"), "bin", "jcmd").toString(),
                Long.toString(pid)));
        cmd.addAll(List.of(command));
        Process p = new ProcessBuilder(cmd).redirectErrorStream(true).start();
        List<String> out = p.inputReader().lines().filter(l -> !l.startsWith("Picked up")).toList();
        p.waitFor();
        return out;
    }
}
