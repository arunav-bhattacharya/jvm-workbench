package workbench.memory.l04;

import workbench.memory.Jvm;

import java.util.List;

/** Logs every safepoint during one second of service load and prints the GC ones. */
public class SafepointDemo {
    public static void main(String[] args) {
        if (args.length > 0) {
            ServiceLoad.run(1, 0.30);
            return;
        }
        Jvm.lines(List.of("-XX:+UseG1GC", "-Xmx256m", "-Xlog:safepoint"), SafepointDemo.class.getName(), "load").stream()
                .filter(line -> line.contains("G1CollectForAllocation"))
                .limit(5)
                .forEach(System.out::println);
    }
}
