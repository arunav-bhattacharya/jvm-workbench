package workbench.container.l03.demo;

import workbench.container.l03.ContainerException;
import workbench.container.l03.RegistryGenerator;
import workbench.container.l03.demo.app.DemoApp;

import java.util.List;

/** Runs the build-time half of the container on the demo app and prints the class it writes. */
public class GenerateDemo {
    public static class Payouts { public Payouts(Statements s) {} }
    public static class Statements { public Statements(Payouts p) {} }

    public static void main(String[] args) {
        String source = RegistryGenerator.generate("workbench.container.l03.demo.gen", "AppRegistry", DemoApp.COMPONENTS);
        System.out.println(source);
        System.out.printf("%d lines, %d holder classes, %d generated interceptor classes%n",
                source.lines().count(),
                source.lines().filter(l -> l.contains("_Holder {")).count(),
                source.lines().filter(l -> l.startsWith("    static final class")).count());
        try {
            RegistryGenerator.generate("x", "Broken", List.of(Payouts.class, Statements.class));
        } catch (ContainerException e) {
            System.out.println("the build fails: " + e.getMessage());
        }
    }
}
