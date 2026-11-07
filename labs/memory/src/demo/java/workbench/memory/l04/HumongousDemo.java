package workbench.memory.l04;

import workbench.memory.Jvm;

import java.util.List;

/**
 * Allocates 3 MiB "settlement files" in a 1 GB G1 heap, where regions are 1 MB, and prints the
 * region counts G1 logs for the first young pause.
 */
public class HumongousDemo {
    static volatile Object sink;

    public static void main(String[] args) {
        if (args.length > 0) {
            for (int i = 0; i < 40; i++) {
                sink = new byte[3 * 1024 * 1024];                      // 3 MiB + a 16-byte header
                for (int j = 0; j < 20_000; j++) sink = new byte[200];  // some ordinary garbage in between
            }
            return;
        }
        for (String line : Jvm.lines(List.of("-XX:+UseG1GC", "-Xmx1g", "-Xlog:gc,gc+init,gc+heap=info"), HumongousDemo.class.getName(), "load")) {
            if (line.contains("Heap Region Size") || line.matches(".*GC\\(0\\) (Pause|.*regions).*")) {
                System.out.println(line.replaceAll("\\s+", " "));
            }
        }
    }
}
