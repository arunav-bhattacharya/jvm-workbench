package workbench.memory.l04;

import workbench.memory.Jvm;

import java.util.List;

/**
 * Runs the service load for one second with G1's age table logged, and prints the first four young
 * collections: how much of the heap each one freed, and how old the survivors are.
 */
public class GenerationsDemo {
    public static void main(String[] args) {
        if (args.length > 0) {
            ServiceLoad.run(1, 0.30);
            return;
        }
        for (String line : Jvm.lines(List.of("-XX:+UseG1GC", "-Xmx256m", "-Xlog:gc,gc+age=trace"), GenerationsDemo.class.getName(), "load")) {
            if (line.matches(".*GC\\([0-3]\\) (Pause Young|- age).*")) System.out.println(line.replaceAll("\\s+", " "));
        }
    }
}
