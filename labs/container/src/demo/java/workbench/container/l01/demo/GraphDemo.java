package workbench.container.l01.demo;

import workbench.container.l01.Container;
import workbench.container.l01.ContainerException;
import workbench.container.l01.demo.app.PaymentService;

import java.util.List;

/** Wires the demo app from a scan, prints the creation order, then tries a graph with a cycle. */
public class GraphDemo {
    public static class Payouts { public Payouts(Statements statements) {} }
    public static class Statements { public Statements(Reconciler reconciler) {} }
    public static class Reconciler { public Reconciler(Payouts payouts) {} }

    public static void main(String[] args) {
        Container app = Container.scan("workbench.container.l01.demo.app");
        System.out.println("creation order: " + app.creationOrder().stream().map(Class::getSimpleName).toList());
        app.get(PaymentService.class).pay("4111111111111111", 12_000);

        try {
            new Container(List.of(Payouts.class, Statements.class, Reconciler.class));
        } catch (ContainerException e) {
            System.out.println("cycle: " + e.getMessage());
        }
    }
}
