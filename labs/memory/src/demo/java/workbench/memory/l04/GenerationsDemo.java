package workbench.memory.l04;

import workbench.memory.Jvm;

import java.util.List;

/**
 * Runs the service load for one second with G1's age table logged, and prints the first four young
 * collections: how much of the heap each one freed, how old the survivors are, the age at which G1
 * promotes them (the tenuring threshold), and how many old regions they fill.
 */
public class GenerationsDemo {
    public static void main(String[] args) {
        if (args.length > 0) {
            ServiceLoad.run(1, 0.30);
            return;
        }
        List<String> flags = List.of("-XX:+UseG1GC", "-Xmx256m", "-Xlog:gc,gc+age=trace,gc+heap=info");
        for (String line : Jvm.lines(flags, GenerationsDemo.class.getName(), "load")) {
            if (line.matches(".*GC\\([0-3]\\) (Pause Young|- age|Desired survivor|Old regions).*")) {
                System.out.println(line.replaceAll("\\s+", " "));
            }
        }
    }
}
